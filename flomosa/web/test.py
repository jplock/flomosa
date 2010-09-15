# -*- coding: utf8 -*-
#
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2010 Flomosa, LLC
# All Rights Reserved.
#

import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

from flomosa import authapp, models


# test@flomosa.com
KEY = '4ef3e685-37c1-43f9-ae03-0a21523051c6'
SECRET = '1913b245-18ae-4caa-a491-cedd2e471a50'


class TestHandler(authapp.SecureRequestHandler):

    def get(self):
        logging.debug('Begin TestHandler.get() method')

        client = models.Client(key_name=KEY,
            email_address='test@flomosa.com',
            password=self.encrypt_string('test'))
        client.first_name = 'Test'
        client.last_name = 'Test'
        client.company = 'Flomosa'
        client.oauth_secret = SECRET

        client.put()
        self.response.out.write('Test account created')

        logging.debug('Finished TestHandler.get() method')

def main():
    application = webapp.WSGIApplication([(r'/tests/client', TestHandler)],
        debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
