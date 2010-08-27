#
# Copyright 2010 Flomosa, LLC
#

import logging
import os.path

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util

from exceptions import MissingException, UnauthorizedException
import models
import oauthapp
from settings import HTTPS_URL, FEEDBACK_EMAIL
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

        template_vars = {'step': step, 'url': HTTPS_URL,
            'email': FEEDBACK_EMAIL}

        template_file = os.path.join(os.path.dirname(__file__),
            'templates/step_feed_atom.tpl')
        output = template.render(template_file, template_vars)

        self.response.headers['Content-Type'] = 'application/atom+xml'
        self.response.out.write(output)

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
