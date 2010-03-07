#!/usr/bin/env python
#
# Copyright 2010 Flomosa, LLC
#

import logging

from django.utils import simplejson
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp import util
from google.appengine.api import memcache

import models
import utils


class TaskHandler(webapp.RequestHandler):
    def post(self):
        logging.debug('Begin process-store task handler')

        num_tries = self.request.headers['X-AppEngine-TaskRetryCount']
        logging.info('Task has been executed %s times' % num_tries)

        process_key = self.request.get('_id')

        try:
            data = simplejson.loads(self.request.get('data'))
        except:
            logging.error('Error parsing JSON request. Exiting.')
            return None

        try:
            name = data['name']
        except KeyError:
            logging.error('Missing "name" parameter. Exiting.')
            return None

        try:
            description = data['description']
        except KeyError:
            description = None

        process = utils.load_from_cache(process_key, models.Process)
        if process:
            process.name = name
            if description is not None:
                process.description = description
        else:
            process = models.Process(key_name=process_key, name=name,
                description=description)

        try:
            process.put()
        except:
            logging.error('Unable to save Process ID "%s" in datastore. ' \
                'Re-queuing.' % process_key)
            self.error(500)
            return None

        logging.debug('Finished process-store task handler')

def main():
    application = webapp.WSGIApplication([('/_ah/queue/process-store',
        TaskHandler)], debug=utils._DEBUG)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
