#!/usr/bin/env python2.5
# -*- coding: utf8 -*-
#
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2010 Flomosa, LLC
# All Rights Reserved.
#

import os
import subprocess
from setuptools import setup, find_packages
from setuptools.command.sdist import sdist


class local_sdist(sdist):
    """Customized sdist hook - builds the ChangeLog file from VC first"""

    def run(self):
        if os.path.isdir('.git'):
            # We're in a Git branch

            log_cmd = subprocess.Popen(['git', 'log'],
                                       stdout=subprocess.PIPE)
            changelog = log_cmd.communicate()[0]
            with open('ChangeLog', 'w') as changelog_file:
                changelog_file.write(changelog)
        sdist.run(self)


setup(
    name='flomosa',
    version='2.0.0',
    description='Flomosa Google AppEngine code',
    author='Flomosa, LLC.',
    author_email='team@flomosa.com',
    url='http://github.com/flomosa/flomosa',
    packages=find_packages(),
    scripts = ['run_tests.py'],
    cmdclass={'sdist': local_sdist}
)