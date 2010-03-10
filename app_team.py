#!/usr/bin/env python
#
# Copyright 2010 Flomosa, LLC
#

import logging

from django.utils import simplejson
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp import util
from google.appengine.api import memcache

import models
import utils

class TeamHandler(webapp.RequestHandler):

    def get(self, team_key):
        logging.debug('Begin TeamHandler.get() function')

        team = utils.load_from_cache(team_key, models.Team)
        if not team:
            return utils.build_json(self,
                'Unable to find team with ID "%s"' % team_key, code=404)

        utils.build_json(self, team.to_dict())

        logging.debug('Finished TeamHandler.get() function')

    def put(self, team_key):
        logging.debug('Begin TeamHandler.put() function')

        try:
            data = simplejson.loads(self.request.body)
        except:
            return utils.build_json(self, 'Error parsing JSON request.',
                code=500)

        try:
            team = models.Team.from_dict(data)
        except Exception, e:
            return utils.build_json(self, e, code=400)

        try:
            team.put()
        except:
            return utils.build_json(self, 'Unable to save team.', code=500)

        memcache.set(team_key, team)

        utils.build_json(self, team.to_dict())

        logging.debug('Finished TeamHandler.put() function')

    def delete(self, team_key):
        logging.debug('Begin TeamHandler.delete() function')

        entities = []
        entity_keys = []

        team = models.Team.get_by_key_name(team_key)
        if team:
            entities.append(team)
            entity_keys.append(team_key)

        db.delete(entities)
        memcache.delete_multi(entity_keys)

        self.error(204)

        logging.debug('Finished TeamHandler.delete() function')

def main():
    application = webapp.WSGIApplication([(r'/teams/(.*)\.json', TeamHandler)],
        debug=utils._DEBUG)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
