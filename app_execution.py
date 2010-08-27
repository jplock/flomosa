#
# Copyright 2010 Flomosa, LLC
#

import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

import models
import oauthapp
import utils


class ExecutionHandler(oauthapp.OAuthHandler):

    def is_client_allowed(self, execution_key):
        client = self.is_valid()
        execution = models.Execution.get(execution_key)
        process = execution.process
        if client.id != process.client.id:
            raise UnauthorizedException('Client "%s" is not authorized to ' \
                'access Process "%s".' % (client.id, process.id))
        return execution

    def get(self, execution_key):
        logging.debug('Begin ExecutionHandler.get() method')

        execution = self.is_client_allowed(execution_key)

        logging.info('Returning Execution "%s" as JSON to client.' % \
            execution.id)
        utils.build_json(self, execution.to_dict())

        logging.debug('Finished ExecutionHandler.get() method')

def main():
    application = webapp.WSGIApplication([(r'/executions/(.*)\.json',
        ExecutionHandler)], debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()