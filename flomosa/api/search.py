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

from flomosa import models
from flomosa.api import OAuthHandler, build_json


class ProcessHandler(OAuthHandler):
    """Handles process search API requests."""

    def get(self, process_key):
        logging.debug('Begin ProcessHandler.get() method')

        #process = models.Process.get(process_key)

        logging.debug('Finished ProcessHandler.get() method')


class StepHandler(OAuthHandler):
    """Handles step search API requests."""

    def get(self, step_key):
        logging.debug('Begin StepHandler.get() method')

        #step = models.Step.get(step_key)

        logging.debug('Finished StepHandler.get() method')


def main():
    """Handles search API requests."""
    application = webapp.WSGIApplication(
        [(r'/search/process/(.*)\.json', ProcessHandler),
        (r'/search/step/(.*)\.json', StepHandler)], debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
