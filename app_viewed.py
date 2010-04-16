#
# Copyright 2010 Flomosa, LLC
#

import base64
import logging

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

        execution = models.Execution.get(execution_key)
        if execution:
            if not execution.viewed_date:
                logging.info('Execution "%s" has not been viewed, storing.' % \
                    execution.id)

                try:
                    execution.set_viewed()
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

        execution = models.Execution.get(execution_key)
        if not execution:
            logging.error('Execution "%s" not found. Returning 404 to user.' \
                % execution_key)
            self.error(404)
            return None

        action = models.Action.get(action_key)
        if not action:
            logging.error('Action "%s" not found. Returning 404 to user.' % \
                action_key)
            self.error(404)
            return None

        try:
            execution.set_completed(action)
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
