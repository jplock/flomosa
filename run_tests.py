# -*- coding: utf8 -*-
#
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2010 Flomosa, LLC
# All Rights Reserved.
#

"""
This is our basic test running framework.

Usage Examples:

    # to run all the tests
    python run_tests.py

    # to run a specific test suite imported here
    python run_tests.py NodeConnectionTestCase

    # to run a specific test imported here
    python run_tests.py NodeConnectionTestCase.test_reboot

    # to run some test suites elsewhere
    python run_tests.py nova.tests.node_unittest
    python run_tests.py nova.tests.node_unittest.NodeConnectionTestCase

"""

import __main__
import os
import sys

#from nova import datastore
#from nova import flags
#from nova import twistd

#from nova.tests.access_unittest import *


if __name__ == '__main__':
    pass
