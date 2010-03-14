#!/usr/bin/env python
#
# Copyright 2010 Flomosa, LLC
#

import logging
from datetime import datetime

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api import memcache
from google.appengine.runtime import apiproxy_errors

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

        logging.info('Looking up Execution "%s" in memcache then datastore.' % \
            execution_key)
        execution = utils.load_from_cache(execution_key, models.Execution)
        if not isinstance(execution, models.Execution):
            logging.error('Execution "%s" was not found. Exiting.' % \
                execution_key)
            return None

        execution.viewed_date = datetime.fromtimestamp(float(viewed_date))
        if execution.sent_date:
            delta = execution.viewed_date - execution.sent_date
            execution.email_delay = delta.days * 86400 + delta.seconds

        logging.info('Storing Execution "%s" in datastore.' % execution.id)
        try:
            execution.put()
        except apiproxy_errors.CapabilityDisabledError:
            logging.error('Unable to save Execution "%s" due to maintenance.' \
                ' Re-queuing.' % execution.id)
            self.error(500)
            return None
        except:
            logging.error('Unable to save Execution "%s". Re-queuing.' % \
                execution.id)
            self.error(500)
            return None

        logging.info('Storing Execution "%s" in memcache.' % execution.id)
        memcache.set(execution.id, execution)

        logging.debug('Finished mail-viewed task handler')

def main():
    application = webapp.WSGIApplication([('/_ah/queue/mail-viewed',
        TaskHandler)], debug=utils._DEBUG)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
