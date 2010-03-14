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
from google.appengine.runtime import apiproxy_errors

import models
import utils


class RequestHandler(webapp.RequestHandler):

    def get(self, request_key):
        logging.debug('Begin RequestHandler.get() function')

        logging.info('Looking up Request key "%s" in memcache then datastore.' \
            % request_key)
        request = utils.load_from_cache(request_key, models.Request)
        if not request:
            error_msg = 'Request key "%s" does not exist.' % request_key
            logging.error(utils.get_log_message(error_msg, 404))
            return utils.build_json(self, error_msg, 404)

        utils.build_json(self, request.to_dict())

        logging.debug('Finished RequestHandler.get() function')

    def post(self, request_key=None):
        logging.debug('Begin RequestHandler.post() function')

        data = self.request.params

        process_key = data.get('process', None)
        if not process_key:
            error_msg = 'Missing "process" parameter.'
            logging.error(utils.get_log_message(error_msg, 400))
            return utils.build_json(self, error_msg, 400)

        process = utils.load_from_cache(process_key, models.Process)
        if not process:
            error_msg = 'Process "%s" does not exist.' % process_key
            logging.error(utils.get_log_message(error_msg, 404))
            return utils.build_json(self, error_msg, 404)

        if not process.is_valid():
            error_msg = 'Process "%s" is not valid.' % process_key
            logging.error(utils.get_log_message(error_msg, 500))
            return utils.build_json(self, error_msg, 500)

        requestor = data.get('requestor', None)
        if not requestor:
            error_msg = 'Missing "requestor" parameter.'
            logging.error(utils.get_log_message(error_msg, 400))
            return utils.build_json(self, error_msg, 400)

        if request_key:
            request = utils.load_from_cache(request_key, models.Request)
            if request:
                error_msg = 'Request "%s" already exists.' % request_key
                logging.error(utils.get_log_message(error_msg, 500))
                return utils.build_json(self, error_msg, 500)
        else:
            request_key = utils.generate_key()
            request = None

        if not request:
            request = models.Request(key_name=request_key, process=process,
                requestor=requestor)

        for key, value in data.items():
            if not hasattr(request, key):
                setattr(request, key, value)

        logging.info('Storing Request "%s" in datastore.' % request_key)
        try:
            request.put()
        except apiproxy_errors.CapabilityDisabledError:
            error_msg = 'Unable to save Request key "%s" due to maintenance.' \
                % request_key
            logging.error(utils.get_log_message(error_msg, 500))
            return utils.build_json(self, error_msg, 500)
        except:
            error_msg = 'Unable to save Request key "%s" in datastore.' % \
                request_key
            logging.error(utils.get_log_message(error_msg, 500))
            return utils.build_json(self, error_msg, 500)

        if request.is_saved():
            logging.info('Storing Request "%s" in memcache.' % request.id)
            memcache.set(request.id, request)

        step = process.get_start_step()
        step.queue_tasks(request)

        logging.info('Returning Request "%s" as JSON to client.' % request.id)
        utils.build_json(self, {'key': request.id}, 201)

        logging.debug('Finished RequestHandler.post() function')

    def delete(self, request_key):
        logging.debug('Begin RequestHandler.delete() function')

        key = db.Key.from_path('Request', request_key)

        logging.info('Deleting Request "%s" from datastore.' % request_key)
        try:
            db.delete(key)
        except apiproxy_errors.CapabilityDisabledError:
            logging.warning('Unable to delete Request "%s" due to ' \
                'maintenance.' % request_key)

        logging.info('Deleting Request "%s" from memcache.' % request_key)
        memcache.delete(request_key)

        self.error(204)

        logging.debug('Finished RequestHandler.delete() function')

def main():
    application = webapp.WSGIApplication(
        [(r'/requests/(.*)\.json', RequestHandler),
        (r'/requests/', RequestHandler)], debug=utils._DEBUG)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
