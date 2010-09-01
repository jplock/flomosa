#
# Copyright 2010 Flomosa, LLC
#

import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

import models
import oauthapp


class ProcessHandler(oauthapp.OAuthHandler):

    def get(self, process_key):
        logging.debug('Begin ProcessHandler.get() method')

        process = models.Process.get(process_key)

        logging.debug('Finished ProcessHandler.get() method')


class StepHandler(oauthapp.OAuthHandler):

    def get(self, step_key):
        logging.debug('Begin StepHandler.get() method')

        step = models.Step.get(step_key)
        
        logging.debug('Finished StepHandler.get() method')


def main():
    application = webapp.WSGIApplication(
        [(r'/search/process/(.*)\.json', ProcessHandler),
        (r'/search/step/(.*)\.json', StepHandler)], debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()