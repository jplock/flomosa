#!/usr/bin/env python2.5
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
from flomosa.api.process import ProcessHandler
from flomosa.api.step import StepAtomHandler


class ProcessStepTest(HandlerTestBase):
    """Test Case for steps"""

    handler_class = ProcessHandler

    def setUp(self):
        super(ProcessStepTest, self).setUp()
        self.client = create_client()

    def tearDown(self):
        super(ProcessStepTest, self).tearDown()
        self.client.delete()

    def test_api_create_step(self):
        team_key = 'test'
        team = models.Team(key_name=team_key, client=self.client,
                           name='Test Team', members=['test@flomosa.com'])
        team.put()

        process_key = 'test'
        step1 = {'kind': 'Step', 'key': 'step1', 'name': '1st Step',
                 'members': ['test@flomosa.com']}
        step2 = {'kind': 'Step', 'key': 'step2', 'name': '2nd Step',
                 'team': team_key}

        data = {
            'key': process_key,
            'kind': 'Process',
            'name': 'Test Process',
            'steps': [step1, step2]
        }
        body = simplejson.dumps(data)
        self.handle('put', body=body, url_value=process_key, wrap_oauth=True)
        self.assertEqual(self.response_code(), 201,
                         'Response code does not equal 201')
        resp_json = self.response_body()
        resp_data = simplejson.loads(resp_json)
        self.assertEqual(resp_data['key'], process_key)

        self.handle('get', url_value=process_key, wrap_oauth=True)
        self.assertEqual(self.response_code(), 200,
                         'Response code does not equal 200')
        resp_json = self.response_body()
        resp_data = simplejson.loads(resp_json)

        for step in resp_data['steps']:
            if step['key'] == 'step1':
                for key, value in step1.items():
                    self.assertEqual(step[key], value)
            elif step['key'] == 'step2':
                for key, value in step2.items():
                    self.assertEqual(step[key], value)

    def test_api_create_step_no_members(self):
        process_key = 'test'
        step1 = {'kind': 'Step', 'key': 'step1', 'name': '1st Step'}

        data = {
            'key': process_key,
            'kind': 'Process',
            'name': 'Test Process',
            'steps': [step1]
        }
        body = simplejson.dumps(data)
        self.assertRaises(exceptions.MissingException, self.handle, 'put',
                          body=body, url_value=process_key, wrap_oauth=True)

    def test_api_create_step_bad_team(self):
        process_key = 'test'
        step1 = {'kind': 'Step', 'key': 'step1', 'name': '1st Step',
                 'team': 'test'}

        data = {
            'key': process_key,
            'kind': 'Process',
            'name': 'Test Process',
            'steps': [step1]
        }
        body = simplejson.dumps(data)
        self.assertRaises(exceptions.NotFoundException, self.handle, 'put',
                          body=body, url_value=process_key, wrap_oauth=True)


class StepTest(HandlerTestBase):
    """Test Case for steps"""

    handler_class = StepAtomHandler

    def setUp(self):
        super(StepTest, self).setUp()
        self.client = create_client()

    def tearDown(self):
        super(StepTest, self).tearDown()
        self.client.delete()

    def test_api_get_step(self):
        process_data = {'key_name': 'test', 'client': self.client,
                        'name': 'Test Process'}
        process = models.Process(**process_data)

        step_key = 'step1'
        step_data = {'step_key': step_key, 'name': '1st Step',
                     'members': ['test@flomosa.com']}
        process.add_step(**step_data)

        self.handle('get', url_value=step_key)
        self.assertEqual(self.response_code(), 200,
                         'Response code does not equal 200')

        headers = {'Cache-Control': 'no-cache',
                   'Content-Type': 'application/atom+xml'}

        resp_headers = self.response_headers()
        for key, value in resp_headers.items():
            self.assertEqual(value, headers[key])

    def test_api_get_step_bad_key(self):
        self.assertRaises(exceptions.NotFoundException, self.handle, 'get',
                          url_value='test')

    def test_step_is_valid(self):
        team = models.Team(key_name='test', client=self.client,
                           name='Test Team')
        process = models.Process(key_name='test', client=self.client,
                                 name='Test Process')
        step = process.add_step(step_key='test', name='1st Step',
                                members=['test@flomosa.com'])

        self.assertTrue(step.is_valid())
        step.members = []
        step.team = team
        self.assertFalse(step.is_valid())
        team.members = ['test@flomosa.com']
        self.assertTrue(step.is_valid())
        step.team = None
        step.members = []
        self.assertFalse(step.is_valid())
        step.team = None
        step.members = ['test@flomosa.com']
        self.assertTrue(step.is_valid())

    def test_step_url(self):
        process = models.Process(key_name='test', client=self.client,
                                 name='Test Process')
        step = process.add_step(step_key='test', name='1st Step',
                                members=['test@flomosa.com'])
        self.assertEqual(step.get_absolute_url(),
                         'https://flomosa.appspot.com/steps/test.atom')
