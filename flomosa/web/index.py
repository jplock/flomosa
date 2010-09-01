#
# Copyright 2010 Flomosa, LLC
#

import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util

from flomosa import authapp, settings


class MainHandler(authapp.SecureRequestHandler):

    def get(self):
        logging.debug('Begin MainHandler.get() method')

        template_vars = {'uri': self.request.uri}
        client = self.get_current_client()
        if client:
            template_vars['current_client'] = client

        template_file = settings.TEMPLATE_DIR + '/index.tpl'
        output = template.render(template_file, template_vars)

        self.response.out.write(output)

        logging.debug('Finished MainHandler.get() method')

def main():
    application = webapp.WSGIApplication([('/', MainHandler)], debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
