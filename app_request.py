#!/usr/bin/env python
#
# Copyright 2010 Flomosa, LLC
#

import logging
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api import memcache
from google.appengine.api.labs import taskqueue
import models
import utils

class NewHandler(webapp.RequestHandler):

    def post(self):
        logging.debug('Begin NewHandler.post() function')

        process_key = self.request.get('process', default_value=None)
        if not process_key:
            return utils.build_json(self, 'Missing "process" parameter',
                code=400)

        process = utils.load_from_cache(process_key, models.Process)
        if not process:
            return utils.build_json(self,
                'Unable to find process with ID "%s"' % process_key, code=404)

        if not process.is_valid():
            return utils.build_json(self, 'Process "%s" is not valid' % \
                process_key, code=500)

        requestor = self.request.get('requestor', default_value=None)
        if not requestor:
            return utils.build_json(self, 'Missing "requestor" parameter',
                code=400)

        request_key = utils.generate_key()
        params = {'_id': request_key}
        for key, value in self.request.params.items():
            params[key] = value

        queue = taskqueue.Queue('request-store')
        task = taskqueue.Task(params=params)
        queue.add(task)

        utils.build_json(self, {'id': request_key}, 201)

        logging.debug('Finished NewHandler.post() function')

class EditHandler(webapp.RequestHandler):

    def get(self, request_key):
        logging.debug('Begin EditHandler.get() function')

        request = utils.load_from_cache(request_key, models.Request)
        if not request:
            return utils.build_json(self,
                'Unable to find request with ID "%s"' % request_key, code=404)

        utils.build_json(self, request.to_dict())

        logging.debug('Finished EditHandler.get() function')

    def post(self, request_key):
        logging.debug('Begin EditHandler.post() function')

        request = utils.load_from_cache(request_key, models.Request)
        if not process:
            return utils.build_json(self,
                'Unable to find request with ID "%s"' % request_key, code=404)

        process = self.request.get('process', default_value=None)
        requestor = self.request.get('requestor', default_value=None)
        is_draft = self.request.get('is_draft', default_value=None)

        if requestor is not None:
            logging.info('Found "requestor" parameter')
            request.requestor = requestor
        if is_draft is not None:
            logging.info('Found "is_draft" parameter')
            request.is_draft = is_draft

        if process is not None:
            if request.is_draft:
                logging.info('Found "process" parameter')
                request.process = process
            else:
                return utils.build_json(self,
                    'Unable to change the process on a previously submitted ' \
                    'request', code=400)

        try:
            request.put()
        except:
            return utils.build_json(self, 'Unable to save request', code=500)

        memcache.set(request_key, request)

        utils.build_json(self, request.to_dict())

        logging.debug('Finished EditHandler.post() function')

def main():
    application = webapp.WSGIApplication(
        [('/requests/', NewHandler),
        (r'/requests/(.*)\.json', EditHandler)],
        debug=utils._DEBUG)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
