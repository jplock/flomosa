#
# Copyright 2010 Flomosa, LLC
#

import logging
import os.path

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util

import authapp
import models
import settings
import utils


class AccountHandler(authapp.SecureRequestHandler):
    def show_form(self, template_vars=None):
        if not template_vars:
            template_vars = {'uri': self.request.uri}
        if 'uri' not in template_vars:
            template_vars['uri'] = self.request.uri

        template_file = os.path.join(os.path.dirname(__file__),
            'templates/account.tpl')
        return template.render(template_file, template_vars)

    def post(self):
        logging.debug('Begin AccountHandler.post() method')

        client = self.get_current_client()
        if not client:
            return self.redirect('/account/login/')

        template_vars = {
            'current_client': client,
            'messages': []
        }

        old_password = self.request.get('old_password')
        new_password = self.request.get('new_password')
        confirm_password = self.request.get('confirm_password')
        first_name = self.request.get('first_name')
        last_name = self.request.get('last_name')
        company = self.request.get('company')

        if old_password:
            if self.encrypt_string(old_password) != client.password:
                template_vars['messages'].append('Old password does not ' \
                    'match your existing password')
            elif not new_password:
                template_vars['messages'].append('Please provide a new ' \
                    'password')
            elif not confirm_password:
                template_vars['messages'].append('Please confirm your new ' \
                    'password')
            elif new_password != confirm_password:
                template_vars['messages'].append('New passwords do not match')

        if template_vars['messages']:
            for key, value in self.request.params.items():
                template_vars[key] = value
            template_vars['email_address'] = client.email_address
            template_vars['client_key'] = client.id
            template_vars['oauth_secret'] = client.oauth_secret

            self.response.out.write(self.show_form(template_vars))
        else:
            if new_password:
                client.password = self.encrypt_string(new_password)
            client.first_name = first_name
            client.last_name = last_name
            client.company = company

            try:
                client.put()
            except Exception, e:
                logging.error(e)
                template_vars['messages'] = [e]
                self.response.out.write(self.show_form(template_vars))

            if client.is_saved():
                return self.redirect('/')

        logging.debug('Finished AccountHandler.post() method')

    def get(self):
        logging.debug('Begin AccountHandler.get() method')

        template_vars = {'url': self.request.uri}

        client = self.get_current_client()
        if not client:
            return self.redirect('/account/login/')

        template_vars['current_client'] = client
        template_vars['email_address'] = client.email_address
        template_vars['first_name'] = client.first_name or ''
        template_vars['last_name'] = client.last_name or ''
        template_vars['company'] = client.company or ''
        template_vars['client_key'] = client.id
        template_vars['oauth_secret'] = client.oauth_secret

        self.response.out.write(self.show_form(template_vars))

        logging.debug('Finished AccountHandler.get() method')

class RegisterHandler(authapp.SecureRequestHandler):
    def show_form(self, template_vars=None):
        if not template_vars:
            template_vars = {'uri': self.request.uri}
        elif 'uri' not in template_vars:
            template_vars['uri'] = self.request.uri

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
        company = self.request.get('company')

        if not email_address:
            template_vars['messages'].append('Please provide an email address')
        if not password:
            template_vars['messages'].append('Please provide a password')
        elif not confirm_password:
            template_vars['messages'].append('Please confirm your password')
        elif password != confirm_password:
            template_vars['messages'].append('Passwords do not match')

        query = models.Client.all()
        query.filter('email_address =', email_address)
        if query.get():
            template_vars['messages'].append('Email address already exists')

        if template_vars['messages']:
            for key, value in self.request.params.items():
                template_vars[key] = value

            self.response.out.write(self.show_form(template_vars))
        else:
            client_key = utils.generate_key()
            client = models.Client(key_name=client_key,
                email_address=email_address,
                password=self.encrypt_string(password))
            client.first_name = first_name
            client.last_name = last_name
            client.company = company
            client.oauth_secret = utils.generate_key()

            try:
                client.put()
            except Exception, e:
                logging.error(e)
                template_vars['messages'] = [e]
                self.response.out.write(self.show_form(template_vars))

            if client.is_saved():
                self.set_secure_cookie(settings.COOKIE_NAME, client_key)
                next_url = self.request.get('next')
                if next_url:
                    return self.redirect(next_url)
                return self.redirect('/')

        logging.debug('Finished RegisterHandler.post() method')

    def get(self):
        logging.debug('Begin RegisterHandler.get() method')

        client = self.get_current_client()
        if client:
            return self.redirect('/account/')

        template_vars = {}
        next_url = self.request.get('next')
        if next_url:
            template_vars['next'] = next_url

        self.response.out.write(self.show_form(template_vars))

        logging.debug('Finished RegisterHandler.get() method')

class LoginHandler(authapp.SecureRequestHandler):
    def show_form(self, template_vars=None):
        if not template_vars:
            template_vars = {'uri': self.request.uri}
        elif 'uri' not in template_vars:
            template_vars['uri'] = self.request.uri

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
            query = models.Client.all()
            query.filter('email_address =', email_address)
            query.filter('password =', self.encrypt_string(password))
            client = query.get()
            if isinstance(client, models.Client):
                self.set_secure_cookie(settings.COOKIE_NAME, client.id)

                next_url = self.request.get('next')
                if next_url:
                    return self.redirect(next_url)
                return self.redirect('/account/')
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

        client = self.get_current_client()
        if client:
            return self.redirect('/account/')

        template_vars = {}
        next_url = self.request.get('next')
        if next_url:
            template_vars['next'] = next_url

        self.response.out.write(self.show_form(template_vars))

        logging.debug('Finished LoginHandler.get() method')

class LogoutHandler(authapp.SecureRequestHandler):
    def get(self):
        logging.debug('Begin LogoutHandler.get() method')

        client = self.get_current_client()
        if not client:
            return self.redirect('/account/login/')

        self.clear_cookie(settings.COOKIE_NAME)

        template_file = os.path.join(os.path.dirname(__file__),
            'templates/account_logout.tpl')
        output = template.render(template_file, {})
        self.response.out.write(output)

        logging.debug('Finished LogoutHandler.get() method')

class CloseHandler(authapp.SecureRequestHandler):
    def get(self):
        logging.debug('Begin CloseHandler.get() method')

        client = self.get_current_client()
        if not client:
            return self.redirect('/account/login/')

        try:
            client.delete()
        except Exception, e:
            logging.error(e)

        self.clear_cookie(settings.COOKIE_NAME)

        self.redirect('/')

        logging.debug('Finished CloseHandler.get() method')

def main():
    application = webapp.WSGIApplication(
        [(r'/account/login/', LoginHandler),
        (r'/account/logout/', LogoutHandler),
        (r'/account/register/', RegisterHandler),
        (r'/account/close/', CloseHandler),
        (r'/account/', AccountHandler)], debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
