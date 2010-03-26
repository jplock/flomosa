#
# Copyright 2010 Flomosa, LLC
#

import os.path
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

        # If we have not sent the email notifications
        if not execution.queued_for_send:
            execution.queued_for_send = True

            try:
                execution.put()
            except Exception, e:
                logging.error(e)

            logging.info('Queuing notification email to be sent "%s".' % \
                execution.member)
            task = taskqueue.Task(params={'key': execution.id})
            queue = taskqueue.Queue('mail-request-notify')
            queue.add(task)

            logging.info('Re-queuing Execution "%s".' % execution.id)
            self.error(500)
            return None

        # If an action has been chosen, queue the next tasks
        if isinstance(execution.action, models.Action):
            logging.info('Action "%s" taken on Execution "%s".' % \
                (execution.action.name, execution.id))

            if execution.action.is_complete:
                logging.info('Queuing completed email to be sent to "%s".' % \
                    execution.request.requestor)
                task = taskqueue.Task(params={'key': execution.id})
                queue = taskqueue.Queue('mail-request-complete')
                queue.add(task)
            else:
                logging.info('Queuing step email to be sent to "%s".' % \
                    execution.request.requestor)
                task = taskqueue.Task(params={'key': execution.id})
                queue = taskqueue.Queue('mail-request-step')
                queue.add(task)

                for step_key in execution.action.outgoing:
                    step = models.Step.get(step_key)
                    if isinstance(step, models.Step):
                        step.queue_tasks(execution.request)

            logging.info('Completed Execution "%s". Exiting.' % execution.id)
            self.error(200)
            return None

        # Check that another team member or someone on a different team didn't
        # already complete this step for this request. Request must not have
        # gone through this step multiple times.
        completed_execution = execution.is_step_completed()
        if completed_execution and execution.num_passes() == 1:
            logging.info('Step "%s" completed by "%s" on "%s"' % \
                (execution.step.id, completed_execution.member,
                completed_execution.end_date))

            execution.end_date = completed_execution.end_date

            try:
                execution.put()
            except Exception, e:
                logging.warning('%s Exiting.' % e)
                self.error(200)
                return None

        # Reached reminder limit, cancel this execution
        elif execution.reminder_count == settings.REMINDER_LIMIT:
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
            if num_seconds >= settings.REMINDER_DELAY:
                logging.info('Queuing reminder email #%s to be sent "%s".' % \
                    (execution.reminder_count, execution.member))
                task = taskqueue.Task(params={'key': execution.id})
                queue = taskqueue.Queue('mail-request-reminder')
                queue.add(task)
            else:
                logging.info('Reminder #%s delay for Execution "%s" has not ' \
                    'expired (%s >= %s).' % (execution.reminder_count,
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
