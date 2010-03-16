#
# Copyright 2010 Flomosa, LLC
#

import logging

from django.utils import simplejson
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

import models
import utils
import cache


class TeamHandler(webapp.RequestHandler):

    def get(self, team_key):
        logging.debug('Begin TeamHandler.get() method')

        logging.debug('Looking up Team "%s" in memcache then datastore.' % \
            team_key)
        team = models.Team.get(team_key)
        if not team:
            error_msg = 'Team key "%s" not found.' % team_key
            logging.error(utils.get_log_message(error_msg, 404))
            return utils.build_json(self, error_msg, 404)

        logging.info('Returning Team "%s" as JSON to client.' % team.id)
        utils.build_json(self, team.to_dict())

        logging.debug('Finished TeamHandler.get() method')

    def put(self, team_key):
        logging.debug('Begin TeamHandler.put() method')

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

        try:
            team.put()
        except Exception, e:
            logging.error(utils.get_log_message(e, 500))
            return utils.build_json(self, e, code=500)

        logging.info('Returning Team "%s" as JSON to client.' % team.id)
        utils.build_json(self, team.to_dict(), 201)

        logging.debug('Finished TeamHandler.put() method')

    def delete(self, team_key):
        logging.debug('Begin TeamHandler.delete() method')

        cache.delete_from_cache(kind='Team', key=team_key)
        self.error(204)

        logging.debug('Finished TeamHandler.delete() method')

def main():
    application = webapp.WSGIApplication([(r'/teams/(.*)\.json', TeamHandler)],
        debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
