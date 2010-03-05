#!/usr/bin/env python
#
# Copyright 2010 Flomosa, LLC
#

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
import utils

class MainHandler(webapp.RequestHandler):
    def get(self):
        self.response.out.write('Hello!')

def main():
    application = webapp.WSGIApplication([('/', MainHandler)],
        debug=utils._DEBUG)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
