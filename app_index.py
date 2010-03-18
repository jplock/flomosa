#
# Copyright 2010 Flomosa, LLC
#

import os.path

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util

import authapp

class MainHandler(authapp.SecureRequestHandler):
    def get(self):
        template_vars = {}
        consumer = self.get_current_consumer()
        if consumer:
            template_vars['current_consumer'] = consumer

        template_file = os.path.join(os.path.dirname(__file__),
            'templates/index.tpl')
        output = template.render(template_file, template_vars)

        self.response.out.write(output)

def main():
    application = webapp.WSGIApplication([('/', MainHandler)], debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
