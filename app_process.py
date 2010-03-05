#!/usr/bin/env python
#
# Copyright 2010 Flomosa, LLC
#

import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api import memcache

import models
import utils

class NewHandler(webapp.RequestHandler):

    def post(self):
        logging.debug('Begin NewHandler.post() function')

        name = self.request.get('name')
        if not name:
            return utils.build_json(self, 'Missing "name" parameter', code=400)

        description = self.request.get('description')

        process_key = utils.generate_key()
        process = models.Process(key_name=process_key, name=name,
            description=description)

        try:
            process.put()
        except:
            return utils.build_json(self, 'Unable to save process', code=500)

        memcache.set(process_key, process)

        utils.build_json(self, process.to_dict(), 201)

        logging.debug('Finished NewHandler.post() function')

class EditHandler(webapp.RequestHandler):

    def get(self, process_key):
        logging.debug('Begin EditHandler.get() function')

        process = utils.load_from_cache(process_key, models.Process)
        if not process:
            return utils.build_json(self,
                'Unable to find process with ID "%s"' % process_key, code=404)

        utils.build_json(self, process.to_dict())

        logging.debug('Finished EditHandler.get() function')

    def post(self, process_key):
        logging.debug('Begin EditHandler.post() function')

        process = utils.load_from_cache(process_key, models.Process)
        if not process:
            return utils.build_json(self,
                'Unable to find process with ID "%s"' % process_key, code=404)

        name = self.request.get('name', default_value=None)
        description = self.request.get('description', default_value=None)

        if name is not None:
            logging.info('Found "name" parameter')
            process.name = name
        if description is not None:
            logging.info('Found "description" parameter')
            process.description = description

        try:
            process.put()
        except:
            return utils.build_json(self, 'Unable to save process', code=500)

        memcache.set(process_key, process)

        utils.build_json(self, process.to_dict())

        logging.debug('Finished EditHandler.post() function')

def main():
    application = webapp.WSGIApplication(
        [('/processes/', NewHandler),
        (r'/processes/(.*)\.json', EditHandler)],
        debug=utils._DEBUG)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
