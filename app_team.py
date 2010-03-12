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

        logging.info('Looking up Team key "%s" in memcache then datastore.' \
            % team_key)
        team = utils.load_from_cache(team_key, models.Team)
        if not team:
            error_msg = 'Team key "%s" not found.' % team_key
            logging.error(utils.get_log_message(error_msg, 404))
            return utils.build_json(self, error_msg, 404)

        logging.info('Returning Team "%s" as JSON to client.' % team.id)
        utils.build_json(self, team.to_dict())

        logging.debug('Finished TeamHandler.get() function')

    def put(self, team_key):
        logging.debug('Begin TeamHandler.put() function')

        try:
            data = simplejson.loads(self.request.body)
        except:
            error_msg = 'Error parsing JSON request.'
            logging.error(utils.get_log_message(error_msg, 500))
            return utils.build_json(self, error_msg, 500)

        try:
            team = models.Team.from_dict(data)
        except Exception, e:
            logging.error(utils.get_log_message(e, 400))
            return utils.build_json(self, e, 400)

        if team_key != team.id:
            logging.warning('Passed Team key "%s" does not match found Team ' \
                'key "%s".' % (team_key, team.id))

        logging.info('Storing Team "%s" in datastore.' % team.id)
        try:
            team.put()
        except:
            error_msg = 'Unable to store team.'
            logging.error(utils.get_log_message(error_msg, 500))
            return utils.build_json(self, error_msg, code=500)

        logging.info('Storing Team "%s" in memcache.' % team.id)
        memcache.set(team.id, team)

        utils.build_json(self, team.to_dict())

        logging.debug('Finished TeamHandler.put() function')

    def delete(self, team_key):
        logging.debug('Begin TeamHandler.delete() function')

        team = models.Team.get_by_key_name(team_key)
        if team:
            logging.info('Deleting Team "%s" from datastore.' % team.id)
            db.delete(team)
            logging.info('Deleting Team "%s" from memcache.' % team.id)
            memcache.delete_multi([team.id, team_key])
        else:
            logging.warning('Team key "%s" not found in datastore to ' \
                'delete.' % team_key)

        self.error(204)

        logging.debug('Finished TeamHandler.delete() function')

def main():
    application = webapp.WSGIApplication([(r'/teams/(.*)\.json', TeamHandler)],
        debug=utils._DEBUG)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
