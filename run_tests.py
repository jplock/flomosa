#!/usr/bin/env python2.5
# -*- coding: utf8 -*-
#
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2010 Flomosa, LLC
# All Rights Reserved.
#

"""
This is our basic test running framework.
"""

import getopt
import logging
import unittest
import sys

from flomosa import test
test.fix_path()

from flomosa.tests.client_unittest import ClientTest
from flomosa.tests.team_unittest import TeamTest
from flomosa.tests.process_unittest import ProcessTest
from flomosa.tests.step_unittest import ProcessStepTest, StepTest
from flomosa.tests.action_unittest import ProcessActionTest
from flomosa.tests.request_unittest import RequestTest
from flomosa.tests.execution_unittest import ExecutionTest
from flomosa.tests.workflow_unittest import WorkflowTest


def usage():
    print 'run_tests.py [-v verbosity] [-t testsuite] [-f format]'
    print '  -t  run specific testsuite [all|client|team|process|workflow|'
    print '                              action|step|request|execution]'
    print '  -v  verbosity [0|1|2]'
    print '  -f  format [text|xml]'


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'ht:v:f:',
                                   ['help', 'testsuite', 'verbosity',
                                    'format'])
    except Exception:
        usage()
        sys.exit(2)

    testsuite = 'all'
    verbosity = 1
    format = 'text'
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit()
        elif opt in ('-t', '--testsuite'):
            testsuite = arg
        elif opt in ('-v', '--verbosity'):
            verbosity = int(arg)
        elif opt in ('-f', '--format'):
            format = arg
    if len(args) != 0:
        usage()
        sys.exit()

    #logging.basicConfig(format='%(levelname)-8s %(filename)s] %(message)s')
    #logging.getLogger().setLevel(logging.DEBUG)

    suite = unittest.TestSuite()
    if testsuite == 'all':
        suite.addTest(unittest.makeSuite(ClientTest))
        suite.addTest(unittest.makeSuite(TeamTest))
        suite.addTest(unittest.makeSuite(ProcessTest))
        suite.addTest(unittest.makeSuite(ProcessStepTest))
        suite.addTest(unittest.makeSuite(ProcessActionTest))
        suite.addTest(unittest.makeSuite(StepTest))
        suite.addTest(unittest.makeSuite(RequestTest))
        suite.addTest(unittest.makeSuite(ExecutionTest))
        suite.addTest(unittest.makeSuite(WorkflowTest))
    elif testsuite == 'client':
        suite.addTest(unittest.makeSuite(ClientTest))
    elif testsuite == 'team':
        suite.addTest(unittest.makeSuite(TeamTest))
    elif testsuite == 'process':
        suite.addTest(unittest.makeSuite(ProcessTest))
    elif testsuite == 'action':
        suite.addTest(unittest.makeSuite(ProcessActionTest))
    elif testsuite == 'step':
        suite.addTest(unittest.makeSuite(ProcessStepTest))
        suite.addTest(unittest.makeSuite(StepTest))
    elif testsuite == 'request':
        suite.addTest(unittest.makeSuite(RequestTest))
    elif testsuite == 'execution':
        suite.addTest(unittest.makeSuite(ExecutionTest))
    elif testsuite == 'workflow':
        suite.addTest(unittest.makeSuite(WorkflowTest))
    else:
        usage()
        sys.exit()

    if format == 'text':
        unittest.TextTestRunner(verbosity=verbosity).run(suite)
    elif format == 'xml':
        import xmlrunner
        xmlrunner.XMLTestRunner(output='unittests.xml',
                                verbose=True).run(suite)


if __name__ == '__main__':
    main()
