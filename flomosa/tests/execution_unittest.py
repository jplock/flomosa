#!/usr/bin/env python
# -*- coding: utf8 -*-
#
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2010 Flomosa, LLC
# All Rights Reserved.
#

from django.utils import simplejson

from flomosa import exceptions, models
from flomosa.test import HandlerTestBase, create_client
from flomosa.api.execution import ExecutionHandler


class ExecutionTest(HandlerTestBase):
    """Test Case for executions"""

    handler_class = ExecutionHandler

    def setUp(self):
        super(ExecutionTest, self).setUp()
        self.client = create_client()

    def tearDown(self):
        super(ExecutionTest, self).tearDown()
        self.client.delete()

    # GET Tests

    def test_api_get_execution(self):
        execution_key = 'test'
        data = {}

        #self.handle('get', url_value=execution_key, wrap_oauth=True)
        #self.assertEqual(self.response_code(), 200,
        #                 'Response code does not equal 200')
        #resp_json = self.response_body()
        #resp_data = simplejson.loads(resp_json)
        #for key, value in data.items():
        #    self.assertEqual(resp_data[key], value,
        #                     'Response "%s" does not equal "%s"' % (key,
        #                                                            value))

    def test_api_get_execution_bad_key(self):
        self.assertRaises(exceptions.NotFoundException, self.handle, 'get',
                          url_value='test', wrap_oauth=True)

    def test_api_get_missing_oauth(self):
        self.assertRaises(exceptions.UnauthenticatedException,
                          self.handle, 'get', url_value='test')