#!/usr/bin/env python

import uuid
import logging
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api import memcache
from google.appengine.api.labs import taskqueue
import models

class NewHandler(webapp.RequestHandler):
    def store_request(self):
        try:
            process_key = self.request.params['process']
        except KeyError:
            raise ValueError('Missing "process" parameter')

        process = memcache.get(process_key)
        if not process:
            process = models.Process.get_by_key_name(process_key)
            if not process:
                raise ValueError('"%s" is not a valid process key' % process_key)
            memcache.set(process_key, process)

        try:
            requestor = self.request.params['requestor']
        except KeyError:
            raise ValueError('Missing "requestor" parameter')

        id = str(uuid.uuid4())
        params = {'_id': id}
        for key, value in self.request.params.items():
            params[key] = value

        queue = taskqueue.Queue('request-store')
        task = taskqueue.Task(params=params)
        queue.add(task)
        return id

    def get(self):
        try:
            id = self.store_request()
        except ValueError as e:
            self.response.clear()
            self.response.set_status(500)
            self.response.out.write('ERROR: '+e.message)
            return None

        self.response.out.write('Request ID: '+id)

    def post(self):
        try:
            id = self.store_request()
        except ValueError as e:
            self.response.clear()
            self.response.set_status(500)
            self.response.out.write('ERROR: '+e.message)
            return None

        self.response.out.write('Request ID: '+id)

class EditHandler(webapp.RequestHandler):
    def get(self, id):
        self.response.out.write('Got ID: '+id)

def main():
    application = webapp.WSGIApplication([
        ('/requests/', NewHandler),
        (r'/requests/(.*)\.json', EditHandler)
        ], debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()