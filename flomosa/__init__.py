#
# Copyright 2010 Flomosa, LLC
#

import os


def is_development():
    try:
        env = os.environ['SERVER_SOFTWARE']
    except Exception:
        env = None

    if env and env == 'Development/1.0':
        return True
    return False