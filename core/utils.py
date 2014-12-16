# System
import hashlib, datetime

# Django
from django.conf import settings
from django.utils import timezone

# 3rd Party
from termcolor import cprint

def debug_print(obj, as_string=False, **kwargs):
    '''
    Wrapper around Python's native `print` statement
    that simply is a no-op when out of DEBUG mode

    All Keyword Arguments accept values listed at https://pypi.python.org/pypi/termcolor

    Arguments:
    obj         {mixed}     The paylod to print
    as_string   {boolean}   Defaults to False. Pass true if
                            your payload can't be printed natively
                            for whatever reason
    Keyword Arguments:
    color       {string}    The color of this print statement.
    bg_color    {string}    The highlight color of this print statement.
    attrs       {list}      Various cprint attributes
    '''
    if settings.DEBUG:
        color = kwargs.get('color', None)
        bg_color = kwargs.get('bg_color', None)
        attrs = kwargs.get('attrs', [])
        if as_string:
            payload = obj.__str__()
        else:
            payload = obj

        if color is not None or bg_color is not None:
            if color is None:
                color = 'white'
            if bg_color is not None:
                bg_color = 'on_' + bg_color
                cprint(payload, color, bg_color, attrs=attrs)
            else:
                cprint(payload, color, attrs=attrs)
        else:
            print payload

def datetime_from_seconds(timestamp):
    '''
    Takes a timestamp (like 1337966815) and turns it into
    something like this: datetime.datetime(2012, 5, 16, 15, 46, 40, tzinfo=<UTC>)
    '''
    datetime_obj = datetime.datetime.utcfromtimestamp(timestamp)
    return timezone.make_aware(datetime_obj, timezone.get_default_timezone())
