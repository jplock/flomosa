#!/usr/bin/env python2.5
# -*- coding: utf8 -*-
#
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2010 Flomosa, LLC
# All Rights Reserved.
#

import datetime
from django.utils import simplejson

from flomosa import exceptions, models
from flomosa.test import HandlerTestBase, create_client
from flomosa.api.execution import ExecutionHandler


class ExecutionTest(HandlerTestBase):
    """Test Case for executions"""

    handler_class = ExecutionHandler

    def setUp(self):
        handler_class = ExecutionHandler
        super(ExecutionTest, self).setUp()
        self.client = create_client()

    def tearDown(self):
        super(ExecutionTest, self).tearDown()
        self.client.delete()

    def _create_execution(self, execution_key):
        process = models.Process(key_name='test', client=self.client,
                                 name='Test Process')
        process.put()
        step1 = process.add_step('1st Step', members=['test@flomosa.com'])
        step1.put()
        step2 = process.add_step('2nd Step', members=['test@flomosa.com'])
        step2.put()
        action = process.add_action('Approved', incoming=[step1],
                                    outgoing=[step2])
        action.put()

        request = models.Request(key_name='test', client=self.client,
                                 process=process, requestor='test@flomosa.com',
                                 first_name='Flo', last_name='Mo')
        request.put()

        data = {'key_name': execution_key, 'process': process, 'step': step1,
                'request': request, 'member': 'test@flomosa.com'}
        execution = models.Execution(**data)
        execution.put()
        return execution

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

    # Other Tests

    def test_get_url(self):
        execution_key = 'test'
        execution = self._create_execution(execution_key)
        url = 'https://flomosa.appspot.com/executions/%s.json' % execution_key
        self.assertEqual(execution.get_absolute_url(), url)

    def test_set_sent(self):
        execution_key = 'test'
        execution = self._create_execution(execution_key)
        self.assertEqual(execution.sent_date, None)
        sent_date = datetime.datetime.now()
        execution.set_sent(sent_date)
        self.assertEqual(execution.sent_date, sent_date)

    def test_set_completed(self):
        execution_key = 'test'
        execution = self._create_execution(execution_key)
        self.assertEqual(execution.end_date, None)
        self.assertEqual(execution.viewed_date, None)
        self.assertEqual(execution.action_delay, 0)
        self.assertEqual(execution.duration, 0)
        self.assertRaises(exceptions.InternalException,
                          execution.set_completed, None)

        process = execution.process
        step3 = process.add_step('3rd Step', members=['test@flomosa.com'])
        step3.put()
        bad_action = process.add_action('Declined', incoming=[step3])
        bad_action.put()
        self.assertRaises(exceptions.InternalException,
                          execution.set_completed, bad_action)

        start_date = datetime.datetime(2010, 4, 14, 5, 9, 10)
        viewed_date = datetime.datetime(2010, 5, 20, 14, 15, 16)
        end_date = datetime.datetime(2010, 8, 14, 8, 18, 20)

        execution.start_date = start_date
        execution.viewed_date = viewed_date
        execution.put()

        action = execution.step.actions[0]
        ret = execution.set_completed(action, end_date)
        self.assertEqual(execution.end_date, end_date)
        self.assertEqual(execution.action_delay, 7408984)
        self.assertEqual(execution.duration, 10552150)
        self.assertEqual(ret, execution.key())

        ret = execution.set_completed(action, end_date)
        self.assertEqual(ret, None)

    def test_set_viewed(self):
        execution_key = 'test'
        execution = self._create_execution(execution_key)
        self.assertEqual(execution.viewed_date, None)
        self.assertEqual(execution.email_delay, 0)

        sent_date = datetime.datetime(2010, 4, 14, 5, 15, 10)
        execution.sent_date = sent_date
        execution.put()

        viewed_date = datetime.datetime(2010, 5, 20, 14, 15, 16)
        ret = execution.set_viewed(viewed_date)
        self.assertEqual(execution.email_delay, 3142806)
        self.assertEqual(ret, execution.key())

        ret = execution.set_viewed(viewed_date)
        self.assertEqual(ret, None)