#!/usr/bin/env python2.5
# -*- coding: utf8 -*-
#
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2010 Flomosa, LLC
# All Rights Reserved.
#

import os
import time


from flomosa import exceptions, models
from flomosa.test import HandlerTestBase, get_tasks, get_queues


class WorkflowRunner(HandlerTestBase):
    """Execute a process until completion."""

    def _load_json(self, filename):
        """Return the contents of a file."""
        full_path = os.path.realpath(os.sep.join([os.path.dirname(__file__),
                                                  'files', filename]))
        fp = open(full_path, 'rb')
        json = fp.read()
        fp.close()
        return json

    def load_team(self, filename, key='test'):
        """Create a team from a JSON file."""
        json = self._load_json(filename)

        from flomosa.api.team import TeamHandler
        self.handler_class = TeamHandler
        self.handle('put', body=json, url_value=key, wrap_oauth=True)
        self.assertEqual(self.response_code(), 201,
                         'Response code does not equal 201')
        return models.Team.get(key)

    def load_process(self, filename, key='test'):
        """Create a process from a JSON file."""
        json = self._load_json(filename)

        from flomosa.api.process import ProcessHandler
        self.handler_class = ProcessHandler
        self.handle('put', body=json, url_value=key, wrap_oauth=True)
        self.assertEqual(self.response_code(), 201,
                         'Response code does not equal 201')
        return models.Process.get(key)

    def create_request(self, process, data=None):
        """Create a request."""
        if data is None:
            data = {'requestor': 'test@flomosa.com', 'first_name': 'Flo',
                    'last_name': 'Mo'}
        if 'process' not in data:
            data['process'] = process.id

        from flomosa.api.request import RequestHandler
        self.handler_class = RequestHandler
        self.handle('post', params=data)
        self.assertEqual(self.response_code(), 201,
                         'Response code does not equal 201')
        resp_json = self.response_body()

        from django.utils import simplejson
        resp_data = simplejson.loads(resp_json)
        self.assertNotEqual(resp_data['key'], '')
        return models.Request.get(resp_data['key'])

    def create_hub(self, url):
        """Create a PubSubHubbub hub."""
        hub = models.Hub(url=url)
        hub.put()
        return hub

    def run_queues(self):
        """Run all available task queues."""
        for queue in get_queues():
            self.run_queue(queue['name'])

    def run_queue(self, queue_name):
        """Run a specific task queue by importing it's TaskHandler class."""
        TaskHandler = None
        if queue_name == 'execution-creation':
            from flomosa.queue.execution_creation import TaskHandler
        elif queue_name == 'execution-process':
            from flomosa.queue.execution_process import TaskHandler
        elif queue_name == 'mail-request-notify':
            from flomosa.queue.mail.request_notify import TaskHandler
        elif queue_name == 'process-callback':
            from flomosa.queue.process_callback import TaskHandler
        elif queue_name == 'request-callback':
            from flomosa.queue.request_callback import TaskHandler
        elif queue_name == 'request-statistics':
            from flomosa.queue.request_statistics import TaskHandler
        elif queue_name == 'step-callback':
            from flomosa.queue.step_callback import TaskHandler
        elif queue_name == 'mail-request-complete':
            from flomosa.queue.mail.request_complete import TaskHandler
        elif queue_name == 'mail-request-reminder':
            from flomosa.queue.mail.request_reminder import TaskHandler
        elif queue_name == 'mail-request-step':
            from flomosa.queue.mail.request_step import TaskHandler
        elif queue_name == 'mail-request-confirmation':
            from flomosa.queue.mail.request_confirmation import TaskHandler

        if TaskHandler:
            self.handler_class = TaskHandler
            tasks = get_tasks(queue_name)
            for task in tasks:
                self.handle('post', params=task['params'],
                            headers=task['headers'])

    def view_mail(self, execution, delay=2):
        """Record an execution as being viewed."""
        time.sleep(delay)

        self.assertEqual(execution.viewed_date, None)
        self.assertEqual(execution.email_delay, 0)

        from flomosa.web.viewed import ViewedHandler
        self.handler_class = ViewedHandler
        self.handle('get', url_value=execution.id)

        execution = models.Execution.get(execution.id)
        self.assertNotEqual(execution.viewed_date, None)
        print '--Viewing step "%s"' % execution.step.name
        print '----Sent on: %s' % execution.sent_date
        print '----View on: %s' % execution.viewed_date

        self.assertNotEqual(execution.email_delay, 0)

    def action_mail(self, execution, action, delay=2):
        """Record an execution has being actioned upon."""
        time.sleep(delay)

        print '--Actioning "%s" on step "%s"' % (action.name,
                                                 execution.step.name)

        self.assertEqual(execution.action, None)
        self.assertEqual(execution.end_date, None)
        self.assertEqual(execution.action_delay, 0)
        self.assertEqual(execution.duration, 0)

        from flomosa.web.viewed import ActionHandler
        self.handler_class = ActionHandler
        self.handle('get', url_value=execution.id, url_value2=action.id)

        execution = models.Execution.get(execution.id)
        self.assertNotEqual(execution.action, None)
        self.assertNotEqual(execution.end_date, None)
        self.assertNotEqual(execution.action_delay, 0)
        self.assertNotEqual(execution.duration, 0)
