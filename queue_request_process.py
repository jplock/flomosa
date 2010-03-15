#!/usr/bin/env python
#
# Copyright 2010 Flomosa, LLC
#

import os.path
import logging
from datetime import datetime

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api.labs import taskqueue
from google.appengine.runtime import apiproxy_errors

import models
import utils

class TaskHandler(webapp.RequestHandler):
    def post(self):
        logging.debug('Begin request-process task handler')

        num_tries = self.request.headers['X-AppEngine-TaskRetryCount']
        logging.info('Task has been executed %s times' % num_tries)

        execution_key = self.request.get('key')
        if not execution_key:
            logging.error('Missing "key" parameter. Exiting.')
            return None

        logging.info('Looking up Execution "%s" in datastore.' % execution_key)
        execution = models.Execution.get_by_key_name(execution_key)
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
            logging.info('Queuing notification email to be sent "%s".' % \
                execution.member)
            task = taskqueue.Task(params={'key': execution.id})
            queue = taskqueue.Queue('mail-request-notify')
            queue.add(task)

            execution.queued_for_send = True

            try:
                execution.put()
            except apiproxy_errors.CapabilityDisabledError:
                logging.error('Unable to save Execution "%s" due to ' \
                    'maintenance.' % execution.id)
            except:
                logging.error('Unable to save Execution "%s" in datastore.' % \
                    execution.id)

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
                for step_key in execution.action.outgoing:
                    step = utils.load_from_cache(step_key, models.Step)
                    if isinstance(step, models.Step):
                        step.queue_tasks(execution.request)
            logging.info('Completed Execution "%s". Exiting.' % execution.id)
        else:
            logging.info('Re-queuing Execution "%s".' % execution.id)
            self.error(500)

        logging.debug('Finished request-process task handler')

def main():
    application = webapp.WSGIApplication([('/_ah/queue/request-process',
        TaskHandler)], debug=utils._DEBUG)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
