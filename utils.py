#
# Copyright 2010 Flomosa, LLC
#

import uuid
import logging

from django.utils import simplejson

_CLIENT_ERROR_FORMAT = 'CLIENT ERROR [%s]: %s'

def get_log_message(message, code=0, format=_CLIENT_ERROR_FORMAT):
    """Return a formatted error log message."""
    return format % (code, message)

def generate_key():
    """Generate a datastore key."""
    return str(uuid.uuid4())

def build_json(webapp, data, code=200, return_response=False):
    """Build a JSON error message response."""

    if isinstance(data, Exception):
        data = dict(message=str(data))
    elif not isinstance(data, dict):
        data = dict(message=data)
    if not str(code).startswith('2'):
        data['code'] = code

    try:
        json = simplejson.dumps(data)
    except:
        logging.critical('Error parsing JSON.')
        return None

    if return_response:
        return json

    webapp.error(code)
    webapp.response.headers['Content-Type'] = 'application/json'
    webapp.response.out.write(json)
    return None
