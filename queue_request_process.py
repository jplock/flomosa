#!/usr/bin/env python
#
# Copyright 2010 Flomosa, LLC
#

import os.path
import logging
from datetime import datetime

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util
from google.appengine.api.labs import taskqueue
from google.appengine.api import mail
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

        logging.info('Looking up Execution "%s" in memcache then datastore.' % \
            execution_key)
        execution = utils.load_from_cache(execution_key, models.Execution)
        if not isinstance(execution, models.Execution):
            logging.error('Execution "%s" was not found. Exiting.' % \
                execution_key)
            return None

        if not isinstance(execution.step, models.Step):
            logging.error('Execution "%s" has no step defined. Exiting.' % \
                execution.id)
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
        if not execution.sent_date:
            directory = os.path.dirname(__file__)
            text_template_file = os.path.join(directory,
                'templates/email_notify_text.tpl')
            html_template_file = os.path.join(directory,
                'templates/email_notify_html.tpl')

            template_vars = {
                'execution_key': execution.id,
                'actions': execution.step.actions,
                'request_data': execution.request.to_dict()
            }

            text_body = template.render(text_template_file, template_vars)
            html_body = template.render(html_template_file, template_vars)

            message = mail.EmailMessage(
                sender='Flomosa &lt;reply+%s@flomosa.appspotmail.com&gt;' % \
                    execution.id,
                to=execution.member,
                subject='[flomosa] New request for your action',
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
                logging.error('Unable to save Execution "%s". Re-queuing.' % \
                    execution.id)
                self.error(500)
                return None

            logging.info('Storing Execution "%s" in memcache.' % execution.id)
            memcache.set(execution.id, execution)

        if not execution.viewed_date:
            pass

        if not execution.action:
            pass

        logging.debug('Finished request-process task handler')

def main():
    application = webapp.WSGIApplication([('/_ah/queue/request-process',
        TaskHandler)], debug=utils._DEBUG)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
