#!/usr/bin/env python2.5
# -*- coding: utf8 -*-
#
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2010 Flomosa, LLC
# All Rights Reserved.
#

from flomosa import models
from flomosa.test import create_client, get_tasks
from flomosa.tests import runner


class WorkflowTest(runner.WorkflowRunner):
    """Test Case for entire request process."""

    def setUp(self):
        super(WorkflowTest, self).setUp()
        self.client = create_client()
        self.hub = self.create_hub('http://pubsubhubbub.appspot.com')
        self.team = self.load_team('sample_team.json')

    def tearDown(self):
        self.client.delete()
        self.hub.delete()
        self.team.delete()

    def test_serial_workflow(self):
        process = self.load_process('serial_process.json')
        request = self.create_request(process)
        request_key = request.id

        count = 0
        is_running = True
        while is_running:
            print 'PASS #%d' % count
            self.run_queues()

            # View the fake notification email
            open_executions = request.get_executions(actioned=False)
            for execution in open_executions:
                self.view_mail(execution)

                # Action the fake notification email
                found_action = False
                for action in execution.get_available_actions():
                    if not action.is_complete:
                        self.action_mail(execution, action)
                        found_action = True
                        break

                if not found_action:
                    print 'No non-complete actions found'
                    for action in execution.get_available_actions():
                        self.action_mail(execution, action)
                        found_action = True
                        break

                if not found_action:
                    is_running = False

            request = models.Request.get(request_key)
            if request.is_completed:
                is_running = False

            count += 1
