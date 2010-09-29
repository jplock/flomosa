#!/usr/bin/env python
# -*- coding: utf8 -*-
#
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2010 Flomosa, LLC
# All Rights Reserved.
#

import base64
import cgi
import logging
import os
import StringIO
import sys
import tempfile
import unittest
import urllib

import oauth2 as oauth


TEST_APP_ID = 'flomosa'
TEST_VERSION_ID = '2'

# test@flomosa.com
TEST_KEY = '4ef3e685-37c1-43f9-ae03-0a21523051c6'
TEST_SECRET = '1913b245-18ae-4caa-a491-cedd2e471a50'


def create_client(key=TEST_KEY, secret=TEST_SECRET):
    """Create the test client in the datastore.

    Args:
        key: client key to create
    """
    from flomosa import models
    client = models.Client(key_name=key, email_address='test@flomosa.com',
                           password='test', first_name='Test',
                           last_name='Test', company='Flomosa',
                           oauth_secret=secret)
    client.put()
    return client

def delete_client(key=TEST_KEY):
    """Delete the test client from the datastore.

    Args:
        key: client key to delete
    """
    from flomosa import models
    client = models.Client.get_by_key_name(key)
    client.delete()

def fix_path():
    """Finds the google_appengine directory and fixes Python imports to use it.

    """
    all_paths = os.environ.get('PATH').split(os.pathsep)
    for path_dir in all_paths:
        dev_appserver_path = os.path.join(path_dir, 'dev_appserver.py')
        if os.path.exists(dev_appserver_path):
            google_appengine = os.path.dirname(os.path.realpath(
                dev_appserver_path))
            sys.path.append(google_appengine)
            # Use the next import will fix up sys.path even further to bring in
            # any dependent lib directories that the SDK needs.
            dev_appserver = __import__('dev_appserver')
            sys.path.extend(dev_appserver.EXTRA_PATHS)
            return

def setup_for_testing(require_indexes=True):
    """Sets up the stubs for testing.

    Args:
        require_indexes: True if indexes should be required for all indexes.
    """
    from google.appengine.api import apiproxy_stub_map
    from google.appengine.api import memcache
    from google.appengine.tools import dev_appserver
    from google.appengine.tools import dev_appserver_index
    before_level = logging.getLogger().getEffectiveLevel()
    try:
        logging.getLogger().setLevel(100)
        root_path = os.path.realpath(os.path.dirname(__file__))
        dev_appserver.SetupStubs(
            TEST_APP_ID,
            root_path=root_path,
            login_url='',
            datastore_path=None,
            blobstore_path=tempfile.mkdtemp(suffix='blobstore_stub'),
            require_indexes=require_indexes,
            clear_datastore=False)
        dev_appserver_index.SetupIndexes(TEST_APP_ID, root_path)
        # Actually need to flush, even though we've reallocated. Maybe because
        # the memcache stub's cache is at the module level, not the API stub?
        memcache.flush_all()
    finally:
        logging.getLogger().setLevel(before_level)

def create_test_request(method, body=None, params=None, wrap_oauth=False):
    """Creates a webapp.Request object for use in testing.

    Args:
        method: Method to use for the test.
        body: The body to use for the request; implies that params is empty.
        params: Dictionary to use in the post-body or query string of
        the request.
        wrap_oauth: Whether to wrap the request in with OAuth headers

    Returns:
        A new webapp.Request object for testing.
    """
    assert not(body and params), 'Must specify body or params, not both'
    from google.appengine.ext import webapp

    if params is None:
        params = {}
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
        'REQUEST_METHOD': method.upper(),
        'SERVER_NAME': 'flomosa.appspot.com',
        'SERVER_PORT': '',
        'SERVER_SOFTWARE': 'Development/1.0',
        'APPLICATION_ID': TEST_APP_ID,
        'CURRENT_VERSION_ID': TEST_VERSION_ID,
        'QUERY_STRING': '',
        'AUTH_DOMAIN': 'flomosa.com',
        'USER_EMAIL': '',
        'wsgi.input': body,
        'wsgi.url_scheme': 'http'
    })
    if method.lower() == 'get':
        environ['QUERY_STRING'] = encoded_params
    else:
        environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'
        environ['CONTENT_LENGTH'] = str(len(body.getvalue()))

    req = webapp.Request(environ)
    if wrap_oauth:
        consumer = oauth.Consumer(TEST_KEY, TEST_SECRET)
        signature = oauth.SignatureMethod_HMAC_SHA1()
        endpoint = 'http://flomosa.appspot.com'

        oauth_request = oauth.Request.from_consumer_and_token(consumer,
            http_method=method, http_url=endpoint, parameters=params)

        oauth_request.sign_request(signature, consumer, None)
        headers = oauth_request.to_header('http://flomosa.appspot.com')
        req.headers.update(headers)
    return req


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

    def handle(self, method, body=None, url_value=None, headers=None,
               params=None, wrap_oauth=False):
        """Runs a test of a webapp.RequestHandler.

        Args:
            method: The method to invoke for this test.
            body: POST/PUT body data to use for the request
            url_value: value to pass in URL
            headers: Request headers to set
            params: Passed to create_test_request()
            wrap_oauth: Whether to wrap the request with OAuth headers
        """
        from google.appengine.ext import webapp
        self.resp = webapp.Response()
        self.req = create_test_request(method, body=body, params=params,
                                       wrap_oauth=wrap_oauth)
        handler = self.handler_class()
        handler.initialize(self.req, self.resp)
        handler_method = getattr(handler, method.lower())
        if url_value:
            handler_method(url_value)
        else:
            handler_method()
        logging.info('%r returned status %d: %s', self.handler_class,
                     self.response_code(), self.response_body())

    def response_body(self):
        """Returns the response body after the request is handled."""
        return self.resp.out.getvalue()

    def response_code(self):
        """Returns the response code after the request is handled."""
        return self.resp._Response__status[0]

    def response_headers(self):
        """Returns the response headers after the request is handled."""
        return self.resp.headers


def get_tasks(queue_name, expected_count=None):
    """Retrieves Tasks from the supplied named queue.

    Args:
        queue_name: The queue to access.
        expected_count: If not None, the number of tasks expected to be in the
            queue. This function will raise an AssertionError exception if
            there are more or fewer tasks.

    Returns:
        List of dictionaries corresponding to each task, with the keys: 'name',
        'url', 'method', 'body', 'headers', 'params'. The 'params' value will
        only be present if the body's Content-Type header is
        'application/x-www-form-urlencoded'.
    """

    from google.appengine.api import apiproxy_stub_map
    stub = apiproxy_stub_map.apiproxy.GetStub('taskqueue')

    tasks = stub.GetTasks(queue_name)

    if expected_count is not None:
        assert len(tasks) == expected_count, 'found %s == %s' % (len(tasks),
                                                                 expected_count)
    for task in tasks:
        task['body'] = base64.b64decode(task['body'])
        # Convert headers list into a dictionary-
        task['headers'] = dict(task['headers'])
        if ('application/x-www-form-urlencoded' in
            task['headers'].get('content-type', '')):
            task['params'] = dict(cgi.parse_qsl(task['body'], True))
    return tasks