#!/usr/bin/env python
#
# Copyright 2010 Flomosa, LLC
#

import logging
from datetime import datetime

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api import memcache

import models
import utils

class TaskHandler(webapp.RequestHandler):
    def post(self):
        logging.debug('Begin mail-viewed task handler')

        num_tries = self.request.headers['X-AppEngine-TaskRetryCount']
        logging.info('Task has been executed %s times' % num_tries)

        execution_key = self.request.get('execution_key')
        if not execution_key:
            logging.error('Missing "execution_key" parameter. Exiting.')
            return None

        viewed_date = self.request.get('viewed_date')
        if not viewed_date:
            logging.error('Missing "viewed_date" parameter. Exiting.')
            return None

        execution = utils.load_from_cache(execution_key, models.Execution)
        if not execution:
            logging.error('Execution "%s" was not found. Exiting.' % \
                execution_key)
            return None

        execution.viewed_date = datetime.fromtimestamp(float(viewed_date))
        if execution.sent_date:
            delta = execution.viewed_date - execution.sent_date
            execution.email_delay = delta.days * 86400 + delta.seconds

        try:
            execution.put()
        except:
            self.error(500)
            logging.error('Unable to save execution "%s". Re-queuing.' % \
                execution_key)
            return None

        memcache.set(execution_key, execution)

        logging.debug('Finished mail-viewed task handler')

def main():
    application = webapp.WSGIApplication([('/_ah/queue/mail-viewed',
        TaskHandler)], debug=utils._DEBUG)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
