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
        logging.debug('Begin mail-request-notify task handler')

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
            'request_data': execution.request.to_dict(),
            'step_name': execution.step.name
        }

        text_body = template.render(text_template_file, template_vars)
        html_body = template.render(html_template_file, template_vars)

        message = mail.EmailMessage(
            sender='Flomosa <reply+%s@flomosa.appspotmail.com>' % \
                execution.id,
            to=execution.member,
            subject='[flomosa] New Request for your Action',
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

        execution.sent_date = datetime.now()

        try:
            execution.put()
        except apiproxy_errors.CapabilityDisabledError:
            logging.error('Unable to save Execution "%s" due to ' \
                'maintenance. Re-queuing.' % execution.id)
            self.error(500)
            return None
        except:
            logging.error('Unable to save Execution "%s" in datastore.' % \
                execution.id)
            self.error(500)
            return None

        logging.debug('Finished mail-request-notify task handler')

def main():
    application = webapp.WSGIApplication([('/_ah/queue/mail-request-notify',
        TaskHandler)], debug=utils._DEBUG)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()