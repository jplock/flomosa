#!/usr/bin/env python
#
# Copyright 2010 Flomosa, LLC
#

import logging

from django.utils import simplejson
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp import util
from google.appengine.api import memcache
from google.appengine.runtime import apiproxy_errors

import models
import utils


class TeamHandler(webapp.RequestHandler):

    def get(self, team_key):
        logging.debug('Begin TeamHandler.get() function')

        logging.info('Looking up Team "%s" in memcache then datastore.' % \
            team_key)
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

        if not isinstance(team, models.Team):
            error_msg = 'Unable to create Team "%s".' % team_key
            logging.error(utils.get_log_message(error_msg, 500))
            return utils.build_json(self, error_msg, 500)

        logging.info('Storing Team "%s" in datastore.' % team.id)
        try:
            team.put()
        except apiproxy_errors.CapabilityDisabledError:
            error_msg = 'Unable to save Team "%s" due to maintenance. ' % \
                team.id
            logging.error(utils.get_log_message(error_msg, 500))
            return utils.build_json(self, error_msg, code=500)
        except:
            error_msg = 'Unable to save Team "%s" in datastore.' % team.id
            logging.error(utils.get_log_message(error_msg, 500))
            return utils.build_json(self, error_msg, code=500)

        logging.info('Storing Team "%s" in memcache.' % team.id)
        memcache.set(team.id, team)

        logging.info('Returning Team "%s" as JSON to client.' % team.id)
        utils.build_json(self, team.to_dict(), 201)

        logging.debug('Finished TeamHandler.put() function')

    def delete(self, team_key):
        logging.debug('Begin TeamHandler.delete() function')

        key = db.Key.from_path('Team', team_key)

        logging.info('Deleting Team "%s" from datastore.' % team_key)
        try:
            db.delete(key)
        except apiproxy_errors.CapabilityDisabledError:
            logging.warning('Unable to delete Team "%s" due to ' \
                'maintenance.' % team_key)

        logging.info('Deleting Team "%s" from memcache.' % team_key)
        memcache.delete(team_key)

        self.error(204)

        logging.debug('Finished TeamHandler.delete() function')

def main():
    application = webapp.WSGIApplication([(r'/teams/(.*)\.json', TeamHandler)],
        debug=utils._DEBUG)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
