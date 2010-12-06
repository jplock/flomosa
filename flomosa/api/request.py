#!/usr/bin/env python2.5
# -*- coding: utf8 -*-
#
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2010 Flomosa, LLC
# All Rights Reserved.
#

import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api import taskqueue

from flomosa import exceptions, models, utils
from flomosa.api import OAuthHandler, build_json


class RequestHandler(OAuthHandler):
    """API handler for requests."""

    def get(self, request_key=None):
        logging.debug('Begin RequestHandler.get() method')

        client = self.is_valid()

        if not request_key:
            raise exceptions.MissingException(
                'Missing "request_key" parameter.')

        request = models.Request.get(request_key, client)

        build_json(self, request.to_dict())

        logging.debug('Finished RequestHandler.get() method')

    def post(self, request_key=None):
        logging.debug('Begin RequestHandler.post() method')

        data = self.request.params

        process_key = data.get('process', None)
        if not process_key:
            raise exceptions.MissingException('Missing "process" parameter.')

        process = models.Process.get(process_key)

        if not process.is_valid():
            raise exceptions.ValidationException(
                'Process "%s" is not valid.' % process_key)

        requestor = data.get('requestor', None)
        if not requestor:
            raise exceptions.MissingException('Missing "requestor" parameter.')

        if request_key:
            request = models.Request.get(request_key)
            if request:
                raise exceptions.InternalException(
                    'Request "%s" already exists.' % request_key)
        else:
            request_key = utils.generate_key()
            request = models.Request(key_name=request_key, process=process,
                                     client=process.client, requestor=requestor)

        callback_url = data.get('callback_url', None)
        response_url = data.get('response_url', None)

        reserved_keys = ['callback_url', 'response_url']

        for key, value in data.items():
            if not hasattr(request, key) and key not in reserved_keys:
                setattr(request, key, value)
        request.put()

        if callback_url:
            # Queue task to submit the callback response
            queue = taskqueue.Queue('request-callback')
            task = taskqueue.Task(params={'request_key': request.id,
                                          'callback_url': callback_url})
            queue.add(task)

        if response_url:
            logging.info('Permanently redirecting client to "%s".',
                         response_url)
            self.redirect(response_url, permanent=True)
        else:
            logging.info('Returning Request "%s" as JSON to client.',
                         request.id)
            build_json(self, {'key': request.id}, 201)

        logging.debug('Finished RequestHandler.post() method')

    def delete(self, request_key=None):
        logging.debug('Begin RequestHandler.delete() method')

        client = self.is_valid()

        if not request_key:
            raise exceptions.MissingException(
                'Missing "request_key" parameter.')

        request = models.Request.get(request_key, client)
        request.delete()

        self.error(204)

        logging.debug('Finished RequestHandler.delete() method')


def main():
    """API handler for requests."""
    application = webapp.WSGIApplication(
        [(r'/requests/(.*)\.json', RequestHandler),
        (r'/requests/', RequestHandler)], debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
