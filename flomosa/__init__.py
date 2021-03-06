#!/usr/bin/env python2.5
# -*- coding: utf8 -*-
#
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2010 Flomosa, LLC
# All Rights Reserved.
#

__all__ = ['is_development']

import os

import _version
__version__ = _version.__version__


def is_development():
    """Returns a boolean whether we're running on the devserver or not."""

    try:
        env = os.environ['SERVER_SOFTWARE']
    except Exception:
        try:
            env = os.environ['OS']
        except Exception:
            try:
                env = os.environ['OSTYPE']
            except Exception:
                env = None

    if env and env in ('Development/1.0', 'Windows_NT', 'FreeBSD', 'darwin'):
        return True
    return False
