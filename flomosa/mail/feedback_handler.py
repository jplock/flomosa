#!/usr/bin/env python2.5
# -*- coding: utf8 -*-
#
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2010 Flomosa, LLC
# All Rights Reserved.
#

import logging
import email.utils

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util, mail_handlers
from google.appengine.api import mail
from google.appengine.runtime import apiproxy_errors

from flomosa import exceptions, settings


class MailHandler(mail_handlers.InboundMailHandler):
    """Handles forwarding mail send to the feedback email address."""

    def receive(self, inbound_message):
        logging.debug('Begin feedback@ incoming mail handler')

        text_body = []
        for content_type, body in inbound_message.bodies('text/plain'):
            text_body.append(body.decode())

        html_body = []
        for content_type, body in inbound_message.bodies('text/html'):
            html_body.append(body.decode())

        message = mail.EmailMessage()
        message.to = settings.FEEDBACK_EMAIL
        message.sender = 'Feedback Forwarder <%s>' % \
            settings.FEEDBACK_FORWARDER_EMAIL

        realname, sender = email.utils.parseaddr(inbound_message.sender)

        if realname and sender:
            subject = '%s (From: "%s" <%s>)' % (inbound_message.subject,
                realname, sender)
        elif sender:
            subject = '%s (From: %s)' % (inbound_message.subject, sender)
        else:
            subject = inbound_message.subject

        message.subject = subject

        if text_body:
            message.body = "\n".join(text_body)
        if html_body:
            message.html = "\n".join(html_body)

        logging.info('Forwarding feedback email to "%s".',
                     settings.FEEDBACK_EMAIL)
        try:
            message.send()
        except apiproxy_errors.OverQuotaError:
            raise exceptions.QuotaException('Over email quota limit to ' \
                'forward feedback email to "%s".' % settings.FEEDBACK_EMAIL)
        except Exception, ex:
            raise exceptions.InternalException('Unable to forward feedback ' \
                'email to "%s" (%s). ' % (settings.FEEDBACK_EMAIL, ex))

        logging.debug('Finished feedback@ incoming mail handler')


def main():
    """Handles forwarding mail send to the feedback email address."""
    application = webapp.WSGIApplication([MailHandler.mapping()], debug=False)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
