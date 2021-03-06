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


class ProcessTest(HandlerTestBase):
    """Test Case for processes"""

    handler_class = ProcessHandler

    def setUp(self):
        super(ProcessTest, self).setUp()
        self.client = create_client()

    def tearDown(self):
        super(ProcessTest, self).tearDown()
        self.client.delete()

    # PUT Tests

    def test_api_put_process(self):
        process_key = 'test'
        data = {'key': process_key, 'kind': 'Process', 'name': 'Test Process'}
        body = simplejson.dumps(data)
        self.handle('put', body=body, url_value=process_key, wrap_oauth=True)
        self.assertEqual(self.response_code(), 201,
                         'Response code does not equal 201')
        resp_json = self.response_body()
        resp_data = simplejson.loads(resp_json)
        self.assertEqual(resp_data['key'], process_key)

    def test_api_put_process_no_key(self):
        data = {'kind': 'Process', 'name': 'Test Process'}
        body = simplejson.dumps(data)
        self.handle('put', body=body, wrap_oauth=True)
        self.assertEqual(self.response_code(), 201,
                         'Response code does not equal 201')
        resp_json = self.response_body()
        resp_data = simplejson.loads(resp_json)
        self.assertNotEquals(resp_data['key'], '')

    def test_api_put_process_no_name(self):
        data = {'kind': 'Process', 'description': 'Test Description'}
        body = simplejson.dumps(data)

        self.assertRaises(exceptions.MissingException, self.handle, 'put',
                          body=body, wrap_oauth=True)

    def test_api_put_process_no_kind(self):
        data = {'name': 'Test Process'}
        body = simplejson.dumps(data)

        self.assertRaises(exceptions.MissingException, self.handle, 'put',
                          body=body, wrap_oauth=True)

    def test_api_put_process_wrong_kind(self):
        data = {'kind': 'Client', 'name': 'Test Team'}
        body = simplejson.dumps(data)

        self.assertRaises(exceptions.MissingException, self.handle, 'put',
                          body=body, wrap_oauth=True)

    def test_api_put_missing_oauth(self):
        self.assertRaises(exceptions.UnauthenticatedException,
                          self.handle, 'put')

    # GET Tests

    def test_api_get_process(self):
        process_key = 'test'
        data = {'key': process_key, 'kind': 'Process', 'name': 'Test Process',
                'description': 'Test Description', 'collect_stats': True}
        body = simplejson.dumps(data)
        self.handle('put', body=body, url_value=process_key, wrap_oauth=True)
        self.assertEqual(self.response_code(), 201,
                         'Response code does not equal 201')
        self.handle('get', url_value=process_key, wrap_oauth=True)
        self.assertEqual(self.response_code(), 200,
                         'Response code does not equal 200')
        resp_json = self.response_body()
        resp_data = simplejson.loads(resp_json)
        for key, value in data.items():
            self.assertEqual(resp_data[key], value,
                             'Response "%s" does not equal "%s"' % (key,
                                                                    value))

    def test_api_get_process_bad_key(self):
        self.assertRaises(exceptions.NotFoundException, self.handle, 'get',
                          url_value='test', wrap_oauth=True)

    def test_api_get_missing_oauth(self):
        self.assertRaises(exceptions.UnauthenticatedException,
                          self.handle, 'get', url_value='test')

    # DELETE Tests

    def test_api_delete_process(self):
        process_key = 'test'
        data = {'key': process_key, 'kind': 'Process', 'name': 'Test Process',
                'description': 'Test Description', 'collect_stats': True}
        body = simplejson.dumps(data)
        self.handle('put', body=body, url_value=process_key, wrap_oauth=True)
        self.assertEqual(self.response_code(), 201,
                         'Response code does not equal 201')
        self.handle('delete', url_value=process_key, wrap_oauth=True)
        self.assertEqual(self.response_code(), 204,
                         'Response code does not equal 204')

    def test_api_delete_process_bad_key(self):
        self.assertRaises(exceptions.NotFoundException, self.handle, 'delete',
                          url_value='test', wrap_oauth=True)

    def test_api_delete_missing_oauth(self):
        self.assertRaises(exceptions.UnauthenticatedException,
                          self.handle, 'delete', url_value='test')

    # Other Tests

    def test_get_url(self):
        process_key = 'test'
        data = {'key_name': process_key, 'client': self.client,
                'name': 'Test Process', 'description': 'Test Description',
                'collect_stats': True}
        process = models.Process(**data)
        process.put()

        url = 'https://flomosa.appspot.com/processes/%s.json' % process_key
        self.assertEqual(process.get_absolute_url(), url)
        process.delete()

    def test_from_dict(self):
        self.assertRaises(exceptions.MissingException,
                          models.Process.from_dict, None, None)
        self.assertRaises(exceptions.MissingException,
                          models.Process.from_dict, 'test', None)
        self.assertRaises(exceptions.MissingException,
                          models.Process.from_dict, self.client, None)
        self.assertRaises(exceptions.MissingException,
                          models.Process.from_dict, self.client, 'test')
        data = {}
        self.assertRaises(exceptions.MissingException,
                          models.Process.from_dict, self.client, data)
        data['name'] = 'Test Process'
        self.assertRaises(exceptions.MissingException,
                          models.Process.from_dict, self.client, data)
        data['kind'] = 'Client'
        self.assertRaises(exceptions.MissingException,
                          models.Process.from_dict, self.client, data)

    def test_to_dict(self):
        process_key = 'test'
        data = {'name': 'Test Process', 'description': 'Test Description',
                'collect_stats': True}
        process = models.Process(key_name=process_key, client=self.client,
                                 **data)

        process_dict = process.to_dict()
        for key, value in data.items():
            self.assertEqual(value, process_dict[key])

        process.put()
        self.assertEqual(process.to_dict()['key'], process_key)

    def test_process_methods(self):
        process_key = 'test'
        data = {'name': 'Test Process'}
        process = models.Process(key_name=process_key, client=self.client,
                                 **data)
        process.put()

        self.assertEqual(process.id, process_key)
        self.assertEqual(str(process), process_key)
        self.assertEqual(unicode(process), process_key)

    def test_process_no_access(self):
        process_key = 'test'
        data = {'name': 'Test Process', 'description': 'Test Description',
                'collect_stats': True}
        process = models.Process(key_name=process_key, client=self.client,
                                 **data)
        process.put()

        other_client = create_client('otherclient', 'otherclient')
        self.assertRaises(exceptions.UnauthorizedException, models.Process.get,
                          process_key, other_client)

    def test_process_is_valid(self):
        team_key = 'test'
        team = models.Team(key_name=team_key, client=self.client,
                           name='Test Team', members=['test@flomosa.com'])
        team.put()

        process_key = 'test'
        step1 = {'kind': 'Step', 'key': 'step1', 'name': '1st Step',
                 'team': team_key}

        data = {
            'key': process_key,
            'kind': 'Process',
            'name': 'Test Process',
            'steps': [step1]
        }
        body = simplejson.dumps(data)
        self.handle('put', body=body, url_value=process_key, wrap_oauth=True)
        self.assertEqual(self.response_code(), 201,
                         'Response code does not equal 201')
        resp_json = self.response_body()
        resp_data = simplejson.loads(resp_json)
        self.assertEqual(resp_data['key'], process_key)

        process = models.Process.get_by_key_name(process_key)
        self.assertTrue(process.is_valid())

        team.members = []
        team.put()
        self.assertFalse(process.is_valid())

    def test_api_invalid_method(self):
        self.assertRaises(AttributeError, self.handle, 'asdf', wrap_oauth=True)
