#!/usr/bin/env python2.5
# -*- coding: utf8 -*-
#
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2010 Flomosa, LLC
# All Rights Reserved.
#

__all__ = ['OAuthHandler', 'build_json']

import logging

from google.appengine.ext import webapp
from django.utils import simplejson
import oauth2 as oauth

from flomosa import exceptions, models


class OAuthHandler(webapp.RequestHandler):
    """Base handler for OAuth request authentication."""

    def __init__(self):
        super(webapp.RequestHandler, self).__init__()
        self._server = oauth.Server()
        self._server.add_signature_method(oauth.SignatureMethod_HMAC_SHA1())
        self._server.add_signature_method(oauth.SignatureMethod_PLAINTEXT())

    def handle_exception(self, exception, debug_mode):
        if debug_mode:
            super(OAuthHandler, self).handle_exception(exception, debug_mode)
        else:
            logging.error(exception)
            return build_json(self, exception)

    def get_oauth_request(self):
        """Return an OAuth Request object for the current request."""

        try:
            method = self.request.environ['REQUEST_METHOD']
        except Exception:
            method = 'GET'

        postdata = None
        if method in ('POST', 'PUT'):
            postdata = self.request.body

        return oauth.Request.from_request(method, self.request.uri,
            headers=self.request.headers, query_string=postdata)

    def get_client(self, request=None):
        """Return the client from the OAuth parameters."""

        if not isinstance(request, oauth.Request):
            request = self.get_oauth_request()
        if not request:
            raise exceptions.UnauthenticatedException(
                'OAuth "Authorization" header not found')

        client_key = request.get_parameter('oauth_consumer_key')
        if not client_key:
            raise exceptions.UnauthenticatedException(
                'Missing "oauth_consumer_key" parameter in OAuth ' \
                '"Authorization" header')

        client = models.Client.get(client_key)
        return client

    def is_valid(self):
        """Returns a Client object if this is a valid OAuth request."""

        request = self.get_oauth_request()
        client = self.get_client(request)
        self._server.verify_request(request, client, None)

        return client

    def is_client_allowed(self, process_key):
        """Checks that the client is valid and created the given process."""

        client = self.is_valid()
        process = models.Process.get(process_key, client)
        return process


def build_json(app, data, code=200, return_response=False):
    """Build a JSON error message response."""

    if isinstance(data, exceptions.HTTPException):
        code = data.status
        data = {'message': data.body}
    elif isinstance(data, Exception):
        data = {'message': unicode(data)}
    elif not isinstance(data, dict):
        data = {'message': data}
    if not str(code).startswith('2'):
        data['code'] = code

    try:
        json = simplejson.dumps(data)
    except Exception, ex:
        logging.critical('JSON ENCODING ERROR: %s.', ex)
        return None

    if return_response:
        return json

    app.error(code)
    app.response.headers['Content-Type'] = 'application/json'
    app.response.out.write(json)
    return None
