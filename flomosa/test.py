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


TEST_APP_ID = 'flomosa'
TEST_VERSION_ID = '2'

# Assign the application ID up front here so we can create db.Key instances
# before doing any other test setup.
os.environ['APPLICATION_ID'] = TEST_APP_ID
os.environ['CURRENT_VERSION_ID'] = TEST_VERSION_ID


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
    from flomosa.tests import urlfetch_test_stub
    before_level = logging.getLogger().getEffectiveLevel()
    try:
        logging.getLogger().setLevel(logging.DEBUG)
        root_path = os.path.realpath(os.path.dirname(__file__))
        dev_appserver.SetupStubs(
            TEST_APP_ID,
            root_path=root_path,
            login_url='',
            datastore_path=tempfile.mktemp(suffix='datastore_stub'),
            history_path=tempfile.mktemp(suffix='datastore_history'),
            blobstore_path=tempfile.mktemp(suffix='blobstore_stub'),
            require_indexes=require_indexes,
            clear_datastore=False)
        dev_appserver_index.SetupIndexes(TEST_APP_ID, root_path)
        apiproxy_stub_map.apiproxy._APIProxyStubMap__stub_map['urlfetch'] = \
            urlfetch_test_stub.instance
        # Actually need to flush, even though we've reallocated. Maybe because
        # the memcache stub's cache is at the module level, not the API stub?
        memcache.flush_all()
    finally:
        logging.getLogger().setLevel(before_level)

def create_test_request(method, body, params=None):
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

    encoded_params = ''
    if body:
        body = StringIO.StringIO(body)
    else:
        if params:
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

    def handle(self, method, url_value=None, headers=None, params=None):
        """Runs a test of a webapp.RequestHandler.

        Args:
            method: The method to invoke for this test.
            url_value: value to pass in URL
            headers: Request headers to set
            params: Passed to create_test_request()
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
            self.req = create_test_request(method, None, params)
            handler = self.handler_class()
            handler.initialize(self.req, self.resp)
            handler_method = getattr(handler, method.lower())
            if url_value:
                handler_method(url_value)
            else:
                handler_method()
            logging.info('%r returned status %d: %s', self.handler_class,
                         self.response_code(), self.response_body())
        finally:
            del os.environ['SERVER_SOFTWARE']
            del os.environ['AUTH_DOMAIN']
            del os.environ['USER_EMAIL']

    def handle_body(self, method, body, url_value=None):
        """Runs a test of a webapp.RequestHandler with a POST body.

        Args:
            method: The HTTP method to invoke for this test.
            body: The body payload bytes.
            url_value: value to pass in URL
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
            getattr(handler, method.lower())(url_value)
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
        # Convert headers list into a dictionary-- we don't care about repeats
        task['headers'] = dict(task['headers'])
        if ('application/x-www-form-urlencoded' in
            task['headers'].get('content-type', '')):
            task['params'] = dict(cgi.parse_qsl(task['body'], True))
    return tasks