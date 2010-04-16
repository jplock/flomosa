#
# Copyright 2010 Flomosa, LLC
#

import logging
from datetime import datetime

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api.labs import taskqueue

import models
import settings


class TaskHandler(webapp.RequestHandler):
    def post(self):
        logging.debug('Begin request-process task handler')

        num_tries = self.request.headers['X-AppEngine-TaskRetryCount']
        logging.info('Task has been executed %s times' % num_tries)

        execution_key = self.request.get('key')
        if not execution_key:
            logging.error('Missing "key" parameter. Exiting.')
            return None

        execution = models.Execution.get(execution_key)
        if execution is None:
            logging.error('Execution "%s" not found in datastore. Exiting.' % \
                execution_key)
            return None

        if not isinstance(execution.step, models.Step):
            logging.error('Execution "%s" has no step defined. Exiting.' % \
                execution.id)
            return None

        if not isinstance(execution.request, models.Request):
            logging.error('Execution "%s" has no request defined. Exiting.' % \
                execution.step.id)
            return None

        if not execution.step.actions:
            logging.error('Step "%s" has no actions defined. Exiting.' % \
                execution.step.id)
            return None

        if not execution.member:
            logging.error('Execution "%s" has no email address. Exiting.' % \
                execution.id)
            return None

        # If the request has been completed, close out this execution
        if execution.request.is_completed:
            execution.end_date = execution.request.completed_date

            try:
                execution.put()
            except Exception, e:
                logging.warning('%s Exiting.' % e)

            self.error(200)
            return None

        # If we have not sent the email notifications
        if not execution.queued_for_send:
            execution.queued_for_send = True

            try:
                execution.put()
            except Exception, e:
                logging.error(e)

            task = taskqueue.Task(params={'key': execution.id})
            queue = taskqueue.Queue('mail-request-notify')
            queue.add(task)

            logging.info('Queued notification email to be sent to "%s" for ' \
                'Execution "%s". Re-queuing.' % (execution.member,
                execution.id))
            self.error(500)
            return None

        # If this task was executed again, and we queued the notification
        # email to be sent, but it has not yet been sent, re-queue this task
        # and wait until the notification email has been sent.
        if not execution.sent_date:
            logging.warning('Notification email not yet sent for Execution ' \
                '"%s". Re-queuing.' % execution.id)
            self.error(500)
            return None

        # Has this step already been completed by another team member?
        completed_execution = execution.is_step_completed()

        # Check that another team member didn't already complete this step for
        # this request. Request must not have gone through this step multiple
        # times.
        if completed_execution and execution.num_passes() == 1:
            execution.end_date = completed_execution.end_date

            try:
                execution.put()
            except Exception, e:
                logging.error(e)

            logging.warning('Step "%s" completed by "%s" on "%s". Exiting.' % \
                (execution.step.id, completed_execution.member,
                completed_execution.end_date))
            self.error(200)
            return None

        # If an action has been chosen, queue the next steps
        if execution.action and isinstance(execution.action, models.Action):
            logging.info('Action "%s" taken on Execution "%s".' % \
                (execution.action.name, execution.id))

            # If the action is a completion action
            if execution.action.is_complete:
                # If the request has not yet been marked as completed,
                # compute the request duration
                if not execution.request.is_completed:
                    try:
                        execution.request.set_completed()
                    except Exception, e:
                        logging.error('%s Re-queuing.' % e)
                        self.error(500)
                        return None

                # Record the request in the Process statistics
                logging.info('Queuing statistics collection for Request ' \
                    '"%s".' % execution.request.id)
                queue = taskqueue.Queue('request-statistics')
                task = taskqueue.Task(params={
                    'request_key': execution.request.id,
                    'process_key': execution.process.id
                })
                queue.add(task)

                logging.info('Queuing completed email to be sent to "%s" for ' \
                    'Request "%s".' % (execution.request.requestor,
                    execution.request.id))
                task = taskqueue.Task(params={'key': execution.id})
                queue = taskqueue.Queue('mail-request-complete')
                queue.add(task)

            # If the action didn't complete the process, queue a step
            # completion email to be sent to the requestor and queue up any
            # outgoing steps after this action.
            else:
                logging.info('Queuing step email to be sent to "%s".' % \
                    execution.request.requestor)
                task = taskqueue.Task(params={'key': execution.id})
                queue = taskqueue.Queue('mail-request-step')
                queue.add(task)

                for step_key in execution.action.outgoing:
                    step = models.Step.get(step_key)
                    if step and isinstance(step, models.Step):
                        step.queue_tasks(execution.request)

            logging.info('Completed Execution "%s". Exiting.' % execution.id)
            self.error(200)
            return None

        # Reached reminder limit, cancel this execution
        if execution.reminder_count == settings.REMINDER_LIMIT:
            logging.warning('Reminder limit reached for Execution "%s". ' \
                'Exiting.' % execution.id)
            self.error(200)
            return None

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
                logging.info('Queuing reminder email #%s to be sent "%s".' % \
                    (execution.reminder_count, execution.member))
                task = taskqueue.Task(params={'key': execution.id})
                queue = taskqueue.Queue('mail-request-reminder')
                queue.add(task)
            else:
                logging.info('Reminder #%s delay for Execution "%s" has not ' \
                    'expired (%s >= %s).' % (execution.reminder_count+1,
                    execution.id, num_seconds, settings.REMINDER_DELAY))

        logging.info('Re-queuing Execution "%s".' % execution.id)
        self.error(500)

        logging.debug('Finished request-process task handler')

def main():
    application = webapp.WSGIApplication([('/_ah/queue/request-process',
        TaskHandler)], debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
