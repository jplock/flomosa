#
# Copyright 2010 Flomosa, LLC
#

import logging
import email.utils

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util, mail_handlers
from google.appengine.api import mail
from google.appengine.runtime import apiproxy_errors


class MailHandler(mail_handlers.InboundMailHandler):
    def receive(self, inbound_message):
        logging.debug('Begin feedback@ incoming mail handler')

        text_body = []
        for content_type, body in inbound_message.bodies('text/plain'):
            text_body.append(body)

        html_body = []
        for content_type, body in inbound_message.bodies('text/html'):
            html_body.append(body.decode())

        recipient = 'feedback@flomosa.com'

        message = mail.EmailMessage(
            sender=inbound_message.sender,
            to='Feedback <%s>' % recipient,
            subject=inbound_message.subject,
            body="\n".join(text_body),
            html="\n".join(html_body))

        logging.info('Forwarding feedback email to "%s".' % recipient)
        try:
            message.send()
        except apiproxy_errors.OverQuotaError:
            logging.error('Over email quota limit to forward feedback email ' \
                'to "%s".' % recipient)
        except Exception, e:
            logging.error('Unable to forward feedback email to "%s" (%s). ' % \
                (recipient, e))

        logging.debug('Finished feedback@ incoming mail handler')

def main():
    application = webapp.WSGIApplication([MailHandler.mapping()], debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
