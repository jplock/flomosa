#
# Copyright 2010 Flomosa, LLC
#

import logging

from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.runtime import apiproxy_errors

from exceptions import MissingException
from settings import DATASTORE_RETRY_ATTEMPTS


def get_from_cache(cls, key):
    """
    Load object from cache, then datastore.

    Load an object by first checking memcache. If the object cannot be found
    in the cache, then check the datastore. Return the object if found,
    otherwise return None.

    """

    if isinstance(key, db.Key):
        key = key.name()
    if not key:
        raise MissingException('Missing "key" parameter.')

    logging.debug('Looking up %s "%s" in memcache.' % (cls.__name__, key))
    model = memcache.get(key, namespace=cls.__name__)
    if not isinstance(model, cls):
        logging.warning('%s "%s" not found in memcache. Trying datastore.' % \
            (cls.__name__, key))
        model = cls.get_by_key_name(key)
        if not isinstance(model, cls):
            raise NotFoundException('%s key "%s" does not exist in the ' \
                'datastore.' % (cls.__name__, key))
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
    """
    Save a model to the datastore, then the cache.

    Save the model to the datastore, raising an exception if unsuccessful.
    If the model is saved, write it to the cache.

    """

    attempts = 0
    success = False
    while (not success and attempts <= DATASTORE_RETRY_ATTEMPTS):
        logging.debug('Storing %s "%s" in datastore (%d/%d).' % (model.kind(),
            model.id, (attempts+1), DATASTORE_RETRY_ATTEMPTS))
        try:
            db.Model.put(model)
            success = True
        except apiproxy_errors.CapabilityDisabledError:
            raise MaintenanceException('Unable to save %s "%s" to the ' \
                'datastore due to maintenance.' % (model.kind(), model.id))
        except db.Timeout:
            logging.warning('Datastore put() request timed out, retrying.')
            attempts += 1
        except db.Error, ex:
            raise InternalException('Unable to save %s "%s" to the ' \
                'datastore: %s' % (model.kind(), model.id, ex))

    memcache.delete(model.id)
    if model.is_saved():
        logging.debug('Storing %s "%s" in memcache.' % (model.kind(), model.id))
        memcache.set(model.id, model, namespace=model.kind())

    return model

def delete_from_cache(model=None, kind=None, key=None):
    """
    Delete a model from the datastore, then from the cache.

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
        raise MissingException('Missing "model" or "kind" and "key" parameters.')

    logging.debug('Deleting %s "%s" from the datastore.' % (kind, key))
    try:
        db.delete(model_key)
    except db.NotSavedError:
        logging.warning('%s "%s" was never saved in the datastore.' % (kind,
            key))
    except apiproxy_errors.CapabilityDisabledError:
        raise MaintenanceException('Unable to delete %s "%s" from the ' \
            'datastore due to maintenance.' % (kind, key))
    except db.Error, ex:
        raise InternalException('Unable to delete %s "%s" from the ' \
            'datastore: %s' % (kind, key, ex))

    logging.debug('Deleting %s "%s" from the memcache.' % (kind, key))
    if not memcache.delete(key):
        logging.warning('Unable to delete %s "%s" from memcache.')

    return None
