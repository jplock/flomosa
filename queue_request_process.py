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

import models
import utils

class TaskHandler(webapp.RequestHandler):
    def post(self):
        logging.debug('Begin request-process task handler')

        num_tries = self.request.headers['X-AppEngine-TaskRetryCount']
        logging.info('Task has been executed %s times' % num_tries)

        execution_key = self.request.get('execution_key')
        if not execution_key:
            logging.error('Missing "execution_key" parameter. Exiting.')
            return None

        execution = utils.load_from_cache(execution_key, models.Execution)
        if not execution:
            logging.error('Execution "%s" was not found. Exiting.' % \
                execution_key)
            return None

        if not execution.step.actions:
            logging.error('No actions found for Step "%s". Exiting.' % \
                execution.step.id)
            return None

        # If we have not send the notification email yet
        if not execution.sent_date:
            directory = os.path.dirname(__file__)
            text_template_file = os.path.join(directory,
                'templates/email_notify_text.tpl')
            html_template_file = os.path.join(directory,
                'templates/email_notify_html.tpl')

            template_vars = {'execution_key': execution_key,
                'actions': execution.step.actions,
                'request_data': execution.request.to_dict()}

            text_body = template.render(text_template_file, template_vars)
            html_body = template.render(html_template_file, template_vars)

            message = mail.EmailMessage(
                sender='Flomosa &lt;reply+%s@flomosa.appspotmail.com&gt;' % \
                    execution_key,
                to=execution.member,
                subject='[flomosa] New request for your action',
                body=text_body, html=html_body)

            try:
                message.send()
            except:
                self.error(500)
                logging.error('Unable to send notification email to "%s". ' \
                    'Re-queuing.' % execution.member)
                return None

            execution.sent_date = datetime.now()

            try:
                execution.put()
            except:
                self.error(500)
                logging.error('Unable to save execution "%s". Re-queuing.' % \
                    execution_key)
                return None

            memcache.set(execution_key, execution)

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
