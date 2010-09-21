# -*- coding: utf8 -*-
#
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2010 Flomosa, LLC
# All Rights Reserved.
#

import uuid


def generate_key():
    "Generate a datastore key."
    return str(uuid.uuid4())