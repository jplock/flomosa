#
# Copyright 2010 Flomosa, LLC
#

import logging
import urllib

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api import urlfetch

from flomosa import exceptions, models, queueapp


class TaskHandler(queueapp.QueueHandler):

    def post(self):
        logging.debug('Begin step-callback task handler')

        num_tries = self.request.headers['X-AppEngine-TaskRetryCount']
        logging.info('Task has been executed %s times' % num_tries)

        step_key = self.request.get('step_key')
        callback_url = self.request.get('callback_url')

        if not step_key:
            raise exceptions.MissingException('Missing "step_key" parameter.')

        if not callback_url:
            raise exceptions.MissingException('Missing "callback_url" ' \
                                              'parameter.')

        step = models.Step.get(step_key)

        hub_data = urllib.urlencode({'hub.url': step.get_absolute_url(),
            'hub.mode': 'publish'}, doseq=True)

        rpc = urlfetch.create_rpc(deadline=5)
        urlfetch.make_fetch_call(rpc, url=callback_url, payload=hub_data,
            method=urlfetch.POST,
            headers={'Content-Type': 'application/x-www-form-urlencoded'})

        try:
            result = rpc.get_result()
            if result.status_code == 204:
                logging.info('Submitted POST request to "%s" for Step ' \
                    '"%s".' % (callback_url, step.id))
            else:
                logging.warning('Received an HTTP status of "%s" when ' \
                    'submitting POST request to "%s" for Step "%s".' % (
                    result.status_code, callback_url, step.id))
                self.halt_requeue()
        except urlfetch.DownloadError, ex:
            logging.warning('Could not submit POST request to "%s" for ' \
                'Step "%s" (%s).' % (callback_url, step.id, ex))
            self.halt_requeue()

        logging.debug('Finished step-callback task handler')

def main():
    application = webapp.WSGIApplication([('/_ah/queue/step-callback',
        TaskHandler)], debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
