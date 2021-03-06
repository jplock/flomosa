#!/usr/bin/env python2.5
# -*- coding: utf8 -*-
#
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2010 Flomosa, LLC
# All Rights Reserved.
#

from datetime import datetime
import logging
import time

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api import taskqueue

from flomosa import exceptions, models, settings
from flomosa.queue import QueueHandler


class TaskHandler(QueueHandler):
    """Main task queue for execution processing."""

    def post(self):
        logging.debug('Begin execution-process task handler')

        num_tries = self.request.headers['X-AppEngine-TaskRetryCount']
        logging.info('Task has been executed %s times', num_tries)

        execution_key = self.request.get('key')
        if not execution_key:
            raise exceptions.MissingException('Missing "key" parameter.')

        execution = models.Execution.get(execution_key)

        if not isinstance(execution.step, models.Step):
            raise exceptions.InternalException(
                'Execution "%s" has no step defined.' % execution.id)

        if not isinstance(execution.request, models.Request):
            raise exceptions.InternalException(
                'Execution "%s" has no request defined.' % execution.id)

        if not execution.step.actions:
            raise exceptions.InternalException(
                'Step "%s" has no actions defined.' % execution.step.id)

        if not execution.member:
            raise exceptions.InternalException(
                'Execution "%s" has no email address.' % execution.id)

        # Always fetch the latest version of the request from the datastore
        request_key = execution.request.id
        request = models.Request.get_by_key_name(request_key)
        if not request:
            raise exceptions.InternalException(
                'Request "%s" not found in datastore.' % request_key)
        execution.request = request

        # If the request has been completed, close out this execution
        if request.is_completed:
            logging.info(
                'Request "%s" already completed. Exiting.', request.id)
            execution.end_date = request.completed_date
            execution.put()

            return self.halt_success()

        # If we have not sent the email notifications
        if not execution.queued_for_send:
            execution.queued_for_send = True
            execution.put()

            task = taskqueue.Task(params={'key': execution.id})
            queue = taskqueue.Queue('mail-request-notify')
            queue.add(task)

            logging.info('Queued notification email to be sent to "%s" for ' \
                'Execution "%s". Re-queuing.', execution.member, execution.id)
            return self.halt_requeue()

        # If this task was executed again, and we queued the notification
        # email to be sent, but it has not yet been sent, re-queue this task
        # and wait until the notification email has been sent.
        if not execution.sent_date:
            logging.warning('Notification email not yet sent for Execution ' \
                '"%s". Re-queuing.', execution.id)
            return self.halt_requeue()

        # Has this step already been completed by another team member?
        completed_execution = execution.is_step_completed()

        # Check that another team member didn't already complete this step for
        # this request. Request must not have gone through this step multiple
        # times.
        if completed_execution and execution.num_passes() == 1:
            execution.end_date = completed_execution.end_date
            execution.put()

            logging.warning('Step "%s" completed by "%s" on "%s". Exiting.',
                            execution.step.id, completed_execution.member,
                            completed_execution.end_date)
            return self.halt_success()

        # If an action has been chosen, halt this execution
        if execution.action and isinstance(execution.action, models.Action):
            logging.info('Completed Execution "%s". Exiting.' % execution.id)
            return self.halt_success()

        # Reached reminder limit, halt this execution
        if execution.reminder_count == settings.REMINDER_LIMIT:
            logging.warning(
                'Reminder limit reached for Execution "%s". Exiting.',
                execution.id)
            return self.halt_success()

        # Send a reminder email notification
        else:
            delta = None
            num_seconds = 0
            if execution.last_reminder_sent_date:
                delta = datetime.now() - execution.last_reminder_sent_date
            elif execution.sent_date:
                delta = datetime.now() - execution.sent_date
            if delta:
                num_seconds = delta.days * 86400 + delta.seconds

            # If are under the REMINDER_DELAY variable, queue up a reminder
            # email to be sent to the member.
            if num_seconds >= settings.REMINDER_DELAY:
                logging.info('Queuing reminder email #%s to be sent "%s".',
                             execution.reminder_count, execution.member)
                task = taskqueue.Task(params={'key': execution.id})
                queue = taskqueue.Queue('mail-request-reminder')
                queue.add(task)
            else:
                logging.info('Reminder #%d delay for Execution "%s" has not ' \
                    'expired (%d >= %d).', (execution.reminder_count + 1),
                    execution.id, num_seconds, settings.REMINDER_DELAY)

        logging.info('Re-queuing Execution "%s".', execution.id)
        self.error(500)

        logging.debug('Finished execution-process task handler')

def main():
    """Main task queue for execution processing."""
    application = webapp.WSGIApplication([('/_ah/queue/execution-process',
        TaskHandler)], debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
