#!/usr/bin/env python2.5
# -*- coding: utf8 -*-
#
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2010 Flomosa, LLC
# All Rights Reserved.
#

__all__ = ['QueueHandler']

import logging

from google.appengine.ext import webapp

from flomosa import exceptions


class QueueHandler(webapp.RequestHandler):
    """Base handler for the other queue handlers."""

    def handle_exception(self, exception, debug_mode):
        if debug_mode:
            super(QueueHandler, self).handle_exception(exception, debug_mode)
        else:
            logging.error(exception)
            if isinstance(exception, exceptions.HTTPException):
                self.error(exception.status)
            return None

    def halt_requeue(self):
        """Re-queue the task in the queue."""
        self.error(500)
        return None

    def halt_success(self):
        """Mark the task as being completed in the queue."""
        self.error(200)
        return None
