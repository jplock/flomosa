#!/usr/bin/env python

import uuid
import logging
from django.utils import simplejson
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api import memcache
import models
import utils

class NewHandler(webapp.RequestHandler):
    def post(self):
        logging.debug('Begin post function')

        name = self.request.get('name')
        if not name:
            return utils.build_json(self, 'Missing "name" parameter', code=400)

        description = self.request.get('description')

        id = str(uuid.uuid4())
        process = models.Process(key_name=id, name=name,
            description=description)

        try:
            process.put()
        except:
            return utils.build_json(self, 'Unable to save process', code=500)

        self.error(201)
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(process.to_json())

        logging.debug('Finished post function')

class EditHandler(webapp.RequestHandler):
    def get(self, process_key):
        logging.debug('Begin get function')

        process = utils.load_from_cache(process_key, models.Process)
        if not process:
            return utils.build_json(self,
                'Unable to find process with ID "%s"' % process_key, code=404)

        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(process.to_json())

        logging.debug('Finished get function')

    def post(self, process_key):
        logging.debug('Begin post function')



        logging.debug('Finished post function')

def main():
    application = webapp.WSGIApplication([
        ('/processes/', NewHandler),
        (r'/processes/(.*)\.json', EditHandler)
        ], debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()