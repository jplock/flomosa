#
# Copyright 2010 Flomosa, LLC
#

import base64
import logging
from datetime import datetime

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

import models
import utils

PIXEL_GIF = \
"""R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw==
"""


class ViewedHandler(webapp.RequestHandler):

    def get(self, execution_key):
        logging.debug('Begin ViewedHandler.get() method')

        logging.debug('Looking up Execution "%s" in memcache then datastore.' \
            % execution_key)
        execution = models.Execution.get(execution_key)
        if isinstance(execution, models.Execution):
            logging.debug('Execution "%s" found in datastore.' % execution.id)
            if not execution.viewed_date:
                logging.info('Execution "%s" not currently viewed, saving.' % \
                    execution.id)
                execution.viewed_date = datetime.now()
                if not execution.email_delay:
                    delta = execution.viewed_date - execution.sent_date
                    execution.email_delay = delta.days * 86400 + delta.seconds

                try:
                    execution.put()
                except Exception, e:
                    logging.error(e)
        else:
            logging.error('Execution "%s" not found in datastore.' % \
                execution_key)

        pixel = base64.b64decode(PIXEL_GIF)
        self.response.headers['Content-Type'] = 'image/gif'
        self.response.out.write(pixel)

        logging.debug('Finished ViewedHandler.get() method')


class ActionHandler(webapp.RequestHandler):

    def get(self, execution_key, action_key):
        logging.debug('Begin ActionHandler.get() method')

        logging.debug('Looking up Execution "%s" in memcache then datastore.' \
            % execution_key)
        execution = models.Execution.get(execution_key)
        if not execution:
            logging.error('Execution "%s" not found. Returning 404 to user.' \
                % execution_key)
            self.error(404)
            return None

        logging.debug('Looking up Action "%s" in memcache then datastore.' \
            % action_key)
        action = models.Action.get(action_key)
        if not isinstance(action, models.Action):
            logging.error('Action "%s" not found. Returning 404 to user.' % \
                action_key)
            self.error(404)
            return None

        execution.action = action
        execution.end_date = datetime.now()
        if execution.viewed_date and not execution.action_delay:
            delta = execution.end_date - execution.viewed_date
            execution.action_delay = delta.days * 86400 + delta.seconds
        if execution.start_date and not execution.duration:
            delta = execution.end_date - execution.start_date
            execution.duration = delta.days * 86400 + delta.seconds

        try:
            execution.put()
        except Exception, e:
            logging.error(e)

        self.response.out.write('Thank you. You can close this window.')

        logging.debug('Finished ActionHandler.get() method')

def main():
    application = webapp.WSGIApplication(
        [(r'/viewed/(.*)/(.*)\.json', ActionHandler),
        (r'/viewed/(.*)\.json', ViewedHandler)], debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
