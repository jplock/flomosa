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
import utils

class TaskHandler(webapp.RequestHandler):
    def post(self):
        logging.debug('Begin mail-request-confirmation task handler')

        num_tries = self.request.headers['X-AppEngine-TaskRetryCount']
        logging.info('Task has been executed %s times' % num_tries)

        execution_key = self.request.get('key')
        if not execution_key:
            logging.error('Missing "key" parameter. Exiting.')
            return None

        logging.info('Looking up Execution "%s" in datastore.' % execution_key)
        execution = models.Execution.get_by_key_name(execution_key)
        if not execution:
            logging.error('Execution "%s" not found in datastore. Exiting.' % \
                execution_key)
            return None

        if not execution.member:
            logging.error('Execution "%s" has no email address. Exiting.' % \
                execution.id)
            return None

        directory = os.path.dirname(__file__)
        text_template_file = os.path.join(directory,
            'templates/email_confirmation_text.tpl')
        html_template_file = os.path.join(directory,
            'templates/email_confirmation_html.tpl')

        template_vars = {
            'action_name': execution.action.name,
            'request_data': execution.request.to_dict(),
            'step_name': execution.step.name
        }

        text_body = template.render(text_template_file, template_vars)
        html_body = template.render(html_template_file, template_vars)

        message = mail.EmailMessage(
            sender='Flomosa <no-reply@flomosa.com>',
            to=execution.member,
            subject='[flomosa] Action Confirmed: %s' % execution.action.name,
            body=text_body,
            html=html_body)

        try:
            message.send()
        except apiproxy_errors.OverQuotaError:
            logging.error('Over email quota limit to send notification ' \
                'email to "%s". Re-queuing.' % execution.member)
            self.error(500)
            return None
        except:
            logging.error('Unable to send notification email to "%s". ' \
                'Re-queuing.' % execution.member)
            self.error(500)
            return None

        logging.debug('Finished mail-request-confirmation task handler')

def main():
    application = webapp.WSGIApplication(
        [('/_ah/queue/mail-request-confirmation', TaskHandler)],
        debug=utils._DEBUG)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
