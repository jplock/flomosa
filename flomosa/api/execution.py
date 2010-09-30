#!/usr/bin/env python
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

from flomosa import exceptions, models
from flomosa.api import OAuthHandler, build_json


class ExecutionHandler(OAuthHandler):

    def is_client_allowed(self, execution_key):
        client = self.is_valid()
        execution = models.Execution.get(execution_key)
        process = execution.process
        if client.id != process.client.id:
            raise exceptions.UnauthorizedException('Client "%s" is not ' \
                'authorized to access Process "%s".' % (client.id, process.id))
        return execution

    def get(self, execution_key=None):
        logging.debug('Begin ExecutionHandler.get() method')

        execution = self.is_client_allowed(execution_key)

        logging.info('Returning Execution "%s" as JSON to client.' % \
            execution.id)
        build_json(self, execution.to_dict())

        logging.debug('Finished ExecutionHandler.get() method')


def main():
    application = webapp.WSGIApplication([
        (r'/executions/(.*)\.json', ExecutionHandler),
        (r'/executions/', ExecutionHandler)], debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
