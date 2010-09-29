#!/usr/bin/env python
# -*- coding: utf8 -*-
#
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2010 Flomosa, LLC
# All Rights Reserved.
#

from django.utils import simplejson

import oauth2 as oauth
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

    def test_create_team(self):
        data = {'key': 'test', 'kind': 'Team', 'name': 'Test Team',
                'description': 'Test Description'}
        body = simplejson.dumps(data)
        self.handle('put', body=body, url_value='test', wrap_oauth=True)
        self.assertEquals(self.response_code(), 201,
                          'Response code does not equal 201')
        resp_json = self.response_body()
        resp_dict = simplejson.loads(resp_json)
        for key, value in data.items():
            self.assertEquals(resp_dict[key], data[key],
                              'Response "%s" does not equal "%s"' % (key,
                                                                     data[key]))
        team_key = resp_dict['key']
        self.handle('get', url_value=team_key, wrap_oauth=True)
        self.handle('delete', url_value=team_key, wrap_oauth=True)