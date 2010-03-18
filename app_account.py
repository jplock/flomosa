#
# Copyright 2010 Flomosa, LLC
#

import os.path
import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util

import models
import utils
import authapp


class AccountHandler(authapp.SecureRequestHandler):
    def get(self):
        logging.debug('Begin AccountHandler.get() method')

        template_vars = {}

        consumer = self.get_current_consumer()
        if not consumer:
            self.redirect('/account/login/')
        else:
            template_vars['current_consumer'] = consumer

        template_file = os.path.join(os.path.dirname(__file__),
            'templates/account.tpl')
        output = template.render(template_file, template_vars)
        self.response.out.write(output)

        logging.debug('Finished AccountHandler.get() method')

class RegisterHandler(authapp.SecureRequestHandler):
    def show_form(self, template_vars={}):
        template_file = os.path.join(os.path.dirname(__file__),
            'templates/account_register.tpl')
        return template.render(template_file, template_vars)

    def post(self):
        logging.debug('Begin RegisterHandler.post() method')

        template_vars = {
            'messages': []
        }

        email_address = self.request.get('email_address')
        password = self.request.get('password')
        confirm_password = self.request.get('confirm_password')
        first_name = self.request.get('first_name')
        last_name = self.request.get('last_name')

        if not email_address:
            template_vars['messages'].append('Please provide an email address')
        if not password:
            template_vars['messages'].append('Please provide a password')
        elif not confirm_password:
            template_vars['messages'].append('Please confirm your password')
        elif password != confirm_password:
            template_vars['messages'].append('Passwords do not match')

        query = models.Consumer.all()
        query.filter('email_address =', email_address)
        if query.get():
            template_vars['messages'].append('Email address already exists')

        if template_vars['messages']:
            for key, value in self.request.params.items():
                template_vars[key] = value

            self.response.out.write(self.show_form(template_vars))
        else:
            consumer_key = utils.generate_key()
            consumer = models.Consumer(key_name=consumer_key,
                email_address=email_address,
                password=self.encrypt_string(password))
            consumer.oauth_token = utils.generate_key()
            consumer.oauth_secret = utils.generate_key()

            try:
                consumer.put()
            except Exception, e:
                logging.error(e)

            self.set_secure_cookie(consumer_key)

            self.redirect('/')

        logging.debug('Finished RegisterHandler.post() method')

    def get(self):
        logging.debug('Begin RegisterHandler.get() method')

        consumer = self.get_current_consumer()
        if consumer:
            self.redirect('/account/')

        self.response.out.write(self.show_form())

        logging.debug('Finished RegisterHandler.get() method')

class LoginHandler(authapp.SecureRequestHandler):
    def show_form(self, template_vars={}):
        template_file = os.path.join(os.path.dirname(__file__),
            'templates/account_login.tpl')
        return template.render(template_file, template_vars)

    def post(self):
        logging.debug('Begin LoginHandler.post() method')

        template_vars = {
            'messages': []
        }

        email_address = self.request.get('email_address')
        password = self.request.get('password')

        if not email_address:
            template_vars['messages'].append('Please provide an email address')
        if not password:
            template_vars['messages'].append('Please provide a password')

        if email_address and password:
            query = models.Consumer.all()
            query.filter('email_address =', email_address)
            query.filter('password =', self.encrypt_string(password))
            consumer = query.get()
            if isinstance(consumer, models.Consumer):
                self.set_secure_cookie(consumer.id)
                self.redirect('/account/')
            else:
                template_vars['messages'].append('Invalid email address or ' \
                    'password')

        if template_vars['messages']:
            for key, value in self.request.params.items():
                template_vars[key] = value

            self.response.out.write(self.show_form(template_vars))

        logging.debug('Finished LoginHandler.post() method')

    def get(self):
        logging.debug('Begin LoginHandler.get() method')

        consumer = self.get_current_consumer()
        if consumer:
            self.redirect('/account/')

        self.response.out.write(self.show_form())

        logging.debug('Finished LoginHandler.get() method')

class LogoutHandler(authapp.SecureRequestHandler):
    def get(self):
        logging.debug('Begin LogoutHandler.get() method')

        self.delete_secure_cookie()

        template_file = os.path.join(os.path.dirname(__file__),
            'templates/account_logout.tpl')
        output = template.render(template_file, {})
        self.response.out.write(output)

        logging.debug('Finished LogoutHandler.get() method')

def main():
    application = webapp.WSGIApplication(
        [(r'/account/login/', LoginHandler),
        (r'/account/logout/', LogoutHandler),
        (r'/account/register/', RegisterHandler),
        (r'/account/', AccountHandler)], debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
