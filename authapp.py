#
# Copyright 2010 Flomosa, LLC
#

import base64
import calendar
import Cookie
import datetime
import email.utils
import hmac
import hashlib
import logging
import re
import time

from google.appengine.ext import webapp

import models
import settings


class SecureRequestHandler(webapp.RequestHandler):

    def get_current_client(self, default=None):
        """Return the currently logged in Client, or None."""
        client_key = self.get_secure_cookie(settings.COOKIE_NAME)
        if client_key:
            client = models.Client.get(client_key)
            if client and isinstance(client, models.Client):
                return client
        return default

    def _cookie_signature(self, *parts):
        hash = hmac.new(settings.COOKIE_SECRET, digestmod=hashlib.sha1)
        for part in parts:
            hash.update(part)
        return hash.hexdigest()

    def get_cookie(self, name, default=None):
        """Gets the value of the cookie with the given name, else default."""
        if name in self.request.cookies:
            return self.request.cookies[name]
        return default

    def set_cookie(self, name, value, domain=None, expires=None, path='/',
            expires_days=None):
        """Sets the given cookie name/value with the given options."""

        name = _utf8(name)
        value = _utf8(value)
        if re.search(r'[\x00-\x20]', name + value):
            # Don't let us accidentally inject bad stuff
            raise ValueError('Invalid cookie %r: %r' % (name, value))

        new_cookie = Cookie.SimpleCookie()
        new_cookie[name] = value
        if domain:
            new_cookie[name]['domain'] = domain
        if expires_days is not None and not expires:
            expires = datetime.datetime.utcnow() + datetime.timedelta(
                days=expires_days)
        if expires:
            timestamp = calendar.timegm(expires.utctimetuple())
            new_cookie[name]['expires'] = email.utils.formatdate(timestamp,
                localtime=False, usegmt=True)
        if path:
            new_cookie[name]['path'] = path

        re_find_header = re.compile('^Set-Cookie: ')
        new_header = str(re_find_header.sub('', new_cookie.output(), count=1))

        self.response.headers.add_header('Set-Cookie', new_header)

    def clear_cookie(self, name, path='/', domain=None):
        """Deletes the cookie with the given name."""
        expires = datetime.datetime.utcnow() - datetime.timedelta(days=365)
        return self.set_cookie(name, value='', path=path, expires=expires,
            domain=domain)

    def set_secure_cookie(self, name, value, expires_days=30, **kwargs):
        """Signs and timestamps a cookie so it cannot be forged.

        You must specify the 'COOKIE_SECRET' setting in your settings file
        to use this method. It should be a long, random sequence of bytes
        to be used as the HMAC secret for the signature.

        To read a cookie set with this method, use get_secure_cookie().
        """

        timestamp = str(int(time.time()))
        value = base64.b64encode(value)
        signature = self._cookie_signature(name, value, timestamp)
        value = '|'.join([value, timestamp, signature])
        return self.set_cookie(name, value, expires_days=expires_days, **kwargs)

    def get_secure_cookie(self, name, value=None):
        """Returns the given signed cookie if it validates, or None."""

        if value is None:
            value = self.get_cookie(name)
        if not value:
            return None

        parts = value.split('|')
        if len(parts) != 3:
            return None

        signature = self._cookie_signature(name, parts[0], parts[1])
        if not _time_independent_equals(parts[2], signature):
            logging.warning('Invalid cookie signature %r', value)
            return None

        timestamp = int(parts[1])
        if timestamp < time.time() - 31 * 86400:
            logging.warning('Expired cookie %r', value)
            return None

        try:
            return base64.b64decode(parts[0])
        except:
            return None

    def encrypt_string(self, password):
        """Encrypt a string using the MD5 hash."""
        return hashlib.md5(password).hexdigest()


def _utf8(s):
    if isinstance(s, unicode):
        return s.encode('utf-8')
    assert isinstance(s, str)
    return s

def _time_independent_equals(a, b):
    if len(a) != len(b):
        return False
    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)
    return result == 0