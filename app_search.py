#!/usr/bin/env python
#
# Copyright 2010 Flomosa, LLC
#

import logging
import time
from datetime import datetime

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api import memcache

import models
import utils


class ProcessHandler(webapp.RequestHandler):

    def get(self, process_key):
        logging.debug('Begin ProcessHandler.get() function')

        process = utils.load_from_cache(process_key, models.Process)
        if not process:
            self.error(404)
            return None



        logging.debug('Finished ProcessHandler.get() function')


class StepHandler(webapp.RequestHandler):

    def get(self, step_key):
        logging.debug('Begin StepHandler.get() function')

        step = utils.load_from_cache(step_key, models.Step)
        if not step:
            self.error(404)
            return None



        logging.debug('Finished StepHandler.get() function')


def main():
    application = webapp.WSGIApplication(
        [(r'/search/process/(.*)\.json', ProcessHandler),
        (r'/search/step/(.*)\.json', StepHandler)],
        debug=utils._DEBUG)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
