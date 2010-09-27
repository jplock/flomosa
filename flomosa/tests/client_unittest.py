#!/usr/bin/env python
# -*- coding: utf8 -*-
#
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2010 Flomosa, LLC
# All Rights Reserved.
#

from flomosa.test import HandlerTestBase
from flomosa.web.client import ClientHandler


class ClientTest(HandlerTestBase):
    """Test Case for clients"""

    handler_class = ClientHandler

    def test_create_client(self):
        self.handle('get')
        assert(self.response_code() == 200), 'Response code is not 200'
        assert(self.response_body() == 'Test account created'), 'Response body is not "Test account created"'