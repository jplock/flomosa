#
# Copyright 2010 Flomosa, LLC
#

import uuid
import logging

from django.utils import simplejson
from google.appengine.api import memcache
from google.appengine.ext import db

_DEBUG = True

_CLIENT_ERROR_FORMAT = 'CLIENT ERROR [%s]: %s'

def get_log_message(message, code=None, format=_CLIENT_ERROR_FORMAT):
    """Return a formatted error log message."""
    return format % (code, message)

def generate_key():
    """Generate a datastore key."""
    return str(uuid.uuid4())

def build_json(webapp, data, code=200):
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

    webapp.error(code)
    webapp.response.headers['Content-Type'] = 'application/json'
    webapp.response.out.write(json)
    return None

def load_from_cache(key, model):
    """Load object from cache, then datastore.

    Load an object by first checking memcache. If the object cannot be found
    in the cache, then check the datastore. Return the object if found,
    otherwise return None.
    """

    if isinstance(key, db.Key):
        key = key.name()

    obj = memcache.get(key)
    if not isinstance(obj, model):
        logging.warning('%s key "%s" not found in memcache. Trying datastore.' \
            % (model.kind(), key))
        obj = model.get_by_key_name(key)
        if not isinstance(obj, model):
            logging.error('%s key "%s" not found in datastore.' % (model.kind(),
                key))
            return None
        else:
            logging.info('%s key "%s" found in datastore. Writing to memcache.' \
                % (model.kind(), key))
        memcache.set(key, obj)
    else:
        logging.info('%s key "%s" found in memcache.' % (model.kind(), key))
    return obj
