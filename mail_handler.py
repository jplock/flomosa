#
# Copyright 2010 Flomosa, LLC
#

import logging
import email.utils
from datetime import datetime

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util, mail_handlers
from google.appengine.api.labs import taskqueue

import models

class MailHandler(mail_handlers.InboundMailHandler):
    def receive(self, message):
        logging.debug('Begin incoming mail handler')

        realname, recipient = email.utils.parseaddr(message.to)
        if not recipient:
            logging.error('Invalid reply user "%s". Exiting.' % recipient)
            return None

        user, hostname = recipient.split('@')
        if not user.startswith('reply+'):
            logging.error('Invalid reply user "%s". Exiting.' % user)
            return None

        temp, execution_key = user.split('+')

        execution = models.Execution.get(execution_key)

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

        realname, sender = email.utils.parseaddr(message.sender)

        if execution.member.lower() != sender.lower():
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
                        logging.info('Found Action named "%s" for Execution ' \
                            '"%s".' % (action.name, execution.id))
                        executed_action = action
                        break
                if isinstance(executed_action, models.Action) or \
                    line.find('ABOVE THIS LINE') != -1:
                    break
                lines.append(line)

        reply_text = "\n".join(lines).strip().lower()

        logging.info('Parsed reply "%s" from email.' % reply_text)

        if not isinstance(executed_action, models.Action):
            raise InternalException('Could not locate action named "%s". ' \
                'Exiting.' % executed_action)

        execution.set_completed(executed_action)
        
        logging.info('Queuing confirmation email to be sent to "%s".' % \
            execution.member)
        task = taskqueue.Task(params={'key': execution.id})
        queue = taskqueue.Queue('mail-request-confirmation')
        queue.add(task)

        logging.debug('Finished incoming mail handler')

def main():
    application = webapp.WSGIApplication([MailHandler.mapping()], debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
