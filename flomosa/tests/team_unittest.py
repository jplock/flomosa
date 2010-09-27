#!/usr/bin/env python
# -*- coding: utf8 -*-
#
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2010 Flomosa, LLC
# All Rights Reserved.
#

import logging
import unittest

#from google.appengine.ext import webapp

from flomosa.api.team import TeamHandler
from flomosa.test import HandlerTestBase


class TeamTest(HandlerTestBase):
    """Test Case for teams"""

    handler_class = TeamHandler

    def setUp(self):  # pylint: disable-msg=C0103
        logging.getLogger().setLevel(logging.DEBUG)
        super(TeamTest, self).setUp()

    def test_create_team(self):
        pass

    def test_get_team(self):
        headers = {'oauth_consumer_key': 'test',
                   'Authorization': 'asdf'}
        params = {'team_key': 'test'}

        self.handle('get', params=params, headers=headers)

    def test_delete_team(self):
        pass