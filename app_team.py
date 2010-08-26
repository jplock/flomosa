#
# Copyright 2010 Flomosa, LLC
#

import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

from exceptions import UnauthorizedException
import models
import utils
import oauthapp


class TeamHandler(oauthapp.OAuthHandler):

    def get(self, team_key):
        logging.debug('Begin TeamHandler.get() method')

        client = self.is_valid()

        team = models.Team.get(team_key)
        if team.client.id != client.id:
            raise UnauthorizedException('Client "%s" is not authorized to ' \
                'access Team "%s".' % (client.id, team.id))
            error_msg = 'Permission denied.'

        logging.info('Returning Team "%s" as JSON to client.' % team.id)
        utils.build_json(self, team.to_dict())

        logging.debug('Finished TeamHandler.get() method')

    def put(self, team_key):
        logging.debug('Begin TeamHandler.put() method')

        client = self.is_valid()

        from django.utils import simplejson
        data = simplejson.loads(self.request.body)

        team = models.Team.from_dict(client, data)
        if not isinstance(team, models.Team):
            raise Exception('Unable to create Team "%s".' % team_key)

        team.put()

        logging.info('Returning Team "%s" as JSON to client.' % team.id)
        utils.build_json(self, team.to_dict(), 201)

        logging.debug('Finished TeamHandler.put() method')

    def delete(self, team_key):
        logging.debug('Begin TeamHandler.delete() method')

        client = self.is_valid()

        team = models.Team.get_by_key_name(team_key)
        if isinstance(team, models.Team):
            if team.client.id != client.id:
                raise UnauthorizedException('Client "%s" is not authorized to ' \
                    'access Team "%s".' % (client.id, team.id))
            else:
                team.delete()
        else:
            logging.info('Team "%s" not found in datastore to delete.' % \
                team_key)

        self.error(204)

        logging.debug('Finished TeamHandler.delete() method')

def main():
    application = webapp.WSGIApplication([(r'/teams/(.*)\.json', TeamHandler)],
        debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
