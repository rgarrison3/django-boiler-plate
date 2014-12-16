# django
from django.db import models
from django.conf import settings

# 3rd party
from model_utils import FieldTracker


class BaseModel(models.Model):
    tracker = FieldTracker()

    class Meta:
        abstract = True

    @classmethod
    def field_names(cls):
        '''
        Returns the names of all fields on the model
        '''
        return [field.name for field in cls._meta.fields]

    def field_values(self, full=False):
        '''
        Returns a dictionary of all local fields.
        '''
        return {field.name: self.get_field_value(field.name, full) for field in self.__class__._meta.fields}

    def get_field_value(self, field_name, full=False):
        '''
        Returns a given value of for this instantiated model.

        Arguments:
        field_name    {string}      The value of the attr you want
        full          {bool}        OPTIONAL. If the passed name is a relation, should it be hydrated?
                                    Defaults to False.
        '''
        field = self._meta.get_field(field_name)
        try:
            # Is this a related field or a literal?
            if isinstance(field, models.fields.related.RelatedField):
                if full:
                    # It's related and they ordered it hydrated
                    val = getattr(self, field_name, None)
                    # Pull out the value and hydrate it if it exists, else
                    # return None
                    if val is not None:
                        return val.field_values()  # Don't forward `full` to avoid cyclical problems
                    else:
                        return None
                else:
                    # Not hydrated is easy enough, just return the PK we
                    # already have on hand
                    return getattr(self, '%s_id' % (field_name,), None)
            else:
                # Not related? Too easy.
                return getattr(self, field_name, None)
        except:
            # Related fields may blow up
            # if their relation is unfilled
            return None

    def update_values(self, data, **kwargs):
        '''
        Updates the instantiated Model with any
        values in `data` said model instance lacks. Only
        honors actual DB fields (non m2m).

        Arguments:
        data        dict/model  Key-Value pairs of data to be applied to self

        Keyword Arguments:
        overwrite   bool        Default FALSE. If False, only 'falsy' values will be
                                overwritten. If True, all supplied values are favored.
        honor_falsy bool        Default FALSE. If True, passed-in Falsy values will
                                overwrite existing non-Falsy values (if overwrite is also True)
        save        bool        Default TRUE. If False, the edits are made but no DB
                                call is made.

        Return      bool        True if any changes were made.
        '''
        should_overwrite = kwargs.get('overwrite', False)

        if isinstance(data, models.Model):
            # If a fellow model instance is supplied,
            # convert it to a dictionary
            data = data.field_values()

        valid_db_field_names = self.__class__.field_names()
        for key, value in data.items():
            # Only mess with actual DB fields
            if key in valid_db_field_names:
                # Pay attention to 'Falsy' rules
                if data.get(key, None) or kwargs.get('honor_falsy', False):
                    # If the existing value is Falsy OR if we should overwrite
                    if should_overwrite or not getattr(self, key, None):
                        # Update the value
                        setattr(self, key, value)

        # Only make a DB call if the model has changed
        if self.tracker.changed():
            if kwargs.get('save', True):
                self.save()
            return True
        else:
            return False
