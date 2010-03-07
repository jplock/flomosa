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

        process = utils.load_from_cache(process_key, models.Process)
        if not process:
            return utils.build_json(self, 'Process ID "%s" does not exist.' % \
                process_key, code=404)

        utils.build_json(self, process.to_dict())

        logging.debug('Finished ProcessHandler.get() function')

    def put(self, process_key):
        logging.debug('Begin ProcessHandler.put() function')

        try:
            data = simplejson.loads(self.request.body)
        except:
            return utils.build_json(self, 'Error parsing JSON request.',
                code=500)

        try:
            name = data['name']
        except KeyError:
            return utils.build_json(self, 'Missing "name" parameter.', code=400)

        params = {'_id': process_key, 'data': self.request.body}

        queue = taskqueue.Queue('process-store')
        task = taskqueue.Task(params=params)
        queue.add(task)

        utils.build_json(self, {'id': process_key}, 201)

        logging.debug('Finished ProcessHandler.put() function')

    def delete(self, process_key):
        logging.debug('Begin ProcessHandler.delete() function')

        entities = []
        entity_keys = []

        process = models.Process.get_by_key_name(process_key)
        if process:
            entities.append(process)
            entity_keys.append(process_key)

            for action in process.actions:
                entities.append(action)
                entity_keys.append(action.id)

            for step in process.steps:
                entities.append(step)
                entity_keys.append(step.id)

        db.delete(entities)
        memcache.delete_multi(entity_keys)

        self.error(204)

        logging.debug('Finished ProcessHandler.delete() function')

def main():
    application = webapp.WSGIApplication(
        [(r'/processes/(.*)\.json', ProcessHandler)], debug=utils._DEBUG)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
