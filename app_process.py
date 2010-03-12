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

class ProcessHandler(webapp.RequestHandler):

    def get(self, process_key):
        logging.debug('Begin ProcessHandler.get() function')

        logging.info('Looking up Process key "%s" in memcache then datastore.' \
            % process_key)
        process = utils.load_from_cache(process_key, models.Process)
        if not process:
            error_msg = 'Process key "%s" does not exist.' % process_key
            logging.error(utils.get_log_message(error_msg, 404))
            return utils.build_json(self, error_msg, 404)

        logging.info('Returning Process "%s" as JSON to client.' % \
            process.id)
        utils.build_json(self, process.to_dict())

        logging.debug('Finished ProcessHandler.get() function')

    def put(self, process_key):
        logging.debug('Begin ProcessHandler.put() function')

        try:
            data = simplejson.loads(self.request.body)
        except:
            error_msg = 'Error parsing JSON request.'
            logging.error(utils.get_log_message(error_msg, 500))
            return utils.build_json(self, error_msg, 500)

        name = data.get('name', None)
        if not name:
            error_msg = 'Missing "name" parameter.'
            logging.error(utils.get_log_message(error_msg, 400))
            return utils.build_json(self, error_msg, 400)

        kind = data.get('kind', None)
        if not kind or kind != 'Process':
            error_msg = 'Invalid "kind" parameter; expected "kind=Process".'
            logging.error(utils.get_log_message(error_msg, 400))
            return utils.build_json(self, error_msg, 400)

        params = {'key': process_key, 'data': self.request.body}
        queue = taskqueue.Queue('process-store')
        task = taskqueue.Task(params=params)

        logging.info('Queued Process "%s" for creation.' % process_key)
        queue.add(task)

        logging.info('Returning Process "%s" as JSON to client.' % \
            process_key)
        utils.build_json(self, {'key': process_key}, 202)

        logging.debug('Finished ProcessHandler.put() function')

    def delete(self, process_key):
        logging.debug('Begin ProcessHandler.delete() function')

        entities = []
        entity_keys = []

        process = models.Process.get_by_key_name(process_key)
        if process:
            logging.info('Deleting Process "%s" from datastore.' % \
                process.id)
            entities.append(process)
            logging.info('Deleting Process "%s" from memcache.' % \
                process.id)
            entity_keys.append(process.id)
            entity_keys.append(process_key)

            for action in process.actions:
                logging.info('Deleting Action "%s" from datastore.' % \
                    action.id)
                entities.append(action)
                logging.info('Deleting Action "%s" from memcache.' % \
                    action.id)
                entity_keys.append(action.id)

            for step in process.steps:
                logging.info('Deleting Step "%s" from datastore.' % \
                    step.id)
                entities.append(step)
                logging.info('Deleting Step "%s" from memcache.' % step.id)
                entity_keys.append(step.id)
        else:
            logging.warning('Process key "%s" not found in datastore to ' \
                'delete.' % process_key)

        if entities:
            db.delete(entities)
        if entity_keys:
            memcache.delete_multi(entity_keys)

        self.error(204)

        logging.debug('Finished ProcessHandler.delete() function')

def main():
    application = webapp.WSGIApplication([(r'/processes/(.*)\.json',
        ProcessHandler)], debug=utils._DEBUG)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
