#!/usr/bin/env python2.5
# -*- coding: utf8 -*-
#
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2010 Flomosa, LLC
# All Rights Reserved.
#

__all__ = ['SecureRequestHandler']

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

from flomosa import models, settings


class SecureRequestHandler(webapp.RequestHandler):
    """RequestHandler which supports setting cookies which have a built-in
    secure signature.

    Portions of this code is from:
    http://github.com/facebook/tornado/blob/master/tornado/web.py
    """

    def get_current_client(self, default=None):
        """Return the currently logged in Client."""
        client_key = self.get_secure_cookie(settings.COOKIE_NAME)
        try:
            return models.Client.get(client_key)
        except Exception:
            return default

    def _cookie_signature(self, *parts):
        hash = hmac.new(settings.COOKIE_SECRET, digestmod=hashlib.sha1)
        for part in parts:
            hash.update(part)
        return hash.hexdigest()

    def get_cookie(self, name, default=None):
        """Gets the value of the cookie with the given name, else default."""
        if name in self.request.cookies:
            return self.request.cookies[name].value
        return default

    def set_cookie(self, name, value, domain=None, expires=None, path='/',
            expires_days=None):
        """Sets the given cookie name/value with the given options."""

        name = _utf8(name)
        value = _utf8(value)
        if re.search(r'[\x00-\x20]', name + value):
            # Don't let us accidentally inject bad stuff
            raise ValueError('Invalid cookie %r: %r' % (name, value))

        new_cookie = Cookie.BaseCookie()
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

        To read a cookie set with this method, use get_secure_cookie().
        """
        self.set_cookie(name, self.create_signed_value(name, value),
                        expires_days=expires_days, **kwargs)

    def create_signed_value(self, name, value):
        """Signs and timestamps a string so it cannot be forged.

        Normally used via set_secure_cookie, but provided as a separate
        method for non-cookie uses.  To decode a value not stored
        as a cookie use the optional value argument to get_secure_cookie.
        """
        timestamp = str(int(time.time()))
        value = base64.b64encode(value)
        signature = self._cookie_signature(name, value, timestamp)
        value = "|".join([value, timestamp, signature])
        return value

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
        if timestamp > time.time() + 31 * 86400:
            # _cookie_signature does not hash a delimiter between the
            # parts of the cookie, so an attacker could transfer trailing
            # digits from the payload to the timestamp without altering the
            # signature.  For backwards compatibility, sanity-check timestamp
            # here instead of modifying _cookie_signature.
            logging.warning('Cookie timestamp in future; possible ' \
                            'tampering %r', value)
            return None
        if parts[1].startswith('0'):
            logging.warning('Tampered cookie %r', value)

        try:
            return base64.b64decode(parts[0])
        except Exception:
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