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
        logging.debug('Begin mail-request-notify task handler')

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

        if execution.sent_date:
            logging.error('Execution "%s" notification already sent to "%s". ' \
                'Exiting.' % (execution.id, execution.member))
            return None

        directory = os.path.dirname(__file__)
        text_template_file = os.path.join(directory,
            'templates/email_notify_text.tpl')
        html_template_file = os.path.join(directory,
            'templates/email_notify_html.tpl')

        template_vars = {
            'execution_key': execution.id,
            'actions': execution.step.actions,
            'requestor': execution.request.requestor,
            'request_key': execution.request.id,
            'submitted_date': execution.request.submitted_date,
            'request_data': execution.request.get_submitted_data(),
            'step_name': execution.step.name
        }

        text_body = template.render(text_template_file, template_vars)
        html_body = template.render(html_template_file, template_vars)

        message = mail.EmailMessage()
        message.sender = 'Flomosa <reply+%s@%s>' % (execution.id,
            settings.EMAIL_DOMAIN)
        message.to = execution.member
        message.subject = '[flomosa] Request #%s' % execution.request.id
        message.body = text_body
        message.html = html_body

        logging.info('Sending email to "%s" for Execution "%s".' % \
            (execution.member, execution.id))
        try:
            message.send()
        except apiproxy_errors.OverQuotaError:
            logging.error('Over email quota limit to send notification ' \
                'email to "%s". Re-queuing.' % execution.member)
            self.error(500)
            return None
        except Exception, e:
            logging.error('Unable to send notification email to "%s" (%s). ' \
                'Re-queuing.' % (execution.member, e))
            self.error(500)
            return None

        execution.sent_date = datetime.now()

        try:
            execution.put()
        except Exception, e:
            logging.error(e)
            self.error(500)

        logging.debug('Finished mail-request-notify task handler')

def main():
    application = webapp.WSGIApplication([('/_ah/queue/mail-request-notify',
        TaskHandler)], debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
