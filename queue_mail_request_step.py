#
# Copyright 2010 Flomosa, LLC
#

import os.path
import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util
from google.appengine.api import mail
from google.appengine.runtime import apiproxy_errors

import models
import settings


class TaskHandler(webapp.RequestHandler):
    def post(self):
        logging.debug('Begin mail-request-step task handler')

        num_tries = self.request.headers['X-AppEngine-TaskRetryCount']
        logging.info('Task has been executed %s times' % num_tries)

        execution_key = self.request.get('key')
        if not execution_key:
            logging.error('Missing "key" parameter. Exiting.')
            return None

        logging.info('Looking up Execution "%s" in datastore.' % execution_key)
        execution = models.Execution.get(execution_key)
        if not execution:
            logging.error('Execution "%s" not found in datastore. Exiting.' % \
                execution_key)
            return None

        if not execution.request.requestor:
            logging.error('Request "%s" has no email address. Exiting.' % \
                execution.id)
            return None

        directory = os.path.dirname(__file__)
        text_template_file = os.path.join(directory,
            'templates/email_step_text.tpl')
        html_template_file = os.path.join(directory,
            'templates/email_step_html.tpl')

        template_vars = {
            'step_name': execution.step.name,
            'process_name': execution.process.name,
            'requestor': execution.request.requestor,
            'request_key': execution.request.id,
            'submitted_date': execution.request.submitted_date,
            'request_data': execution.request.get_submitted_data(),
            'action_name': execution.action.name
        }

        text_body = template.render(text_template_file, template_vars)
        html_body = template.render(html_template_file, template_vars)

        message = mail.EmailMessage()
        message.sender = 'Flomosa <%s>' % settings.FEEDBACK_FORWARDER_EMAIL
        message.to = execution.request.requestor
        message.subject = '[flomosa] Request #%s' % execution.request.id
        message.body = text_body
        message.html = html_body

        logging.info('Sending step email to "%s".' % \
            execution.request.requestor)
        try:
            message.send()
        except apiproxy_errors.OverQuotaError:
            logging.error('Over email quota limit to send step email to ' \
                '"%s". Re-queuing.' % execution.request.requestor)
            self.error(500)
        except Exception, e:
            logging.error('Unable to send step email to "%s" (%s). ' \
                'Re-queuing.' % (execution.request.requestor, e))
            self.error(500)

        logging.debug('Finished mail-request-step task handler')

def main():
    application = webapp.WSGIApplication([('/_ah/queue/mail-request-step',
        TaskHandler)], debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
