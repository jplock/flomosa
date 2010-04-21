#
# Copyright 2010 Flomosa, LLC
#

import logging
import uuid

from django.utils import simplejson

_CLIENT_ERROR_FORMAT = 'CLIENT ERROR [%s]: %s'

def get_log_message(message, code=0, format=_CLIENT_ERROR_FORMAT):
    """Return a formatted error log message.

    Parameters:
      message - message to format
      code - error code
      format - format string
    """
    return format % (code, message)

def generate_key():
    """Generate a datastore key."""
    return str(uuid.uuid4())

def build_json(webapp, data, code=200, return_response=False):
    """Build a JSON error message response.

    Parameters:
      webapp - The webapp instance
      data - Exception, dict or string to convert to JSON
      code - error code
      return_response - return the JSON message or not
    """

    if isinstance(data, Exception):
        data = dict(message=str(data))
    elif not isinstance(data, dict):
        data = dict(message=data)
    if not str(code).startswith('2'):
        data['code'] = code

    try:
        json = simplejson.dumps(data)
    except Exception, e:
        logging.critical('Error parsing JSON: %s.' % e)
        return None

    if return_response:
        return json

    webapp.error(code)
    webapp.response.headers['Content-Type'] = 'application/json'
    webapp.response.out.write(json)
    return None


class FlomosaException(Exception):
    """Base exception for all exceptions."""

    def __init__(self, code, message, headers=None):
        self._code = code
        self._message = str(message)
        self._headers = headers or {}
        Exception.__init__(self, message)

    def __getitem__(self, key):
        if key == 'code':
            return self._code

        try:
            return self._headers[key]
        except KeyError:
            return None

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return '%s (#%s)' % (self._message, self._code)
