#!/usr/bin/env python
# -*- coding: utf8 -*-
#
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2010 Flomosa, LLC
# All Rights Reserved.
#

import uuid


def generate_key():
    """Generate a datastore key."""
    return str(uuid.uuid4())

def compute_duration(date1, date2):
    """Return the number of seconds between two dates."""
    duration = 0
    if date1 and date2:
        delta = abs(date1 - date2)
        duration = delta.days * 86400 + delta.seconds
    return duration