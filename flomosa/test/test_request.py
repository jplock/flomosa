#!/usr/bin/env python2.5
# -*- coding: utf8 -*-
#
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2010 Flomosa, LLC
# All Rights Reserved.
#

from datetime import datetime

from django.utils import simplejson

from flomosa import exceptions, models
from flomosa.test import HandlerTestBase, create_client, get_tasks
from flomosa.api.request import RequestHandler


class RequestTest(HandlerTestBase):
    """Test Case for requests"""

    handler_class = RequestHandler

    def setUp(self):
        handler_class = RequestHandler
        super(RequestTest, self).setUp()
        self.client = create_client()

    def tearDown(self):
        super(RequestTest, self).tearDown()
        self.client.delete()

    def _create_team(self, key='test', members=None):
        if members is None:
            members = ['test@flomosa.com']
        team = models.Team(key_name=key, client=self.client, name='Test Team',
                           members=members)
        team.put()
        return team

    def _create_process(self, team=None, key='test'):
        process = models.Process(key_name=key, client=self.client,
                                 name='Test Process')
        process.put()

        step1 = process.add_step(name='1st Step', members=['test@flomosa.com'])
        step1.put()
        if team is not None:
            team_key = team.id
        else:
            team_key = None
        step2 = process.add_step(name='2nd Step', team_key=team_key,
                                 members=['test@flomosa.com'])
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

    def _create_request(self, process, data=None):
        if data is None:
            data = {'process': process.id, 'requestor': 'test@flomosa.com'}
        self.handler_class = RequestHandler
        self.handle('post', params=data)
        self.assertEqual(self.response_code(), 201,
                         'Response code does not equal 201')
        resp_json = self.response_body()
        resp_data = simplejson.loads(resp_json)
        self.assertNotEqual(resp_data['key'], '')
        return resp_data['key']

    # POST Tests

    def test_api_post_request(self):
        hub = _create_hub('http://pubsubhubbub.appspot.com')
        team = self._create_team()
        process = self._create_process(team)
        request_key = self._create_request(process)
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

    # GET Tests

    def test_api_get_request(self):
        request_key = 'test'
        process = self._create_process()
        data = {'process': process, 'requestor': 'test@flomosa.com',
                'first_name': 'Flo', 'last_name': 'Mo'}
        request = models.Request(key_name=request_key, client=self.client,
                                 **data)
        request.put()

        self.handle('get', url_value=request_key, wrap_oauth=True)
        self.assertEqual(self.response_code(), 200,
                         'Response code does not equal 200')
        resp_json = self.response_body()
        resp_data = simplejson.loads(resp_json)

        for key, value in data.items():
            if key == 'client':
                continue
            elif key == 'process':
                value = process.id
            self.assertEqual(resp_data[key], value)

    def test_api_get_request_bad_key(self):
        self.assertRaises(exceptions.NotFoundException, self.handle, 'get',
                          url_value='test', wrap_oauth=True)

    def test_api_get_missing_oauth(self):
        self.assertRaises(exceptions.UnauthenticatedException,
                          self.handle, 'get', url_value='test')

    # DELETE Tests

    def test_api_delete_request(self):
        request_key = 'test'
        process = self._create_process()
        data = {'key_name': request_key, 'client': self.client,
                'process': process, 'requestor': 'test@flomosa.com',
                'first_name': 'Flo', 'last_name': 'Mo'}
        request = models.Request(**data)
        request.put()

        self.handle('delete', url_value=request_key, wrap_oauth=True)
        self.assertEqual(self.response_code(), 204,
                         'Response code does not equal 204')

    def test_api_delete_request_bad_key(self):
        self.assertRaises(exceptions.NotFoundException, self.handle, 'delete',
                          url_value='test', wrap_oauth=True)

    def test_api_delete_missing_oauth(self):
        self.assertRaises(exceptions.UnauthenticatedException,
                          self.handle, 'delete', url_value='test')

    # Other Tests

    def test_get_url(self):
        request_key = 'test'
        process = self._create_process()
        data = {'key_name': request_key, 'client': self.client,
                'process': process, 'requestor': 'test@flomosa.com',
                'first_name': 'Flo', 'last_name': 'Mo'}
        request = models.Request(**data)
        request.put()

        url = 'https://127.0.0.1:8080/requests/%s.json' % request_key
        self.assertEqual(request.get_absolute_url(), url)

    def test_request_methods(self):
        request_key = 'test'
        process = self._create_process()
        data = {'key_name': request_key, 'client': self.client,
                'process': process, 'requestor': 'test@flomosa.com',
                'first_name': 'Flo', 'last_name': 'Mo'}
        request = models.Request(**data)
        request.put()

        self.assertEqual(request.id, request_key)
        self.assertEqual(str(request), request_key)
        self.assertEqual(unicode(request), request_key)

    def test_request_no_access(self):
        request_key = 'test'
        process = self._create_process()
        data = {'key_name': request_key, 'client': self.client,
                'process': process, 'requestor': 'test@flomosa.com',
                'first_name': 'Flo', 'last_name': 'Mo'}
        request = models.Request(**data)
        request.put()

        other_client = create_client('otherclient', 'otherclient')
        self.assertRaises(exceptions.UnauthorizedException, models.Request.get,
                          request_key, other_client)

    def test_api_invalid_method(self):
        self.assertRaises(AttributeError, self.handle, 'asdf', wrap_oauth=True)

    def test_set_completed(self):
        request_key = 'test'
        process = self._create_process()
        data = {'key_name': request_key, 'client': self.client,
                'process': process, 'requestor': 'test@flomosa.com',
                'first_name': 'Flo', 'last_name': 'Mo'}
        request = models.Request(**data)
        request.put()

        self.assertFalse(request.is_completed)
        self.assertEqual(request.completed_date, None)
        submitted_date = request.submitted_date
        completed_date = datetime.now()
        key = request.set_completed(completed_date)
        self.assertEqual(key, request.key())
        self.assertTrue(request.is_completed)
        self.assertEqual(request.completed_date, completed_date)
        duration = _datetime_diff(submitted_date, completed_date)
        self.assertEqual(request.duration, duration)
        key = request.set_completed()
        self.assertEqual(key, None)

    def test_get_submitted_data(self):
        request_key = 'test'
        process = self._create_process()
        data = {'key_name': request_key, 'client': self.client,
                'process': process, 'requestor': 'test@flomosa.com',
                'first_name': 'Flo', 'last_name': 'Mo',
                'favorite_color': 'green'}
        request = models.Request(**data)
        request.put()

        dyn_data = request.get_submitted_data()
        self.assertEqual(len(dyn_data), 3)
        self.assertEqual(dyn_data['first_name'], data['first_name'])
        self.assertEqual(dyn_data['last_name'], data['last_name'])
        self.assertEqual(dyn_data['favorite_color'], data['favorite_color'])

    def test_to_dict(self):
        request_key = 'test'
        process = self._create_process()
        data = {'requestor': 'test@flomosa.com', 'first_name': 'Flo',
                'last_name': 'Mo', 'favorite_color': 'green',
                'contact': 'test2@flomosa.com'}
        request = models.Request(key_name=request_key, client=self.client,
                                 process=process, **data)
        request.put()

        request_dict = request.to_dict()
        for key, value in data.items():
            self.assertEqual(request_dict[key], value)
        self.assertEqual(request_dict['key'], request_key)


def _datetime_diff(date1, date2):
    if date1 > date2:
        delta = date1 - date2
    elif date2 < date1:
        delta = date2 - date1
    else:
        return 0
    duration = delta.days * 86400 + delta.seconds
    return duration

def _create_hub(url):
    hub = models.Hub(url=url)
    hub.put()
    return hub
