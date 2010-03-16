#
# Copyright 2010 Flomosa, LLC
#

import logging

from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.runtime import apiproxy_errors

def get_from_cache(cls, key):
    """Load object from cache, then datastore.

    Load an object by first checking memcache. If the object cannot be found
    in the cache, then check the datastore. Return the object if found,
    otherwise return None.
    """

    if isinstance(key, db.Key):
        key = key.name()

    logging.debug('Looking up %s "%s" in memcache.' % (cls.__name__, key))
    model = memcache.get(key, namespace=cls.__name__)
    if not isinstance(model, cls):
        logging.warning('%s "%s" not found in memcache. Trying datastore.' % \
            (cls.__name__, key))
        model = cls.get_by_key_name(key)
        if not isinstance(model, cls):
            logging.error('%s "%s" not found in datastore.' % (cls.__name__,
                key))
            return None
        elif model.id == key:
            logging.info('%s "%s" found in datastore. Writing to memcache.' % \
                (cls.__name__, key))
            memcache.set(key, model, namespace=model.kind())
        else:
            model = None
    else:
        logging.debug('%s "%s" found in memcache.' % (cls.__name__, key))

    return model

def save_to_cache(model):
    """Save a model to the datastore, then the cache.

    Save the model to the datastore, raising an exception if unsuccessful.
    If the model is saved, write it to the cache.
    """

    if not isinstance(model, db.Model):
        raise Exception('Object is not Model')

    logging.debug('Storing %s "%s" in datastore.' % (model.kind(), model.id))
    try:
        db.Model.put(model)
    except apiproxy_errors.CapabilityDisabledError:
        memcache.delete(model.id)
        raise Exception('Unable to save %s "%s" due to maintenance.' % \
            (model.kind(), model.id))
    except:
        memcache.delete(model.id)
        raise Exception('Unable to save %s "%s" in datastore.' % (model.kind(),
            model.id))

    if model.is_saved():
        logging.debug('Storing %s "%s" in memcache.' % (model.kind(), model.id))
        memcache.set(model.id, model, namespace=model.kind())

    return model

def delete_from_cache(model=None, kind=None, key=None):
    """Delete a model from the datastore, then from the cache.

    Delete the model from the datastore, raising an exception if unsuccessful.
    Also delete the model from the cache.
    """

    if isinstance(model, db.Model):
        model_key = model.key()
        kind = model.kind()
        key = model.id
    elif kind and key:
        model_key = db.Key.from_path(kind, key)
    else:
        return None

    logging.debug('Deleting %s "%s" from the datastore.' % (kind, key))
    try:
        db.delete(model_key)
    except db.NotSavedError:
        logging.warning('%s "%s" was never saved in the datastore.' % (kind,
            key))
    except apiproxy_errors.CapabilityDisabledError:
        logging.error('Unable to delete %s "%s" from datastore due to ' \
            'maintenance.' % (kind, key))
    except Exception, e:
        logging.error('Unable to delete %s "%s" from datastore: %s' % (kind,
            key, e))

    logging.debug('Deleting %s "%s" from the memcache.' % (kind, key))
    if not memcache.delete(key):
        logging.warning('Unable to delete %s "%s" from memcache.')

    return None
