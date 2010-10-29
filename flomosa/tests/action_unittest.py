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


class ProcessActionTest(HandlerTestBase):
    """Test Case for actions"""

    handler_class = ProcessHandler

    def setUp(self):
        super(ProcessActionTest, self).setUp()
        self.client = create_client()

    def tearDown(self):
        super(ProcessActionTest, self).tearDown()
        self.client.delete()

    def test_api_create_action(self):
        team_key = 'test'
        team = models.Team(key_name=team_key, client=self.client,
                           name='Test Team', members=['test@flomosa.com'])
        team.put()

        process_key = 'test'
        step1 = {'kind': 'Step', 'key': 'step1', 'name': '1st Step',
                 'members': ['test@flomosa.com']}
        step2 = {'kind': 'Step', 'key': 'step2', 'name': '2nd Step',
                 'team': team_key}
        action1 = {'kind': 'Action', 'key': 'action1', 'name': 'Approved',
                   'incoming': ['step1'], 'outgoing': ['step2']}
        action2 = {'kind': 'Action', 'key': 'action2', 'name': 'Approved',
                   'incoming': ['step2']}

        data = {
            'key': process_key,
            'kind': 'Process',
            'name': 'Test Process',
            'steps': [step1, step2],
            'actions': [action1, action2]
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

        for action in resp_data['actions']:
            if action['key'] == 'action1':
                for key, value in action1.items():
                    self.assertEqual(action[key], value)
            elif action['key'] == 'action2':
                for key, value in action2.items():
                    self.assertEqual(action[key], value)
