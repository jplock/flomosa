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
from flomosa.test import HandlerTestBase, create_client, get_tasks
from flomosa.api.request import RequestHandler


class RequestTest(HandlerTestBase):
    """Test Case for requests"""

    handler_class = RequestHandler

    def setUp(self):
        super(RequestTest, self).setUp()
        self.client = create_client()

    def tearDown(self):
        super(RequestTest, self).tearDown()
        self.client.delete()

    def _create_hub(self, url):
        hub = models.Hub(url=url)
        hub.put()
        return hub

    def _create_team(self, key='test', members=None):
        if members is None:
            members = ['test@flomosa.com']
        team = models.Team(key_name=key, client=self.client, name='Test Team',
                           members=members)
        team.put()
        return team

    def _create_process(self, team, key='test'):
        process = models.Process(key_name=key, client=self.client,
                                 name='Test Process')
        process.put()

        step1 = process.add_step(name='1st Step', members=['test@flomosa.com'])
        step1.put()
        step2 = process.add_step(name='2nd Step', team_key=team.id)
        step2.put()
        step1_approve = process.add_action(name='1-Approve',
                                           incoming=[step1.id],
                                           outgoing=[step2.id])
        step1_approve.put()
        step1_reject = process.add_action(name='1-Reject', incoming=[step1.id])
        step1_reject.put()
        step2_approve = process.add_action(name='2-Approve',
                                           incoming=[step2.id])
        step2_approve.put()
        step2_reject = process.add_action(name='2-Reject', incoming=[step2.id])
        step2_reject.put()
        return process

    # POST Tests

    def test_api_post_request(self):
        hub = self._create_hub('http://pubsubhubbub.appspot.com')
        team = self._create_team()
        process = self._create_process(team)

        data = {'process': process.id, 'requestor': 'test@flomosa.com'}
        self.handle('post', params=data)

        self.assertEqual(self.response_code(), 201,
                         'Response code does not equal 201')
        resp_json = self.response_body()
        resp_data = simplejson.loads(resp_json)
        request_key = resp_data['key']
        self.assertNotEqual(request_key, '')

        first_step = process.get_start_step()

        stat_tasks = get_tasks('request-statistics', 1)
        for task in stat_tasks:
            params = task['params']
            self.assertEqual(params['request_key'], request_key)

        create_tasks = get_tasks('execution-creation', 1)
        for task in create_tasks:
            params = task['params']
            if params['team_key'] != 'None':
                self.assertEqual(params['team_key'], team.id)
                found_member = False
                for member in team.members:
                    if member == params['member']:
                        found_member = True
                        break
                self.assertTrue(found_member, 'Team member "%s" was ' \
                                'not found' % params['member'])
            self.assertEqual(params['request_key'], request_key)
            self.assertEqual(params['step_key'], first_step.id)

        hub_tasks = get_tasks('step-callback', 1)
        for task in hub_tasks:
            params = task['params']
            self.assertEqual(params['step_key'], first_step.id)
            self.assertEqual(params['callback_url'], hub.url)