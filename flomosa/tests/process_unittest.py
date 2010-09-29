#!/usr/bin/env python
# -*- coding: utf8 -*-
#
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2010 Flomosa, LLC
# All Rights Reserved.
#

from flomosa.test import HandlerTestBase
from flomosa.api.process import ProcessHandler


class ProcessTest(HandlerTestBase):
    """Test Case for processes"""

    handler_class = ProcessHandler

    def test_create_process(self):
        pass