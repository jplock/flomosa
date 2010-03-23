"""
The MIT License

Copyright (c) 2010 Flomosa, LLC

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import os

from google.appengine.ext import webapp
import oauth2 as oauth

import models


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
