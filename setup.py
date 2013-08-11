#!/usr/bin/env python2.5
# -*- coding: utf8 -*-
#
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2010 Flomosa, LLC
# All Rights Reserved.
#

from __future__ import with_statement
import os
import re
import subprocess
from setuptools import setup, find_packages
from setuptools.command.sdist import sdist


PKG = 'flomosa'
VERSIONFILE = os.path.join(PKG, '_version.py')
verstr = 'unknown'
try:
    verstrline = open(VERSIONFILE, 'rt').read()
except EnvironmentError:
    pass  # no version file
else:
    VSRE = r"^verstr = ['\"]([^'\"]*)['\"]"
    mo = re.search(VSRE, verstrline, re.M)
    if mo:
        verstr = mo.group(1)
    else:
        print 'unable to find version in %s' % VERSIONFILE
        raise RuntimeError('if %s.py exists, it must be well-formed' \
                           % VERSIONFILE)


class local_sdist(sdist):
    """Customized sdist hook - builds the ChangeLog file from VC first"""

    def run(self):
        if os.path.isdir('.git'):
            # We're in a Git branch

            log_cmd = subprocess.Popen(['git', 'log'], stdout=subprocess.PIPE)
            changelog = log_cmd.communicate()[0]
            with open('ChangeLog', 'w') as changelog_file:
                changelog_file.write(changelog)
        sdist.run(self)


setup(
    name=PKG,
    version=verstr,
    description='Flomosa AppEngine code',
    author='Justin Plock',
    author_email='jplock@gmail.com',
    url='http://github.com/jplock/flomosa',
    packages=find_packages(),
    provides=['flomosa'],
    keywords='flomosa',
    zip_safe=False,
    test_suite='flomosa.test',
    cmdclass={'sdist': local_sdist}
)
