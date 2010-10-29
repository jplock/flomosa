#!/usr/bin/env python2.5
# -*- coding: utf8 -*-
#
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2010 Flomosa, LLC
# All Rights Reserved.
#

import logging

from google.appengine.ext import db, webapp
from google.appengine.ext.webapp import util

from flomosa import exceptions, models
from flomosa.api import OAuthHandler, build_json


class ProcessHandler(OAuthHandler):
    """Handles process API requests."""

    def get(self, process_key):
        logging.debug('Begin ProcessHandler.get() method')

        process = self.is_client_allowed(process_key)

        logging.debug('Returning Process "%s" as JSON to client.', process.id)
        build_json(self, process.to_dict())

        logging.debug('Finished ProcessHandler.get() method')

    def put(self, process_key=None):
        logging.debug('Begin ProcessHandler.put() method')

        client = self.is_valid()

        from django.utils import simplejson
        data = simplejson.loads(self.request.body)

        if 'name' not in data:
            raise exceptions.MissingException('Missing "name" parameter.')
        if 'kind' not in data:
            raise exceptions.MissingException('Missing "kind" parameter.')

        if data['kind'] != 'Process':
            raise exceptions.MissingException(
                'Invalid "kind" parameter; expected "kind=Process".')

        # Load the process data
        process = models.Process.from_dict(client, data, process_key)
        process.put()

        # Clear out any old steps and actions
        process.delete_steps_actions()

        # Load any steps on this process
        logging.info('Loading steps for Process "%s".', process.id)
        steps = data.get('steps', None)
        if steps:
            try:
                db.run_in_transaction(process.add_steps, steps)
            except Exception, exc:
                process.delete_steps_actions()
                raise exc

        # Load any actions on this process
        logging.info('Loading actions for Process "%s".', process.id)
        actions = data.get('actions', None)
        if actions:
            try:
                db.run_in_transaction(process.add_actions, actions)
            except Exception, exc:
                process.delete_steps_actions()
                raise exc

        logging.info('Returning Process "%s" as JSON to client.', process.id)
        build_json(self, {'key': process.id}, 201)

        logging.debug('Finished ProcessHandler.put() method')

    def delete(self, process_key):
        logging.debug('Begin ProcessHandler.delete() method')

        process = self.is_client_allowed(process_key)
        process.delete()

        self.error(204)

        logging.debug('Finished ProcessHandler.delete() method')


def main():
    """Handles process API requests."""
    application = webapp.WSGIApplication([
        (r'/processes/(.*)\.json', ProcessHandler),
        (r'/processes/', ProcessHandler)], debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
