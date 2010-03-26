#!/usr/bin/env python
#
# Copyright 2010 Flomosa, LLC
#

import os.path
import logging
from datetime import datetime

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util
from google.appengine.api import mail
from google.appengine.runtime import apiproxy_errors

import models
import settings


class TaskHandler(webapp.RequestHandler):
    def post(self):
        logging.debug('Begin mail-request-reminder task handler')

        num_tries = self.request.headers['X-AppEngine-TaskRetryCount']
        logging.info('Task has been executed %s times' % num_tries)

        execution_key = self.request.get('key')
        if not execution_key:
            logging.error('Missing "key" parameter. Exiting.')
            return None

        logging.debug('Looking up Execution "%s" in datastore.' % execution_key)
        execution = models.Execution.get(execution_key)
        if not execution:
            logging.error('Execution "%s" not found in datastore. Exiting.' % \
                execution_key)
            return None

        if not execution.member:
            logging.error('Execution "%s" has no email address. Exiting.' % \
                execution.id)
            return None

        if isinstance(execution.action, models.Action):
            logging.warning('Action already taken on Execution "%s". ' \
                'Exiting.' % execution.id)
            return None

        directory = os.path.dirname(__file__)
        text_template_file = os.path.join(directory,
            'templates/email_notify_text.tpl')
        html_template_file = os.path.join(directory,
            'templates/email_notify_html.tpl')

        template_vars = {
            'execution_key': execution.id,
            'actions': execution.step.actions,
            'request_data': execution.request.to_dict(),
            'step_name': execution.step.name
        }

        text_body = template.render(text_template_file, template_vars)
        html_body = template.render(html_template_file, template_vars)

        execution.reminder_count = execution.reminder_count + 1
        execution.last_reminder_sent_date = datetime.now()

        message = mail.EmailMessage(
            sender='Flomosa <reply+%s@flomosa.appspotmail.com>' % \
                execution.id,
            to=execution.member,
            subject='[flomosa] Request #%s (Reminder %s of %s)' % \
                (execution.request.id, execution.reminder_count,
                settings.REMINDER_LIMIT),
            body=text_body,
            html=html_body)

        logging.info('Sending reminder email to "%s" for Execution "%s".' % \
            (execution.member, execution.id))
        try:
            message.send()
        except apiproxy_errors.OverQuotaError:
            logging.error('Over email quota limit to send reminder email to ' \
                '"%s". Re-queuing.' % execution.member)
            self.error(500)
            return None
        except Exception, e:
            logging.error('Unable to send reminder email to "%s" (%s). ' \
                'Re-queuing.' % (execution.member, e))
            self.error(500)
            return None

        try:
            execution.put()
        except Exception, e:
            logging.error(e)
            self.error(500)

        logging.debug('Finished mail-request-reminder task handler')

def main():
    application = webapp.WSGIApplication([('/_ah/queue/mail-request-reminder',
        TaskHandler)], debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
