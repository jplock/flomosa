import logging
from django.utils import simplejson
from google.appengine.api import memcache
from google.appengine.ext import db

def build_json(webapp, data, code=200):
    webapp.error(code)
    if not isinstance(data, dict):
        data = dict(message=data)
    if str(code)[0] != '2':
        data['code'] = code
        logging.error(data['message'])

    try:
        json = simplejson.dumps(data)
    except:
        logging.critical('Error parsing JSON')
        return None

    webapp.response.headers['Content-Type'] = 'application/json'
    webapp.response.out.write(json)
    return None

def load_from_cache(key, model):
    """
    Load an object by first checking memcache. If the object cannot be found
    in the cache, then check the datastore. Return the object if found,
    otherwise return None.
    """
    if isinstance(key, db.Key):
        key = key.name()

    obj = memcache.get(key)
    if not isinstance(obj, model):
        logging.warning('%s "%s" not found in memcache' % (model.__name__,
            key))
        obj = model.get_by_key_name(key)
        if not isinstance(obj, model):
            logging.error('%s "%s" not found in datastore' % (model.__name__,
                key))
            return None
        memcache.set(key, obj)
    return obj