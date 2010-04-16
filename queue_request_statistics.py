#
# Copyright 2010 Flomosa, LLC
#

import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

import models


class TaskHandler(webapp.RequestHandler):
    def post(self):
        logging.debug('Begin request-statistics task handler')

        num_tries = self.request.headers['X-AppEngine-TaskRetryCount']
        logging.info('Task has been executed %s times' % num_tries)

        request_key = self.request.get('request_key')
        process_key = self.request.get('process_key')
        step_key = self.request.get('step_key')

        if not request_key:
            logging.error('Missing "request_key" parameter. Exiting.')
            return None

        request = models.Request.get(request_key)
        if request is None:
            logging.error('Request "%s" not found in datastore. Exiting.' % \
                request_key)
            return None

        if not process_key:
            logging.error('Missing "process_key" parameters. Exiting.')
            return None

        process = models.Process.get(process_key)
        if not process:
            logging.error('Process "%s" not found in datastore. Exiting.' % \
                process_key)
            return None

        try:
            models.Statistic.store_stats(request, process)
        except Exception, e:
            logging.error('Storing statistics failed for Request "%s": %s' % \
                (request.id, e))

        logging.debug('Finished request-statistics task handler')

def main():
    application = webapp.WSGIApplication([('/_ah/queue/request-statistics',
        TaskHandler)], debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
