#
# Copyright 2010 Flomosa, LLC
#

import logging
import email.utils

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util, mail_handlers


class MailHandler(mail_handlers.InboundMailHandler):
    def receive(self, message):
        logging.debug('Begin incoming mail handler')



        logging.debug('Finished incoming mail handler')

def main():
    application = webapp.WSGIApplication(
        [(r'/_ah/mail/support%40.*flomosa\.appspotmail\.com', MailHandler)],
        debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
