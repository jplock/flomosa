#
# Copyright 2010 Flomosa, LLC
#

import os.path
import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util

class MainHandler(webapp.RequestHandler):
    def get(self):
        directory = os.path.dirname(__file__)
        template_file = os.path.join(directory, 'templates/index.tpl')

        template_vars = {
            'name': 'test'
        }

        output = template.render(template_file, template_vars)

        self.response.out.write(output)

def main():
    application = webapp.WSGIApplication([('/', MainHandler)],
        debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
