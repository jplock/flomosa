#
# Copyright 2010 Flomosa, LLC
#

import os

from google.appengine.ext import webapp
import oauth2 as oauth

from exceptions import UnauthenticatedException, UnauthorizedException
import models
import utils


class OAuthHandler(webapp.RequestHandler):

    def __init__(self):
        self._server = oauth.Server()
        self._server.add_signature_method(oauth.SignatureMethod_HMAC_SHA1())
        self._server.add_signature_method(oauth.SignatureMethod_PLAINTEXT())

    def handle_exception(self, exception, debug_mode):
        logging.error(exception)
        return utils.build_json(self, exception)

    def get_oauth_request(self):
        "Return an OAuth Request object for the current request."

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
        "Return the client from the OAuth parameters."

        if not isinstance(request, oauth.Request):
            request = self.get_oauth_request()
        if not request:
            raise UnauthenticatedException('OAuth "Authorization" header '
                'not found')

        client_key = request.get_parameter('oauth_consumer_key')
        if not client_key:
            raise UnauthenticatedException('Missing "oauth_consumer_key" ' \
                'parameter in OAuth "Authorization" header')

        client = models.Client.get(client_key)
        return client

    def is_valid(self):
        "Returns a Client object if this is a valid OAuth request."

        request = self.get_oauth_request()
        client = self.get_client(request)
        params = self._server.verify_request(request, client, None)

        return client

    def is_client_allowed(self, process_key):
        "Checks that the client is valid and created the given process."

        client = self.is_valid()
        process = models.Process.get(process_key)

        if process.client.id != client.id:
            raise UnauthorizedException('Client "%s" is not authorized to ' \
                'access Process "%s".' % (client.id, process.id))
        return process
