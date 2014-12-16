from django.db import models, connections
from django.db.models.query import QuerySet
from django.db.models.fields.related import RelatedField


class NoCountQuerySet(QuerySet):
    def count(self):
        # Code from django/db/models/query.py

        if self._result_cache is not None and not self._iter:
            return len(self._result_cache)

        is_mysql = 'mysql' in connections[self.db].client.executable_name.lower()

        query = self.query
        if (is_mysql and not query.where and
                query.high_mark is None and
                query.low_mark == 0 and
                not query.select and
                not query.group_by and
                not query.having and
                not query.distinct):
            # If query has no constraints, we would be simply doing
            # "SELECT COUNT(*) FROM foo". Monkey patch so the we
            # get an approximation instead.
            cursor = connections[self.db].cursor()
            cursor.execute("SHOW TABLE STATUS LIKE %s",
                    (self.model._meta.db_table,))
            return cursor.fetchall()[0][4]
        else:
            return self.query.get_count(using=self.db)


class BaseManager(models.Manager):

    def _build_dynamic_or_where_clause(self, value_dict):
        '''
        Arguments:
        value_dict  {dict}  The data on which we want to WHERE

        Return:
        tuple ({keys_list}, {values_list},)
        '''
        keys = []
        values = []
        for key, value in value_dict.items():
            if key in self.model.field_names():
                # This is *technically* a security hole, as `key`
                # could be open to SQL-injection attacks. However,
                # our valid_db_field_names catch above will prevent
                # any such attacks unless we add model field names
                # that are themselves SQL-injection values.
                db_column_name = key
                field = self.model._meta.get_field(key)
                if field.db_column is not None:
                    db_column_name = field.db_column

                if isinstance(field, RelatedField):
                    value = value.pk

                # Note what we did
                keys.append(db_column_name)
                values.append(value)
        return keys, values

    def _build_dynamic_or_sql(self, values_dict):
        '''
        Builds keys-values to be thrown into a "SELECT * ... WHERE x=y OR a=b" style query

        Return  (sql, values,)  The finished SQL to be run and the values to pass .raw()
        '''
        sql = '''SELECT *
        FROM `%s`
        WHERE ::where_clause::
        ''' % (self.model._meta.db_table)


        # Django's ORM doesn't support dynamic OR clauses like this
        # with Q-complex lookups, so we have to drop into raw sql
        keys, values = self._build_dynamic_or_where_clause(values_dict)

        # Massage or keys into a SQLy string
        or_where = []
        for key in keys:
            or_where.append('`'+ key +'` = %s')
        or_where = ' OR '.join(or_where)

        # Finish the big `sql` variable
        sql = sql.replace('::where_clause::', or_where)
        return sql, values

    def dynamic_or(self, **kwargs):
        '''
        Django's ORM handles OR clauses nicely, unless you have
        a dynamic amount of OR values in your WHERE clause. This
        handles that.

        Throw it a dictionary, potentially containing invalid keys for
        this particular model, and just let it work.
        '''
        sql, values = self._build_dynamic_or_sql(kwargs)

        # This will throw an ObjectDoesNotExist if the query doesn't find anything
        # Also note that Django will prevent SQL-injection attacks with `values`
        raw_query_set = self.model.objects.raw(sql, values)

        # Raw Querysets don't give us things like len(), so we have to
        # pull out every single record (it won't be an intensive quantity)
        # to figure out if a merge is required
        matches = []
        for row in raw_query_set:
            matches.append(row)
        return matches


class NoCountManager(BaseManager):
        def get_query_set(self):
            return NoCountQuerySet(self.model, using=self._db)
