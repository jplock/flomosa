#!/usr/bin/env python2.5
# -*- coding: utf8 -*-
#
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2010 Flomosa, LLC
# All Rights Reserved.
#

__version__ = '1.0.0'
__all__ = ['is_development']

import os


def is_development():
    try:
        env = os.environ['SERVER_SOFTWARE']
    except Exception:
        env = None

    if env and env == 'Development/1.0':
        return True
    return False