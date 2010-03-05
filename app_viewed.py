#!/usr/bin/env python
#
# Copyright 2010 Flomosa, LLC
#

import base64
import logging
import time
from datetime import datetime

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api import memcache
from google.appengine.api.labs import taskqueue

import models
import utils

_PIXEL_GIF = \
"""R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw==
"""

class ViewedHandler(webapp.RequestHandler):

    def get(self, execution_key):
        logging.debug('Begin ViewedHandler.get() function')

        execution = utils.load_from_cache(execution_key, models.Execution)
        if not execution:
            self.error(404)
            return None

        if not execution.viewed_date:
            params = {'execution_key': execution_key,
                'viewed_date': time.time()}

            queue = taskqueue.Queue('mail-viewed')
            task = taskqueue.Task(params=params)
            queue.add(task)

        pixel = base64.b64decode(_PIXEL_GIF)
        self.response.headers['Content-Type'] = 'image/gif'
        self.response.out.write(pixel)

        logging.debug('Finished ViewedHandler.get() function')

class ActionHandler(webapp.RequestHandler):

    def get(self, execution_key, action_key):
        logging.debug('Begin ActionHandler.get() function')

        execution = utils.load_from_cache(execution_key, models.Execution)
        if not execution:
            self.error(404)
            return None

        action = utils.load_from_cache(action_key, models.Action)
        if not action:
            self.error(404)
            return None

        execution.action = action
        execution.end_date = datetime.now()
        delta = execution.end_date - execution.start_date
        execution.duration = delta.days * 86400 + delta.seconds

        if execution.viewed_date:
            delta = execution.end_date - execution.viewed_date
            execution.action_delay = delta.days * 86400 + delta.seconds

        try:
            execution.put()
        except:
            self.error(500)
            logging.error('Unable to save execution "%s"' % execution_key)
            return None

        memcache.set(execution_key, execution)

        # See queue_request_store.py code

        self.response.out.write('Thank you. This window will now close.')

        logging.debug('Finished ActionHandler.get() function')

def main():
    application = webapp.WSGIApplication(
        [(r'/viewed/(.*)/(.*)\.json', ActionHandler),
        (r'/viewed/(.*)\.json', ViewedHandler)],
        debug=utils._DEBUG)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
