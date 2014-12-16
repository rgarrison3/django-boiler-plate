# sys
import traceback, os, sys, json, time

# django
from django.db import connection
from django.conf import settings

# local
from core.utils import debug_print

class RequestInfo(object):
    def process_request(self, request):
        if settings.DEBUG:
            querystring = ''
            if request.META['QUERY_STRING']:
                querystring = '?%s' % request.META['QUERY_STRING']
            debug_print('%s%s' % (request.META['PATH_INFO'], querystring,), color='cyan')
            try:
                if request.method == 'POST' and bool(request.body):
                    debug_print(json.loads(request.body), color='cyan')
            except Exception as e:
                # JSON errors are possible if the post data is weird, but whatever
                debug_print('Error: %s' % (e.args,), color='red')


class PrintQueries(object):
    def process_response(self, request, response):
        if 'print_queries' not in request.GET.keys():
            return response

        try:
            import sqlparse
        except ImportError:
            sqlparse = None

        if len(connection.queries) > 0 and settings.DEBUG:
            total_time = 0.0
            for query in connection.queries:
                print ''
                if sqlparse:
                    print sqlparse.format(query['sql'], reindent=True)
                    print '\033[93m'+ query['time'] +'\033[0m'
                else:
                    print query['sql']
                print ''
                total_time = total_time + float(query['time'])
            print "\033[1;32m[TOTAL TIME: %s seconds]\033[0m" % total_time
            print "  Ran %d queries" % len(connection.queries)
        return response


class TimeRequests(object):
    def process_request(self, request):
        request._start_time = time.time()

    def process_response(self, request, response):
        if settings.DEBUG:
            print 'Responded in %.3f seconds' % (time.time() - request._start_time)

        return response