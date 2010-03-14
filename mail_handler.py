#!/usr/bin/env python
#
# Copyright 2010 Flomosa, LLC
#

import logging
import email.utils
from datetime import datetime

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util, mail_handlers
from google.appengine.api import memcache
from google.appengine.api.labs import taskqueue
from google.appengine.runtime import apiproxy_errors

import models
import utils

class MailHandler(mail_handlers.InboundMailHandler):
    def receive(self, message):
        logging.debug('Begin incoming mail handler')

        user, hostname = message.to.split('@')
        temp, execution_key = user.split('+')

        logging.info('Looking up Execution "%s" in memcache then datastore.' % \
            execution_key)
        execution = utils.load_from_cache(execution_key, models.Execution)
        if not isinstance(execution, models.Execution):
            logging.error('Execution "%s" not found in datastore. Exiting.' % \
                execution_key)
            return None

        if isinstance(execution.action, models.Action):
            logging.error('Action "%s" already taken on Execution "%s". ' \
                'Exiting.' % (execution.action.name, execution.id))
            return None

        if not isinstance(execution.process, models.Process):
            logging.error('Execution "%s" does not have a process defined. ' \
                'Exiting.' % execution.id)
            return None

        if not isinstance(execution.step, models.Step):
            logging.error('Execution "%s" does not have a step defined. ' \
                'Exiting.' % execution.id)
            return None

        if not isinstance(execution.request, models.Request):
            logging.error('Execution "%s" does not have a request defined. ' \
                'Exiting.' % execution.id)
            return None

        sender = email.utils.parseaddr(message.sender)
        sender = sender[1].lower()

        if execution.member.lower() != sender:
            logging.error('Email sent from "%s", expected "%s". Exiting.' % \
                (sender, execution.member))
            return None

        lines = []

        actions = {}
        executed_action = None
        for action in execution.step.actions:
            actions[action.name.lower()] = action

        for content_type, body in message.bodies('text/plain'):
            for line in body.decode().splitlines():
                for name, action in actions.iteritems():
                    if line.lower().find(name) != -1:
                        executed_action = action
                        break
                if isinstance(executed_action, models.Action) or \
                    line.find('ABOVE THIS LINE') != -1:
                    break
                lines.append(line)

        reply_text = "\n".join(lines).strip().lower()

        logging.info('Parsed reply "%s" from email.' % reply_text)

        if not isinstance(executed_action, models.Action):
            logging.error('Could not locate action named "%s". Exiting.' % \
                reply_text)
            return None

        execution.action = executed_action
        execution.end_date = datetime.now()

        logging.info('Storing Execution "%s" in datastore.' % execution.id)
        try:
            execution.put()
        except apiproxy_errors.CapabilityDisabledError:
            logging.error('Unable to save Execution "%s" due to maintenance.' \
                ' Exiting.' % execution.id)
            return None
        except:
            logging.error('Unable to save Execution "%s". Exiting.' % \
                execution.id)
            return None

        if execution.is_saved():
            logging.info('Storing Execution "%s" in memcache.' % execution.id)
            memcache.set(execution.id, execution)

        logging.debug('Finished incoming mail handler')

def main():
    application = webapp.WSGIApplication([(r'/_ah/mail/.+',
        MailHandler)], debug=utils._DEBUG)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
