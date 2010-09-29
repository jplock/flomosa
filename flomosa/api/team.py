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

from flomosa import models
from flomosa.api import OAuthHandler, build_json


class TeamHandler(OAuthHandler):

    def get(self, team_key=None):
        logging.debug('Begin TeamHandler.get() method')

        client = self.is_valid()
        team = models.Team.get(team_key, client)

        logging.info('Returning Team "%s" as JSON to client.' % team.id)
        build_json(self, team.to_dict())

        logging.debug('Finished TeamHandler.get() method')

    def put(self, team_key=None):
        logging.debug('Begin TeamHandler.put() method')

        client = self.is_valid()

        from django.utils import simplejson
        data = simplejson.loads(self.request.body)

        team = models.Team.from_dict(client, data)
        team.put()

        logging.info('Returning Team "%s" as JSON to client.' % team.id)
        build_json(self, team.to_dict(), 201)

        logging.debug('Finished TeamHandler.put() method')

    def delete(self, team_key=None):
        logging.debug('Begin TeamHandler.delete() method')

        client = self.is_valid()
        team = models.Team.get(team_key, client)
        team.delete()

        self.error(204)

        logging.debug('Finished TeamHandler.delete() method')


def main():
    application = webapp.WSGIApplication([
        (r'/teams/(.*)\.json', TeamHandler),
        (r'/teams/', TeamHandler)], debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
