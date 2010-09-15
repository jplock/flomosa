# -*- coding: utf8 -*-
#
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2010 Flomosa, LLC
# All Rights Reserved.
#

import logging
import os
import StringIO
import unittest
import urllib


def create_test_request(method, body, *params):
    """Creates a webapp.Request object for use in testing.

    Args:
        method: Method to use for the test.
        body: The body to use for the request; implies that *params is empty.
        *params: List of (key, value) tuples to use in the post-body or query
        string of the request.

    Returns:
        A new webapp.Request object for testing.
    """
    assert not(body and params), 'Must specify body or params, not both'
    from google.appengine.ext import webapp

    if body:
        body = StringIO.StringIO(body)
        encoded_params = ''
    else:
        encoded_params = urllib.urlencode(params)
        body = StringIO.StringIO()
        body.write(encoded_params)
        body.seek(0)

    environ = os.environ.copy()
    environ.update({
        'QUERY_STRING': '',
        'wsgi.input': body,
    })
    if method.lower() == 'get':
        environ['REQUEST_METHOD'] = method.upper()
        environ['QUERY_STRING'] = encoded_params
    else:
        environ['REQUEST_METHOD'] = method.upper()
        environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'
        environ['CONTENT_LENGTH'] = str(len(body.getvalue()))
    return webapp.Request(environ)


class HandlerTestBase(unittest.TestCase):
    """Base-class for webapp.RequestHandler tests."""

    # Set to the class being tested.
    handler_class = None

    def setUp(self):
        """Sets up the test harness."""
        setup_for_testing()

    def tearDown(self):
        """Tears down the test harness."""
        pass

    def handle(self, method, *params):
        """Runs a test of a webapp.RequestHandler.

        Args:
            method: The method to invoke for this test.
            *params: Passed to testutil.create_test_request
        """
        from google.appengine.ext import webapp
        before_software = os.environ.get('SERVER_SOFTWARE')
        before_auth_domain = os.environ.get('AUTH_DOMAIN')
        before_email = os.environ.get('USER_EMAIL')

        os.environ['wsgi.url_scheme'] = 'http'
        os.environ['SERVER_NAME'] = 'flomosa.com'
        os.environ['SERVER_PORT'] = ''
        try:
            if not before_software:
                os.environ['SERVER_SOFTWARE'] = 'Development/1.0'
            if not before_auth_domain:
                os.environ['AUTH_DOMAIN'] = 'flomosa.com'
            if not before_email:
                os.environ['USER_EMAIL'] = ''
            self.resp = webapp.Response()
            self.req = create_test_request(method, None, *params)
            handler = self.handler_class()
            handler.initialize(self.req, self.resp)
            getattr(handler, method.lower())()
            logging.info('%r returned status %d: %s', self.handler_class,
                         self.response_code(), self.response_body())
        finally:
            del os.environ['SERVER_SOFTWARE']
            del os.environ['AUTH_DOMAIN']
            del os.environ['USER_EMAIL']

    def handle_body(self, method, body):
        """Runs a test of a webapp.RequestHandler with a POST body.

        Args:
            method: The HTTP method to invoke for this test.
            body: The body payload bytes.
        """
        from google.appengine.ext import webapp
        before_software = os.environ.get('SERVER_SOFTWARE')
        before_auth_domain = os.environ.get('AUTH_DOMAIN')
        before_email = os.environ.get('USER_EMAIL')

        os.environ['wsgi.url_scheme'] = 'http'
        os.environ['SERVER_NAME'] = 'flomosa.com'
        os.environ['SERVER_PORT'] = ''
        try:
            if not before_software:
                os.environ['SERVER_SOFTWARE'] = 'Development/1.0'
            if not before_auth_domain:
                os.environ['AUTH_DOMAIN'] = 'flomosa.com'
            if not before_email:
                os.environ['USER_EMAIL'] = ''
            self.resp = webapp.Response()
            self.req = create_test_request(method, body)
            handler = self.handler_class()
            handler.initialize(self.req, self.resp)
            getattr(handler, method.lower())()
            logging.info('%r returned status %d: %s', self.handler_class,
                         self.response_code(), self.response_body())
        finally:
            del os.environ['SERVER_SOFTWARE']
            del os.environ['AUTH_DOMAIN']
            del os.environ['USER_EMAIL']

    def response_body(self):
        """Returns the response body after the request is handled."""
        return self.resp.out.getvalue()

    def response_code(self):
        """Returns the response code after the request is handled."""
        return self.resp._Response__status[0]

    def response_headers(self):
        """Returns the response headers after the request is handled."""
        return self.resp.headers