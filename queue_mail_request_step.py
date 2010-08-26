#
# Copyright 2010 Flomosa, LLC
#

import os.path
import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util
from google.appengine.api import mail
from google.appengine.runtime import apiproxy_errors

from exceptions import MissingException, InternalException, QuotaException
import models
import settings
import queueapp


class TaskHandler(queueapp.QueueHandler):

    def post(self):
        logging.debug('Begin mail-request-step task handler')

        num_tries = self.request.headers['X-AppEngine-TaskRetryCount']
        logging.info('Task has been executed %s times' % num_tries)

        execution_key = self.request.get('key')
        if not execution_key:
            raise MissingException('Missing "key" parameter.')

        execution = models.Execution.get(execution_key)
        request = execution.request
        if not request.requestor:
            raise InternalException('Request "%s" has no email address.' % \
                execution.id)

        directory = os.path.dirname(__file__)
        text_template_file = os.path.join(directory,
            'templates/email_step_text.tpl')
        html_template_file = os.path.join(directory,
            'templates/email_step_html.tpl')

        template_vars = {
            'step_name': execution.step.name,
            'process_name': execution.process.name,
            'requestor': request.requestor,
            'request_key': request.id,
            'submitted_date': request.submitted_date,
            'request_data': request.get_submitted_data(),
            'action_name': execution.action.name
        }

        text_body = template.render(text_template_file, template_vars)
        html_body = template.render(html_template_file, template_vars)

        message = mail.EmailMessage()
        message.sender = 'Flomosa <%s>' % settings.FEEDBACK_FORWARDER_EMAIL
        message.to = request.requestor
        message.subject = '[flomosa] Request #%s' % request.id
        message.body = text_body
        message.html = html_body

        logging.info('Sending step email to "%s".' % request.requestor)
        try:
            message.send()
        except apiproxy_errors.OverQuotaError:
            raise QuotaException('Over email quota limit to send step email ' \
                'to "%s". Re-queuing.' % request.requestor)
        except Exception:
            raise InternalException('Unable to send step email to "%s". ' \
                'Re-queuing.' % request.requestor)

        logging.debug('Finished mail-request-step task handler')

def main():
    application = webapp.WSGIApplication([('/_ah/queue/mail-request-step',
        TaskHandler)], debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
