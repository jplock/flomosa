#!/usr/bin/env python
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
import unittest
import sys

from flomosa import test
test.fix_path()

from flomosa.tests.team_unittest import TeamTest


def usage():
    print 'run_tests.py [-v verbosity]'
    print '    -t   run specific testsuite'
    print '    -v   verbosity (0|1|2)'

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'ht:v:',
                                   ['help', 'testsuite', 'verbosity'])
    except Exception:
        usage()
        sys.exit(2)

    testsuite = 'all'
    verbosity = 1
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit()
        if opt in ('-t', '--testsuite'):
            testsuite = a
        if opt in ('-v', '--verbosity'):
            verbosity = int(arg)
    if len(args) != 0:
        usage()
        sys.exit()
    suite = unittest.TestSuite()
    if testsuite == 'all':
        suite.addTest(unittest.makeSuite(TeamTest))
    else:
        usage()
        sys.exit()
    unittest.TextTestRunner(verbosity=verbosity).run(suite)

if __name__ == '__main__':
    main()