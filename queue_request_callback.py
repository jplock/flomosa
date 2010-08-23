#
# Copyright 2010 Flomosa, LLC
#

import logging
import urllib

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api import urlfetch

import models


class TaskHandler(webapp.RequestHandler):
    def post(self):
        logging.debug('Begin request-callback task handler')

        num_tries = self.request.headers['X-AppEngine-TaskRetryCount']
        logging.info('Task has been executed %s times' % num_tries)

        request_key = self.request.get('request_key')
        callback_url = self.request.get('callback_url')

        if not request_key:
            logging.error('Missing "request_key" parameter. Exiting.')
            return None

        if not callback_url:
            logging.error('Missing "callback_url" parameter. Exiting.')
            return None

        request = models.Request.get(request_key)
        if request is None:
            logging.error('Request "%s" not found in datastore. Exiting.' % \
                request_key)
            return None

        response_fields = {'key': request.id}

        form_data = urllib.urlencode(response_fields)

        rpc = urlfetch.create_rpc(deadline=2)
        urlfetch.make_fetch_call(rpc, url=callback_url, payload=form_data,
            method=urlfetch.POST,
            headers={'Content-Type': 'application/x-www-form-urlencoded'})

        try:
            result = rpc.get_result()
            if result.status_code == 200:
                logging.info('Submitted POST request to "%s" for Request ' \
                    '"%s".' % (callback_url, request.id))
            else:
                logging.warning('Could not submit POST request to "%s" for ' \
                    'Request "%s".' % (callback_url, request.id))
        except urlfetch.DownloadError, e:
            logging.warning('Could not submit POST request to "%s" for ' \
                'Request "%s" (%s).' % (callback_url, request.id, e))

        logging.debug('Finished request-callback task handler')

def main():
    application = webapp.WSGIApplication([('/_ah/queue/request-callback',
        TaskHandler)], debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
