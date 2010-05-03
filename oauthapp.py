#
# Copyright 2010 Flomosa, LLC
#

import os

from google.appengine.ext import webapp
import oauth2 as oauth

import models
import utils


class OAuthHandler(webapp.RequestHandler):

    def __init__(self):
        self._server = oauth.Server()
        self._server.add_signature_method(oauth.SignatureMethod_HMAC_SHA1())
        self._server.add_signature_method(oauth.SignatureMethod_PLAINTEXT())

    def get_oauth_request(self):
        """Return an OAuth Request object for the current request."""

        try:
            method = os.environ['REQUEST_METHOD']
        except:
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
            raise Exception('OAuth "Authorization" header not found')

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

    def is_client_allowed(self, process_key):
        """Checks that the client is valid and created the given process.

        Parameters:
          process_key - process to lookup and validate against client
        """

        try:
            client = self.is_valid()
        except Exception, e:
            raise utils.FlomosaException(401, e)

        process = models.Process.get(process_key)
        if not process:
            error_msg = 'Process key "%s" does not exist.' % process_key
            raise utils.FlomosaException(404, error_msg)

        if process.client.id != client.id:
            error_msg = 'Permission denied.'
            raise utils.FlomosaException(401, 'Permission denied.')
        return process
