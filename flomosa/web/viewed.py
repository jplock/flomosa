#!/usr/bin/env python2.5
# -*- coding: utf8 -*-
#
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2010 Flomosa, LLC
# All Rights Reserved.
#

import base64
import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

from flomosa import models, utils


PIXEL_GIF = \
"""R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw==
"""


class ViewedHandler(webapp.RequestHandler):

    def output_pixel(self):
        """Output a transparent pixel GIF image to the user"""
        pixel = base64.b64decode(PIXEL_GIF)
        self.error(200)
        self.response.headers['Content-Type'] = 'image/gif'
        self.response.out.write(pixel)
        return None

    def handle_exception(self, exception, debug_mode):
        if debug_mode:
            super(ViewedHandler, self).handle_exception(exception, debug_mode)
        else:
            logging.error(exception)
            self.output_pixel()

    def get(self, execution_key):
        logging.debug('Begin ViewedHandler.get() method')

        execution = models.Execution.get(execution_key)
        execution.set_viewed()

        self.output_pixel()

        logging.debug('Finished ViewedHandler.get() method')


class ActionHandler(webapp.RequestHandler):

    def handle_exception(self, exception, debug_mode):
        if debug_mode:
            super(ActionHandler, self).handle_exception(exception, debug_mode)
        else:
            logging.error(exception)
            self.error(404)
            return None

    def get(self, execution_key, action_key):
        logging.debug('Begin ActionHandler.get() method')

        execution = models.Execution.get(execution_key)
        action = models.Action.get(action_key)
        execution.set_completed(action)

        # TODO: Make this a nicer page
        self.response.out.write('Thank you. You can close this window.')

        logging.debug('Finished ActionHandler.get() method')


def main():
    application = webapp.WSGIApplication(
        [(r'/viewed/(.*)/(.*)\.json', ActionHandler),
        (r'/viewed/(.*)\.json', ViewedHandler)], debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
