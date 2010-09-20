# -*- coding: utf8 -*-
#
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2010 Flomosa, LLC
# All Rights Reserved.
#

__all__ = ['fix_paths', 'setup_for_testing']

import logging
import os
import sys
import tempfile


TEST_APP_ID = 'flomosa'
TEST_VERSION_ID = '2'

# Assign the application ID up front here so we can create db.Key instances
# before doing any other test setup.
os.environ['APPLICATION_ID'] = TEST_APP_ID
os.environ['CURRENT_VERSION_ID'] = TEST_VERSION_ID


def fix_path():
    """Finds the google_appengine directory and fixes Python imports to use it.

    """
    all_paths = os.environ.get('PATH').split(os.pathsep)
    for path_dir in all_paths:
        dev_appserver_path = os.path.join(path_dir, 'dev_appserver.py')
        if os.path.exists(dev_appserver_path):
            google_appengine = os.path.dirname(os.path.realpath(
                dev_appserver_path))
            sys.path.append(google_appengine)
            # Use the next import will fix up sys.path even further to bring in
            # any dependent lib directories that the SDK needs.
            dev_appserver = __import__('dev_appserver')
            sys.path.extend(dev_appserver.EXTRA_PATHS)
            return

def setup_for_testing(require_indexes=True):
    """Sets up the stubs for testing.

    Args:
        require_indexes: True if indexes should be required for all indexes.
    """
    from google.appengine.api import apiproxy_stub_map
    from google.appengine.api import memcache
    from google.appengine.tools import dev_appserver
    from google.appengine.tools import dev_appserver_index
    import urlfetch_test_stub
    before_level = logging.getLogger().getEffectiveLevel()
    try:
        logging.getLogger().setLevel(100)
        root_path = os.path.realpath(os.path.dirname(__file__))
        dev_appserver.SetupStubs(
            TEST_APP_ID,
            root_path=root_path,
            login_url='',
            datastore_path=tempfile.mktemp(suffix='datastore_stub'),
            history_path=tempfile.mktemp(suffix='datastore_history'),
            blobstore_path=tempfile.mktemp(suffix='blobstore_stub'),
            require_indexes=require_indexes,
            clear_datastore=False)
        dev_appserver_index.SetupIndexes(TEST_APP_ID, root_path)
        apiproxy_stub_map.apiproxy._APIProxyStubMap__stub_map['urlfetch'] = \
            urlfetch_test_stub.instance
        # Actually need to flush, even though we've reallocated. Maybe because
        # the memcache stub's cache is at the module level, not the API stub?
        memcache.flush_all()
    finally:
        logging.getLogger().setLevel(before_level)