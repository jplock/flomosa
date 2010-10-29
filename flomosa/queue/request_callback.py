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
    """Handles sending the request ID to a callback URL specified in the
    request form data."""

    def post(self):
        logging.debug('Begin request-callback task handler')

        num_tries = self.request.headers['X-AppEngine-TaskRetryCount']
        logging.info('Task has been executed %s times', num_tries)

        request_key = self.request.get('request_key')
        callback_url = self.request.get('callback_url')

        if not request_key:
            raise exceptions.MissingException(
                'Missing "request_key" parameter.')

        if not callback_url:
            raise exceptions.MissingException(
                'Missing "callback_url" parameter.')

        request = models.Request.get(request_key)

        form_data = urllib.urlencode({'key': request.id})

        rpc = urlfetch.create_rpc(deadline=2)
        urlfetch.make_fetch_call(rpc, url=callback_url, payload=form_data,
            method=urlfetch.POST,
            headers={'Content-Type': 'application/x-www-form-urlencoded'})

        try:
            result = rpc.get_result()
            if result.status_code == 200:
                logging.info('Submitted POST request to "%s" for Request ' \
                             '"%s".', callback_url, request.id)
            else:
                logging.warning('Received an HTTP status of "%s" when ' \
                    'submitting POST request to "%s" for Request "%s".',
                    result.status_code, callback_url, request.id)
                self.halt_requeue()
        except urlfetch.DownloadError, ex:
            logging.warning('Could not submit POST request to "%s" for ' \
                'Request "%s": %s', callback_url, request.id, ex)
            self.halt_requeue()

        logging.debug('Finished request-callback task handler')


def main():
    """Handles sending the request ID to a callback URL specified in the
    request form data."""
    application = webapp.WSGIApplication([('/_ah/queue/request-callback',
        TaskHandler)], debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
