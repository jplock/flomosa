#!/usr/bin/env python2.5
# -*- coding: utf8 -*-
#
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2010 Flomosa, LLC
# All Rights Reserved.
#

import logging
import urllib

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api import urlfetch

from flomosa import exceptions, models, is_development
from flomosa.queue import QueueHandler


class TaskHandler(QueueHandler):
    """Handles notifying the PubSubHubbub hubs that a step has been updated."""

    def post(self):
        logging.debug('Begin step-callback task handler')

        num_tries = self.request.headers['X-AppEngine-TaskRetryCount']
        logging.info('Task has been executed %s times', num_tries)

        step_key = self.request.get('step_key')
        callback_url = self.request.get('callback_url')

        if not step_key:
            raise exceptions.MissingException('Missing "step_key" parameter.')

        if not callback_url:
            raise exceptions.MissingException(
                'Missing "callback_url" parameter.')

        if is_development():
            logging.info('Skip POST\'ing hub notifications in development.')
            return None

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
                logging.info('Submitted POST request to "%s" for Step "%s".',
                             callback_url, step.id)
            else:
                logging.warning('Received an HTTP status of "%s" when ' \
                    'submitting POST request to "%s" for Step "%s".',
                    result.status_code, callback_url, step.id)
                self.halt_requeue()
        except urlfetch.DownloadError, ex:
            logging.warning('Could not submit POST request to "%s" for ' \
                'Step "%s": %s.', callback_url, step.id, ex)
            self.halt_requeue()

        logging.debug('Finished step-callback task handler')


def main():
    """Handles notifying the PubSubHubbub hubs that a step has been updated."""
    application = webapp.WSGIApplication([('/_ah/queue/step-callback',
        TaskHandler)], debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
