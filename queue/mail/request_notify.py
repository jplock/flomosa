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
        logging.debug('Begin mail-request-notify task handler')

        num_tries = self.request.headers['X-AppEngine-TaskRetryCount']
        logging.info('Task has been executed %s times' % num_tries)

        execution_key = self.request.get('key')
        if not execution_key:
            raise MissingException('Missing "key" parameter.')

        execution = models.Execution.get(execution_key)
        if not execution.member:
            raise InternalException('Execution "%s" has no email address.' % \
                execution.id)

        if execution.sent_date:
            logging.warning('Execution "%s" notification already sent to ' \
                '"%s". Exiting.' % (execution.id, execution.member))
            return None

        request = execution.request
        step = execution.step

        directory = os.path.dirname(__file__)
        text_template_file = os.path.join(directory,
            'templates/email_notify_text.tpl')
        html_template_file = os.path.join(directory,
            'templates/email_notify_html.tpl')

        template_vars = {
            'execution_key': execution.id,
            'actions': step.actions,
            'requestor': request.requestor,
            'request_key': request.id,
            'submitted_date': request.submitted_date,
            'request_data': request.get_submitted_data(),
            'step_name': step.name,
            'url': settings.HTTP_URL
        }

        text_body = template.render(text_template_file, template_vars)
        html_body = template.render(html_template_file, template_vars)

        message = mail.EmailMessage()
        message.sender = 'Flomosa <reply+%s@%s>' % (execution.id,
            settings.EMAIL_DOMAIN)
        message.to = execution.member
        message.subject = '[flomosa] Request #%s' % request.id
        message.body = text_body
        message.html = html_body

        logging.info('Sending email to "%s" for Execution "%s".' % \
            (execution.member, execution.id))
        try:
            message.send()
        except apiproxy_errors.OverQuotaError:
            raise QuotaException('Over email quota limit to send notification ' \
                'email to "%s".' % execution.member)
        except:
            raise InternalException('Unable to send notification email to ' \
                '"%s".' % execution.member)

        execution.set_sent()

        logging.debug('Finished mail-request-notify task handler')

def main():
    application = webapp.WSGIApplication([('/_ah/queue/mail-request-notify',
        TaskHandler)], debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
