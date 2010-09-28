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
        data = {'name': 'Test Team'}
        body = simplejson.dumps(data)
        self.handle_body('put', 'test', body, add_oauth=True)

    def test_get_team(self):
        self.handle('get', 'test', add_oauth=True)

    def test_delete_team(self):
        self.handle('delete', 'test', add_oauth=True)