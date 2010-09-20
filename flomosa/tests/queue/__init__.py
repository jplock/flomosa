# -*- coding: utf8 -*-
#
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2010 Flomosa, LLC
# All Rights Reserved.
#

__all__ = ['get_tasks']

import base64
import cgi


def get_tasks(queue_name, expected_count=None):
    """Retrieves Tasks from the supplied named queue.

    Args:
        queue_name: The queue to access.
        expected_count: If not None, the number of tasks expected to be in the
            queue. This function will raise an AssertionError exception if
            there are more or fewer tasks.

    Returns:
        List of dictionaries corresponding to each task, with the keys: 'name',
        'url', 'method', 'body', 'headers', 'params'. The 'params' value will
        only be present if the body's Content-Type header is
        'application/x-www-form-urlencoded'.
    """

    from google.appengine.api import apiproxy_stub_map
    stub = apiproxy_stub_map.apiproxy.GetStub('taskqueue')

    tasks = stub.GetTasks(queue_name)

    if expected_count is not None:
        assert len(tasks) == expected_count, 'found %s == %s' % (len(tasks),
                                                                 expected_count)
    for task in tasks:
        task['body'] = base64.b64decode(task['body'])
        # Convert headers list into a dictionary-- we don't care about repeats
        task['headers'] = dict(task['headers'])
        if ('application/x-www-form-urlencoded' in
            task['headers'].get('content-type', '')):
            task['params'] = dict(cgi.parse_qsl(task['body'], True))
    return tasks