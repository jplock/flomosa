#
# Copyright 2010 Flomosa, LLC
#

import logging
from datetime import datetime

from google.appengine.ext import db, webapp
from google.appengine.ext.webapp import util

import models


class TaskHandler(webapp.RequestHandler):
    def post(self):
        logging.debug('Begin request-statistics task handler')

        num_tries = self.request.headers['X-AppEngine-TaskRetryCount']
        logging.info('Task has been executed %s times' % num_tries)

        request_key = self.request.get('request_key')
        process_key = self.request.get('process_key')
        timestamp = self.request.get('timestamp') # POSIX UTC timestamp

        if not request_key:
            logging.error('Missing "request_key" parameter. Exiting.')
            return None

        request = models.Request.get(request_key)
        if request is None:
            logging.error('Request "%s" not found in datastore. Exiting.' % \
                request_key)
            return None

        if not process_key:
            logging.error('Missing "process_key" parameter. Exiting.')
            return None

        process = models.Process.get(process_key)
        if not process:
            logging.error('Process "%s" not found in datastore. Exiting.' % \
                process_key)
            return None

        if not timestamp:
            logging.error('Missing "timestamp" parameter. Exiting.')
            return None

        try:
            stat_time = datetime.utcfromtimestamp(timestamp)
        except ValueError, e:
            logging.error('Could not convert timestamp "%s": %s' % \
                (timestamp, e))
            return None

        try:
            db.run_in_transaction(models.Statistic.store_stats, request,
                process, timestamp=stat_time)
        except db.TransactionFailedError, e:
            logging.critical('Storing statistics failed for Request "%s". ' \
                'Re-queuing.' % request.id)
            self.error(500)
            return None

        logging.debug('Finished request-statistics task handler')

def main():
    application = webapp.WSGIApplication([('/_ah/queue/request-statistics',
        TaskHandler)], debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
