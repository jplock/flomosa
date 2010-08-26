#
# Copyright 2010 Flomosa, LLC
#

from datetime import datetime
import logging
import os.path

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util
from google.appengine.api import mail
from google.appengine.runtime import apiproxy_errors

from exceptions import MissingException, QuotaException, InternalException
import models
import settings
import queueapp


class TaskHandler(queueapp.QueueHandler):

    def post(self):
        logging.debug('Begin mail-request-reminder task handler')

        num_tries = self.request.headers['X-AppEngine-TaskRetryCount']
        logging.info('Task has been executed %s times' % num_tries)

        execution_key = self.request.get('key')
        if not execution_key:
            raise MissingException('Missing "key" parameter.')

        execution = models.Execution.get(execution_key)
        if not execution.member:
            raise InternalException('Execution "%s" has no email address.' % \
                execution.id)

        if isinstance(execution.action, models.Action):
            logging.warning('Action already taken on Execution "%s". ' \
                'Exiting.' % execution.id)
            return None

        request = execution.request

        directory = os.path.dirname(__file__)
        text_template_file = os.path.join(directory,
            'templates/email_notify_text.tpl')
        html_template_file = os.path.join(directory,
            'templates/email_notify_html.tpl')

        template_vars = {
            'execution_key': execution.id,
            'actions': execution.step.actions,
            'requestor': request.requestor,
            'request_key': request.id,
            'submitted_date': request.submitted_date,
            'request_data': request.get_submitted_data(),
            'step_name': execution.step.name
        }

        text_body = template.render(text_template_file, template_vars)
        html_body = template.render(html_template_file, template_vars)

        execution.reminder_count = execution.reminder_count + 1
        execution.last_reminder_sent_date = datetime.now()

        message = mail.EmailMessage()
        message.sender = 'Flomosa <reply+%s@%s>' % (execution.id,
            settings.EMAIL_DOMAIN)
        message.to = execution.member
        message.subject = '[flomosa] Request #%s (Reminder %s of %s)' % \
            (request.id, execution.reminder_count, settings.REMINDER_LIMIT)
        message.body = text_body
        message.html = html_body

        logging.info('Sending reminder email to "%s" for Execution "%s".' % \
            (execution.member, execution.id))
        try:
            message.send()
        except apiproxy_errors.OverQuotaError:
            raise QuotaException('Over email quota limit to send reminder ' \
                'email to "%s".' % execution.member)
        except:
            raise InternalException('Unable to send reminder email to "%s".' \
                % execution.member)

        execution.put()

        logging.debug('Finished mail-request-reminder task handler')

def main():
    application = webapp.WSGIApplication([('/_ah/queue/mail-request-reminder',
        TaskHandler)], debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
