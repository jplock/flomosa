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
from flomosa.api.team import TeamHandler


class TeamTest(HandlerTestBase):
    """Test Case for teams"""

    handler_class = TeamHandler

    def setUp(self):
        super(TeamTest, self).setUp()
        self.client = create_client()

    def tearDown(self):
        super(TeamTest, self).tearDown()
        self.client.delete()

    # PUT Tests

    def test_api_put_team(self):
        team_key = 'test'
        data = {'key': team_key, 'kind': 'Team', 'name': 'Test Team',
                'description': 'Test Description'}
        body = simplejson.dumps(data)
        self.handle('put', body=body, url_value=team_key, wrap_oauth=True)
        self.assertEqual(self.response_code(), 201,
                         'Response code does not equal 201')
        resp_json = self.response_body()
        resp_data = simplejson.loads(resp_json)
        for key, value in data.items():
            self.assertEqual(resp_data[key], value,
                             'Response "%s" does not equal "%s"' % (key,
                                                                    value))

    def test_api_put_team_no_key(self):
        data = {'kind': 'Team', 'name': 'Test Team',
                'description': 'Test Description'}
        body = simplejson.dumps(data)
        self.handle('put', body=body, wrap_oauth=True)
        self.assertEqual(self.response_code(), 201,
                         'Response code does not equal 201')
        resp_json = self.response_body()
        resp_data = simplejson.loads(resp_json)
        for key, value in data.items():
            self.assertEqual(resp_data[key], value,
                             'Response "%s" does not equal "%s"' % (key,
                                                                    value))

    def test_api_put_team_no_name(self):
        data = {'kind': 'Team', 'description': 'Test Description'}
        body = simplejson.dumps(data)

        self.assertRaises(exceptions.MissingException, self.handle, 'put',
                          body=body, wrap_oauth=True)

    def test_api_put_team_no_kind(self):
        data = {'name': 'Test Team', 'description': 'Test Description'}
        body = simplejson.dumps(data)

        self.assertRaises(exceptions.MissingException, self.handle, 'put',
                          body=body, wrap_oauth=True)

    def test_api_put_team_wrong_kind(self):
        data = {'kind': 'Client', 'name': 'Test Team'}
        body = simplejson.dumps(data)

        self.assertRaises(exceptions.MissingException, self.handle, 'put',
                          body=body, wrap_oauth=True)

    def test_api_put_missing_oauth(self):
        self.assertRaises(exceptions.UnauthenticatedException,
                          self.handle, 'put')

    # GET Tests

    def test_api_get_team(self):
        team_key = 'test'
        data = {'key': team_key, 'kind': 'Team', 'name': 'Test Team',
                'description': 'Test Description'}
        body = simplejson.dumps(data)
        self.handle('put', body=body, url_value=team_key, wrap_oauth=True)
        self.assertEqual(self.response_code(), 201,
                         'Response code does not equal 201')
        self.handle('get', url_value=team_key, wrap_oauth=True)
        self.assertEqual(self.response_code(), 200,
                         'Response code does not equal 200')
        resp_json = self.response_body()
        resp_data = simplejson.loads(resp_json)
        for key, value in data.items():
            self.assertEqual(resp_data[key], value,
                             'Response "%s" does not equal "%s"' % (key,
                                                                    value))

    def test_api_get_team_bad_key(self):
        self.assertRaises(exceptions.NotFoundException, self.handle, 'get',
                          url_value='test', wrap_oauth=True)

    def test_api_get_missing_oauth(self):
        self.assertRaises(exceptions.UnauthenticatedException,
                          self.handle, 'get', url_value='test')

    # DELETE Tests

    def test_api_delete_team(self):
        team_key = 'test'
        data = {'key': team_key, 'kind': 'Team', 'name': 'Test Team',
                'description': 'Test Description'}
        body = simplejson.dumps(data)
        self.handle('put', body=body, url_value=team_key, wrap_oauth=True)
        self.assertEqual(self.response_code(), 201,
                         'Response code does not equal 201')
        self.handle('delete', url_value=team_key, wrap_oauth=True)
        self.assertEqual(self.response_code(), 204,
                         'Response code does not equal 204')

    def test_api_delete_team_bad_key(self):
        self.assertRaises(exceptions.NotFoundException, self.handle, 'delete',
                          url_value='test', wrap_oauth=True)

    def test_api_delete_missing_oauth(self):
        self.assertRaises(exceptions.UnauthenticatedException,
                          self.handle, 'delete', url_value='test')

    # Other Tests

    def test_get_url(self):
        team_key = 'test'
        data = {'key_name': team_key, 'client': self.client,
                'name': 'Test Team', 'description': 'Test Description'}
        team = models.Team(**data)
        team.put()

        url = 'https://flomosa.appspot.com/teams/%s.json' % team_key
        self.assertEqual(team.get_absolute_url(), url)

    def test_from_dict(self):
        self.assertRaises(exceptions.MissingException, models.Team.from_dict,
                          None, None)
        self.assertRaises(exceptions.MissingException, models.Team.from_dict,
                          'test', None)
        self.assertRaises(exceptions.MissingException, models.Team.from_dict,
                          self.client, None)
        self.assertRaises(exceptions.MissingException, models.Team.from_dict,
                          self.client, 'test')
        data = {}
        self.assertRaises(exceptions.MissingException, models.Team.from_dict,
                          self.client, data)
        data['name'] = 'Test Team'
        self.assertRaises(exceptions.MissingException, models.Team.from_dict,
                          self.client, data)
        data['kind'] = 'Client'
        self.assertRaises(exceptions.MissingException, models.Team.from_dict,
                          self.client, data)

    def test_to_dict(self):
        team_key = 'test'
        data = {'name': 'Test Team', 'description': 'Test Description',
                'members': ['test1@flomosa.com', 'test2@flomosa.com']}
        team = models.Team(key_name=team_key, client=self.client, **data)
        team.put()

        team_dict = team.to_dict()
        for key, value in data.items():
            self.assertEqual(team_dict[key], value)
        self.assertEqual(team_dict['key'], team_key)

    def test_team_methods(self):
        team_key = 'test'
        data = {'name': 'Test Team', 'description': 'Test Description',
                'members': ['test1@flomosa.com', 'test2@flomosa.com']}
        team = models.Team(key_name=team_key, client=self.client, **data)
        team.put()

        self.assertEqual(team.id, team_key)
        self.assertEqual(str(team), team_key)
        self.assertEqual(unicode(team), team_key)

    def test_team_no_access(self):
        team_key = 'test'
        data = {'name': 'Test Team', 'description': 'Test Description',
                'members': ['test1@flomosa.com', 'test2@flomosa.com']}
        team = models.Team(key_name=team_key, client=self.client, **data)
        team.put()

        other_client = create_client('otherclient', 'otherclient')
        self.assertRaises(exceptions.UnauthorizedException, models.Team.get,
                          team_key, other_client)

    def test_api_invalid_method(self):
        self.assertRaises(AttributeError, self.handle, 'asdf', wrap_oauth=True)