#!/usr/bin/env python
#
# Copyright 2010 Flomosa, LLC
#

import logging

from django.utils import simplejson
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp import util
from google.appengine.api import memcache
from google.appengine.api.labs import taskqueue

import models
import utils

class RequestHandler(webapp.RequestHandler):

    def get(self, request_key):
        logging.debug('Begin RequestHandler.get() function')

        request = utils.load_from_cache(request_key, models.Request)
        if not request:
            return utils.build_json(self, 'Request ID "%s" does not exist.' % \
                request_key, code=404)

        utils.build_json(self, request.to_dict())

        logging.debug('Finished RequestHandler.get() function')

    def post(self, request_key):
        logging.debug('Begin RequestHandler.post() function')

        try:
            data = simplejson.loads(self.request.body)
        except:
            return utils.build_json(self, 'Error parsing JSON request.',
                code=500)

        process_key = data.get('process', None)
        if not process_key:
            return utils.build_json(self, 'Missing "process" parameter.',
                code=400)

        process = utils.load_from_cache(process_key, models.Process)
        if not process:
            return utils.build_json(self, 'Process ID "%s" does not exist.' % \
                process_key, code=404)

        if not process.is_valid():
            return utils.build_json(self, 'Process ID "%s" is not valid.' % \
                process_key, code=500)

        requestor = data.get('requestor', None)
        if not requestor:
            return utils.build_json(self, 'Missing "requestor" parameter.',
                code=400)

        request = utils.load_from_cache(request_key, models.Request)
        if request:
            return utils.build_json(self, 'Request ID "%s" already exists.' % \
                request_key, code=500)

        params = self.request.params.items()
        params['_id'] = request_key

        queue = taskqueue.Queue('request-store')
        task = taskqueue.Task(params=params)
        queue.add(task)

        utils.build_json(self, {'id': request_key}, 201)

        logging.debug('Finished RequestHandler.post() function')

    def delete(self, request_key):
        logging.debug('Begin RequestHandler.delete() function')

        key = db.Key.from_path('Request', request_key)
        db.delete(key)
        memcache.delete(request_key)

        self.error(204)

        logging.debug('Finished RequestHandler.delete() function')

def main():
    application = webapp.WSGIApplication(
        [(r'/requests/(.*)\.json', RequestHandler)], debug=utils._DEBUG)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
