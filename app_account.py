#
# Copyright 2010 Flomosa, LLC
#

import os.path
import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util

class AccountHandler(webapp.RequestHandler):
    def get(self):
        template_vars = {
            'name': 'test'
        }

        directory = os.path.dirname(__file__)
        template_file = os.path.join(directory, 'templates/account.tpl')
        output = template.render(template_file, template_vars)

        self.response.out.write(output)

class RegisterHandler(webapp.RequestHandler):
    def show_form(self, template_vars={}):
        directory = os.path.dirname(__file__)
        template_file = os.path.join(directory,
            'templates/account_register.tpl')
        return template.render(template_file, template_vars)

    def post(self):
        email_address = self.request.get('email_address')

        template_vars = {}
        for key, value in self.request.params.items():
            template_vars[key] = value

        self.response.out.write(template_vars)
        self.response.out.write(self.show_form(template_vars))

    def get(self):
        self.response.out.write(self.show_form())

class LoginHandler(webapp.RequestHandler):
    def get(self):
        directory = os.path.dirname(__file__)
        template_file = os.path.join(directory,
            'templates/account_login.tpl')

        template_vars = {
            'name': 'test'
        }

        output = template.render(template_file, template_vars)

        self.response.out.write(output)

class LogoutHandler(webapp.RequestHandler):
    def get(self):
        directory = os.path.dirname(__file__)
        template_file = os.path.join(directory,
            'templates/account_register.tpl')

        template_vars = {
            'name': 'test'
        }

        output = template.render(template_file, template_vars)

        self.response.out.write(output)

def main():
    application = webapp.WSGIApplication(
        [(r'/account/login/', LoginHandler),
        (r'/account/logout/', LogoutHandler),
        (r'/account/register/', RegisterHandler),
        (r'/account/', AccountHandler)],
        debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
