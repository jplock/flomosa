#
# Copyright 2010 Flomosa, LLC
#

import os
import re
import Cookie
import base64
import logging
import hashlib
import time

from google.appengine.ext import webapp

import models


class SecureRequestHandler(webapp.RequestHandler):
    _COOKIE_NAME = 'flomosa'
    _COOKIE_SECRET = 'F10m0sA'

    def get_current_consumer(self):
        """Get the currently logged in consumer."""
        consumer_key = self.get_secure_cookie()
        if consumer_key:
            consumer = models.Consumer.get(consumer_key)
            if isinstance(consumer, models.Consumer):
                return consumer
        return None

    def set_secure_cookie(self, data, name=_COOKIE_NAME, expires=None):
        """Sets a secure cookie in the response header."""

        timestamp = str(time.time())
        signature = hashlib.sha1(self._COOKIE_SECRET+timestamp+data).hexdigest()
        signed_data = base64.b64encode('%s|%s|%s' % (signature, timestamp,
            data))

        cookie = Cookie.SimpleCookie()
        cookie[name] = str(signed_data)
        cookie[name]['path'] = '/'
        if os.environ.get('SERVER_SOFTWARE').startswith('Development'):
            cookie[name]['domain'] = '127.0.0.1'
        else:
            cookie[name]['domain'] = os.environ.get('HTTP_HOST')
        if expires:
            cookie[name]['expires'] = expires
        cookie[name]['httponly'] = True

        re_find_header = re.compile('^Set-Cookie: ')
        new_header = str(re_find_header.sub('', cookie.output(), count=1))

        self.response.headers.add_header('Set-Cookie', new_header)
        return None

    def get_secure_cookie(self, name=_COOKIE_NAME):
        """Gets a secure cookie from the request header."""

        try:
            signed_data = self.request.cookies[name]
        except KeyError:
            return None

        decoded_data = str(base64.b64decode(signed_data))
        signature, timestamp, data = decoded_data.split('|', 3)
        computed_sig = hashlib.sha1(self._COOKIE_SECRET+timestamp+data)
        if signature != computed_sig.hexdigest():
            return None
        return data

    def delete_secure_cookie(self, name=_COOKIE_NAME):
        """Deletes the secure cookie by setting it to no value."""
        return self.set_secure_cookie('')

    def encrypt_string(self, password):
        """Encrypt a string using the MD5 hash."""
        return hashlib.md5(password).hexdigest()
