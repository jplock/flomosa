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
from google.appengine.ext.webapp import template, util

from flomosa import exceptions, models, settings
#from flomosa.api import OAuthHandler


class StepHandler(webapp.RequestHandler):
    """Base step handler for API requests."""

    def is_client_allowed(self, step_key):
        client = self.is_valid()
        step = models.Step.get(step_key)
        process = step.process
        if client.id != process.client.id:
            raise exceptions.UnauthorizedException('Client "%s" is not ' \
                'authorized to access Process "%s".' % (client.id, process.id))
        return step


class StepAtomHandler(StepHandler):
    """Handles Atom requests for a given step."""

    def get(self, step_key):
        logging.debug('Begin StepAtomHandler.get() method')

        step = models.Step.get(step_key)
        # TODO: Need to determine how to authorization clients accessing the
        #       ATOM feed for a step. ATOM feeds can be signed according to
        #       RFC4287 - http://tools.ietf.org/html/rfc4287#section-8.5
        #step = self.is_client_allowed(step_key)

        template_vars = {'step': step, 'url': settings.HTTPS_URL,
                         'email': settings.FEEDBACK_EMAIL}
        template_vars['hubs'] = models.Hub.all()

        template_file = settings.TEMPLATE_DIR + '/step_feed_atom.tpl'
        output = template.render(template_file, template_vars)

        self.response.headers['Content-Type'] = 'application/atom+xml'
        self.response.out.write(output)

        logging.debug('Finished StepAtomHandler.get() method')


def main():
    """Handles step API requests."""
    application = webapp.WSGIApplication([(r'/steps/(.*)\.atom',
        StepAtomHandler)], debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
