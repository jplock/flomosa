#!/usr/bin/env python
# -*- coding: utf8 -*-
#
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2010 Flomosa, LLC
# All Rights Reserved.
#

from django.utils import simplejson

from flomosa.api.team import TeamHandler
from flomosa.test import HandlerTestBase


class TeamTest(HandlerTestBase):
    """Test Case for teams"""

    handler_class = TeamHandler

    def setUp(self):
        headers = {'oauth_consumer_key': 'test',
                   'Authorization': 'asdf'}
        self.headers = headers

    def test_create_team(self):
        data = {'name': 'Test Team'}
        body = simplejson.dumps(data)
        self.handle_body('put', 'test', body, headers=self.headers)

    def test_get_team(self):
        self.handle('get', 'test', headers=self.headers)

    def test_delete_team(self):
        self.handle('delete', 'test', headers=self.headers)