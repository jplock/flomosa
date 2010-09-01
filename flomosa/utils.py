#
# Copyright 2010 Flomosa, LLC
#

import logging
import uuid

from django.utils import simplejson

from flomosa import exceptions


def generate_key():
    "Generate a datastore key."
    return str(uuid.uuid4())

def build_json(webapp, data, code=200, return_response=False):
    "Build a JSON error message response."

    if isinstance(data, exceptions.HTTPException):
        code = data.status
        data = {'message': data.body}
    elif isinstance(data, Exception):
        data = {'message': unicode(data)}
    elif not isinstance(data, dict):
        data = {'message': data}
    if not str(code).startswith('2'):
        data['code'] = code

    try:
        json = simplejson.dumps(data)
    except Exception, ex:
        logging.critical('JSON ERROR: %s.' % ex)
        return None

    if return_response:
        return json

    webapp.error(code)
    webapp.response.headers['Content-Type'] = 'application/json'
    webapp.response.out.write(json)
    return None
