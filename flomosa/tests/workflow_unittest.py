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

from django.utils import simplejson

from flomosa import exceptions, models
from flomosa.test import HandlerTestBase, create_client, get_tasks
from flomosa.api.team import TeamHandler
from flomosa.api.process import ProcessHandler
from flomosa.api.request import RequestHandler
from flomosa.web.viewed import ViewedHandler, ActionHandler
from flomosa.queue.execution_creation import TaskHandler as creation_handler
from flomosa.queue.execution_process import TaskHandler as process_handler
from flomosa.queue.process_callback import TaskHandler as process_callback
from flomosa.queue.request_callback import TaskHandler as request_callback
from flomosa.queue.request_statistics import TaskHandler as statistics_handler
from flomosa.queue.step_callback import TaskHandler as step_callback
from flomosa.queue.mail.request_notify import TaskHandler as mail_notify
from flomosa.queue.mail.request_complete import TaskHandler as mail_complete
from flomosa.queue.mail.request_reminder import TaskHandler as mail_reminder
from flomosa.queue.mail.request_step import TaskHandler as mail_step
from flomosa.queue.mail.request_confirmation import TaskHandler as mail_confirmation


class WorkflowTest(HandlerTestBase):
    """Test Case for entire request process."""

    handler_class = RequestHandler

    def setUp(self):
        super(WorkflowTest, self).setUp()
        self.client = create_client()
        self.team = self._create_team()

    def tearDown(self):
        self.client.delete()
        self.team.delete()

    def _load_json(self, filename):
        full_path = os.path.realpath(os.sep.join([os.path.dirname(__file__),
                                                  'files', filename]))
        fp = open(full_path, 'rb')
        json = fp.read()
        fp.close()
        return json

    def _create_team(self, key='test'):
        team_json = self._load_json('sample_team.json')

        self.handler_class = TeamHandler
        self.handle('put', body=team_json, url_value=key, wrap_oauth=True)
        self.assertEqual(self.response_code(), 201,
                         'Response code does not equal 201')
        return models.Team.get(key)

    def _create_process(self, filename, key='test'):
        process_json = self._load_json(filename)

        self.handler_class = ProcessHandler
        self.handle('put', body=process_json, url_value=key, wrap_oauth=True)
        self.assertEqual(self.response_code(), 201,
                         'Response code does not equal 201')
        return models.Process.get(key)

    def _create_request(self, process):
        data = {'process': process.id, 'requestor': 'test@flomosa.com'}
        self.handler_class = RequestHandler
        self.handle('post', params=data)
        self.assertEqual(self.response_code(), 201,
                         'Response code does not equal 201')
        resp_json = self.response_body()
        resp_data = simplejson.loads(resp_json)
        self.assertNotEqual(resp_data['key'], '')
        return resp_data['key']

    def _create_executions(self):
        self.handler_class = creation_handler

        tasks = get_tasks('execution-creation')
        for task in tasks:
            self.assertRaises(exceptions.MissingException, self.handle, 'post',
                              params={}, headers=task['headers'])
            self.assertRaises(exceptions.NotFoundException, self.handle, 'post',
                              params={'step_key': 'test',
                                      'request_key': 'test', 'member': 'test'},
                              headers=task['headers'])
            self.handle('post', params=task['params'], headers=task['headers'])

    def _process_executions(self):
        self.handler_class = process_handler

        tasks = get_tasks('execution-process')
        for task in tasks:
            self.assertRaises(exceptions.MissingException, self.handle, 'post',
                              params={}, headers=task['headers'])
            self.assertRaises(exceptions.NotFoundException, self.handle, 'post',
                              params={'key': 'test'}, headers=task['headers'])
            self.handle('post', params=task['params'], headers=task['headers'])

    def _send_notification_mail(self):
        self.handler_class = mail_notify

        tasks = get_tasks('mail-request-notify')
        for task in tasks:
            self.assertRaises(exceptions.MissingException, self.handle, 'post',
                              params={}, headers=task['headers'])
            self.assertRaises(exceptions.NotFoundException, self.handle, 'post',
                              params={'key': 'test'}, headers=task['headers'])
            self.handle('post', params=task['params'], headers=task['headers'])
            self.assertEqual(self.response_code(), 200,
                             'Response code does not equal 200.')

    def _view_mail(self, execution):
        time.sleep(2)

        self.assertEqual(execution.viewed_date, None)
        self.assertEqual(execution.email_delay, 0)
        self.handler_class = ViewedHandler
        self.handle('get', url_value=execution.id)

        execution = models.Execution.get(execution.id)
        self.assertNotEqual(execution.viewed_date, None)
        print '--Viewing step "%s"' % execution.step.name
        print '----Sent on: %s' % execution.sent_date
        print '----View on: %s' % execution.viewed_date

        self.assertNotEqual(execution.email_delay, 0)

    def _action_mail(self, execution, action):
        time.sleep(2)

        print '--Actioning "%s" on step "%s"' % (action.name, execution.step.name)

        self.assertEqual(execution.action, None)
        self.assertEqual(execution.end_date, None)
        self.assertEqual(execution.action_delay, 0)
        self.assertEqual(execution.duration, 0)
        self.handler_class = ActionHandler
        self.handle('get', url_value=execution.id, url_value2=action.id)

        execution = models.Execution.get(execution.id)
        self.assertNotEqual(execution.action, None)
        self.assertNotEqual(execution.end_date, None)
        self.assertNotEqual(execution.action_delay, 0)
        self.assertNotEqual(execution.duration, 0)

    def test_serial_workflow(self):
        hub = _create_hub('http://pubsubhubbub.appspot.com')

        process = self._create_process('serial_process.json')
        request_key = self._create_request(process)
        first_step = process.get_start_step()

        stat_tasks = get_tasks('request-statistics', 1)
        for task in stat_tasks:
            params = task['params']
            self.assertEqual(params['request_key'], request_key)

        request = models.Request.get(request_key)

        count = 0
        is_running = True
        while is_running:
            print 'PASS #%d' % count

            # Create the executions
            self._create_executions()
            # Process the executions
            self._process_executions()
            # Send the initial notification email
            self._send_notification_mail()

            # View the fake notification email
            open_executions = request.get_executions(actioned=False)
            for execution in open_executions:
                self._view_mail(execution)

                # Action the fake notification email
                found_action = False
                for action in execution.get_available_actions():
                    if not action.is_complete:
                        self._action_mail(execution, action)
                        found_action = True
                        break

                if not found_action:
                    print 'No non-complete actions found'
                    for action in execution.get_available_actions():
                        self._action_mail(execution, action)
                        found_action = True
                        break

                if not found_action:
                    is_running = False



            request = models.Request.get(request_key)
            if request.is_completed:
                is_running = False

            count += 1


def _create_hub(url):
    hub = models.Hub(url=url)
    hub.put()
    return hub
