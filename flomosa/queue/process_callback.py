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

from flomosa import exceptions, models
from flomosa.queue import QueueHandler


class TaskHandler(QueueHandler):

    def post(self):
        logging.debug('Begin process-callback task handler')

        num_tries = self.request.headers['X-AppEngine-TaskRetryCount']
        logging.info('Task has been executed %s times' % num_tries)

        execution_key = self.request.get('execution_key')
        callback_url = self.request.get('callback_url')
        timestamp = self.request.get('timestamp')  # POSIX UTC timestamp

        if not execution_key:
            raise exceptions.MissingException(
                'Missing "execution_key" parameter.')
        if not callback_url:
            raise exceptions.MissingException(
                'Missing "callback_url" parameter.')
        if not timestamp:
            raise exceptions.MissingException('Missing "timestamp" parameter.')

        execution = models.Execution.get(execution_key)

        form_data = urllib.urlencode({'key': execution.request.id,
                                      'step': execution.step.name,
                                      'action': execution.action.name,
                                      'timestamp': timestamp})

        rpc = urlfetch.create_rpc(deadline=2)
        urlfetch.make_fetch_call(rpc, url=callback_url, payload=form_data,
            method=urlfetch.POST,
            headers={'Content-Type': 'application/x-www-form-urlencoded'})

        try:
            result = rpc.get_result()
            if result.status_code == 200:
                logging.info(
                    'Submitted POST request to "%s" for Request "%s".' % (
                        callback_url, request.id))
            else:
                logging.warning('Received an HTTP status of "%s" when ' \
                    'submitting POST request to "%s" for Request "%s".' % (
                    result.status_code, callback_url, request.id))
                self.halt_requeue()
        except urlfetch.DownloadError, ex:
            logging.warning('Could not submit POST request to "%s" for ' \
                'Request "%s": %s' % (callback_url, request.id, ex))
            self.halt_requeue()

        logging.debug('Finished process-callback task handler')


def main():
    application = webapp.WSGIApplication([('/_ah/queue/process-callback',
        TaskHandler)], debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
