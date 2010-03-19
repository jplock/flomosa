#
# Copyright 2010 Flomosa, LLC
#

import os

from google.appengine.ext import webapp
import oauth2 as oauth

import models


class OAuthHandler(webapp.RequestHandler):

    def __init__(self):
        self._server = oauth.Server()
        self._server.add_signature_method(oauth.SignatureMethod_HMAC_SHA1())

    def get_oauth_request(self):
        """Return an OAuth Request object for the current request."""

        try:
            method = os.environ['REQUEST_METHOD']
        except:
            method = 'GET'

        return oauth.Request.from_request(method, self.request.uri,
            self.request.headers)

    def get_client(self, request=None):
        """Return the client from the OAuth parameters."""

        if not isinstance(request, oauth.Request):
            request = self.get_oauth_request()
        client_key = request.get_parameter('oauth_consumer_key')
        if not client_key:
            raise Exception('Missing "oauth_consumer_key" parameter in ' \
                'OAuth "Authorization" header')

        client = models.Client.get(client_key)
        if not client:
            raise Exception('Client "%s" not found.' % client_key)

        return client

    def is_valid(self):
        """Returns a Client object if this is a valid OAuth request."""

        try:
            request = self.get_oauth_request()
            client = self.get_client(request)
            params = self._server.verify_request(request, client, None)
        except Exception, e:
            raise e

        return client
