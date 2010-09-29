#!/usr/bin/env python
# -*- coding: utf8 -*-
#
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2010 Flomosa, LLC
# All Rights Reserved.
#

from django.utils import simplejson

from flomosa import exceptions
from flomosa.api.team import TeamHandler
from flomosa.test import HandlerTestBase, create_client, delete_client


class TeamTest(HandlerTestBase):
    """Test Case for teams"""

    handler_class = TeamHandler

    def setUp(self):
        super(TeamTest, self).setUp()
        create_client()

    def tearDown(self):
        super(TeamTest, self).tearDown()
        delete_client()

    def test_put_team(self):
        team_key = 'test'
        data = {'key': team_key, 'kind': 'Team', 'name': 'Test Team',
                'description': 'Test Description'}
        body = simplejson.dumps(data)
        self.handle('put', body=body, url_value=team_key, wrap_oauth=True)
        self.assertEquals(self.response_code(), 201,
                          'Response code does not equal 201')
        resp_json = self.response_body()
        resp_data = simplejson.loads(resp_json)
        for key, value in data.items():
            self.assertEquals(resp_data[key], data[key],
                              'Response "%s" does not equal "%s"' % (key,
                                                                     data[key]))

    def test_put_team_no_key(self):
        data = {'kind': 'Team', 'name': 'Test Team',
                'description': 'Test Description'}
        body = simplejson.dumps(data)
        self.handle('put', body=body, wrap_oauth=True)
        self.assertEquals(self.response_code(), 201,
                          'Response code does not equal 201')
        resp_json = self.response_body()
        resp_data = simplejson.loads(resp_json)
        for key, value in data.items():
            self.assertEquals(resp_data[key], data[key],
                              'Response "%s" does not equal "%s"' % (key,
                                                                     data[key]))

    def test_put_team_no_kind(self):
        data = {'name': 'Test Team', 'description': 'Test Description'}
        body = simplejson.dumps(data)

        self.assertRaises(exceptions.MissingException, self.handle, 'put',
                          body=body, wrap_oauth=True)

    def test_get_team(self):
        team_key = 'test'
        data = {'key': team_key, 'kind': 'Team', 'name': 'Test Team',
                'description': 'Test Description'}
        body = simplejson.dumps(data)
        self.handle('put', body=body, url_value=team_key, wrap_oauth=True)
        self.assertEquals(self.response_code(), 201,
                          'Response code does not equal 201')
        self.handle('get', url_value=team_key, wrap_oauth=True)
        self.assertEquals(self.response_code(), 200,
                          'Response code does not equal 200')
        resp_json = self.response_body()
        resp_data = simplejson.loads(resp_json)
        for key, value in data.items():
            self.assertEquals(resp_data[key], data[key],
                              'Response "%s" does not equal "%s"' % (key,
                                                                     data[key]))

    def test_delete_team(self):
        team_key = 'test'
        data = {'key': team_key, 'kind': 'Team', 'name': 'Test Team',
                'description': 'Test Description'}
        body = simplejson.dumps(data)
        self.handle('put', body=body, url_value=team_key, wrap_oauth=True)
        self.assertEquals(self.response_code(), 201,
                          'Response code does not equal 201')
        self.handle('delete', url_value=team_key, wrap_oauth=True)
        self.assertEquals(self.response_code(), 204,
                          'Response code does not equal 204')

    def test_put_missing_oauth(self):
        self.assertRaises(exceptions.UnauthenticatedException,
                          self.handle, 'put')

    def test_get_missing_oauth(self):
        self.assertRaises(exceptions.UnauthenticatedException,
                          self.handle, 'get')

    def test_delete_missing_oauth(self):
        self.assertRaises(exceptions.UnauthenticatedException,
                          self.handle, 'delete')