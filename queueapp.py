#
# Copyright 2010 Flomosa, LLC
#

import logging

from google.appengine.ext import webapp

from exceptions import HTTPException


class QueueHandler(webapp.RequestHandler):

    def handle_exception(self, exception, debug_mode):
        if debug_mode:
            super(QueueHandler, self).handle_exception(exception, debug_mode)
        else:
            logging.error(exception)
            if isinstance(exception, HTTPException):
                self.error(exception.status)
            return None

    def halt_requeue(self):
        "Re-queue the task in the queue."
        self.error(500)
        return None

    def halt_success(self):
        "Mark the task as being completed in the queue."
        self.error(200)
        return None
