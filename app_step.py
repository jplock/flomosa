#
# Copyright 2010 Flomosa, LLC
#

import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util

from exceptions import MissingException, UnauthorizedException
import models
import oauthapp
import utils


class StepHandler(oauthapp.OAuthHandler):

    def is_client_allowed(self, step_key):
        client = self.is_valid()
        step = models.Step.get(step_key)
        if client.id != step.process.client.id:
            raise UnauthorizedException('Client "%s" is not authorized to ' \
                'access Step "%s".' % (client.id, step.id))
        return step

class StepAtomHandler(StepHandler):

    def get(self, step_key):
        logging.debug('Begin StepAtomHandler.get() method')

        step = self.is_client_allowed()

        logging.debug('Finished StepAtomHandler.get() method')

class StepRssHandler(StepHandler):

    def get(self, step_key):
        logging.debug('Begin StepRssHandler.get() method')

        step = self.is_client_allowed()

        logging.debug('Finished StepRssHandler.get() method')

def main():
    application = webapp.WSGIApplication([
        (r'/steps/(.*)/rss\.xml', StepRssHandler),
        (r'/steps/(.*)/atom\.xml', StepAtomHandler)], debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
