#!/usr/bin/env python
#
# Copyright 2010 Flomosa, LLC
#

import logging

from django.utils import simplejson
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp import util
from google.appengine.api import memcache
from google.appengine.api.labs import taskqueue
from google.appengine.runtime import apiproxy_errors

import models
import utils

_EXECUTION_QUERY = db.GqlQuery("SELECT __key__ FROM Execution " \
    "WHERE process = :process AND request = :request AND step = :step " \
    "AND team = :team AND member = :member LIMIT 1")

class RequestHandler(webapp.RequestHandler):

    def get(self, request_key):
        logging.debug('Begin RequestHandler.get() function')

        logging.info('Looking up Request key "%s" in memcache then datastore.' \
            % request_key)
        request = utils.load_from_cache(request_key, models.Request)
        if not request:
            error_msg = 'Request key "%s" does not exist.' % request_key
            logging.error(utils.get_log_message(error_msg, 404))
            return utils.build_json(self, error_msg, 404)

        utils.build_json(self, request.to_dict())

        logging.debug('Finished RequestHandler.get() function')

    def post(self, request_key):
        logging.debug('Begin RequestHandler.post() function')

        try:
            data = simplejson.loads(self.request.body)
        except:
            error_msg = 'Error parsing JSON request.'
            logging.error(utils.get_log_message(error_msg, 500))
            return utils.build_json(self, error_msg, 500)

        process_key = data.get('process', None)
        if not process_key:
            error_msg = 'Missing "process" parameter.'
            logging.error(utils.get_log_message(error_msg, 400))
            return utils.build_json(self, error_msg, 400)

        process = utils.load_from_cache(process_key, models.Process)
        if not process:
            error_msg = 'Process "%s" does not exist.' % process_key
            logging.error(utils.get_log_message(error_msg, 404))
            return utils.build_json(self, error_msg, 404)

        if not process.is_valid():
            error_msg = 'Process "%s" is not valid.' % process_key
            logging.error(utils.get_log_message(error_msg, 500))
            return utils.build_json(self, error_msg, 500)

        requestor = data.get('requestor', None)
        if not requestor:
            error_msg = 'Missing "requestor" parameter.'
            logging.error(utils.get_log_message(error_msg, 400))
            return utils.build_json(self, error_msg, 400)

        request = utils.load_from_cache(request_key, models.Request)
        if request:
            error_msg = 'Request "%s" already exists.' % request_key
            logging.error(utils.get_log_message(error_msg, 500))
            return utils.build_json(self, error_msg, 500)
        else:
            request = models.Request(key_name=request_key, process=process,
                requestor=requestor)

        for key, value in data:
            if not hasattr(request, key):
                setattr(request, key, value)

        logging.info('Storing Request "%s" in datastore.' % request.id)
        try:
            request.put()
        except apiproxy_errors.CapabilityDisabledError:
            error_msg = 'Unable to save Request key "%s" due to maintenance.' \
                % request.id
            logging.error(utils.get_log_message(error_msg, 500))
            return utils.build_json(self, error_msg, 500)
        except:
            error_msg = 'Unable to save Request key "%s" in datastore.' % \
                request.id
            logging.error(utils.get_log_message(error_msg, 500))
            return utils.build_json(self, error_msg, 500)

        logging.info('Storing Request "%s" in memcache.' % request.id)
        memcache.set(request_key, request)

        step = process.get_start_step()

        queue = taskqueue.Queue('request-process')
        for team_key in step.teams:
            team = utils.load_from_cache(team_key, models.Team)
            if not team:
                continue

            for member in team.members:
                _EXECUTION_QUERY.bind(process=process, request=request,
                    step=step, team=team, member=member)

                execution_key = _EXECUTION_QUERY.get()
                if execution_key:
                    logging.info('Execution "%s" previously queued for ' \
                        '"%s".' % (execution_key.name(), member))
                    continue

                execution_key = utils.generate_key()
                execution = models.Execution(key_name=execution_key,
                    process=process, request=request, step=step, team=team,
                    member=member)

                logging.info('Storing Execution "%s" in datastore.' % \
                    execution.id)
                try:
                    execution.put()
                except apiproxy_errors.CapabilityDisabledError:
                    logging.error('Unable to save Execution "%s" due to ' \
                        'maintenance.' % execution.id)
                    continue
                except:
                    logging.error('Unable to save Execution "%s" in ' \
                        'datastore.' % execution.id)
                    continue

                logging.info('Storing Execution "%s" in memcache.' % \
                    execution.id)
                memcache.set(execution.id, execution)

                params = {'key': execution.id}

                try:
                    task = taskqueue.Task(params=params)
                except taskqueue.TaskTooLargeError:
                    logging.error('Execution "%s" task is too large. ' \
                        'Continuing.' % execution.id)
                    continue

                queue.add(task)

        logging.info('Returning Request "%s" as JSON to client.' % request.id)
        utils.build_json(self, {'key': request.id}, 201)

        logging.debug('Finished RequestHandler.post() function')

    def delete(self, request_key):
        logging.debug('Begin RequestHandler.delete() function')

        key = db.Key.from_path('Request', request_key)

        logging.info('Deleting Request "%s" from datastore.' % request_key)
        try:
            db.delete(key)
        except apiproxy_errors.CapabilityDisabledError:
            logging.warning('Unable to delete Request "%s" due to ' \
                'maintenance.' % request_key)

        logging.info('Deleting Request "%s" from memcache.' % request_key)
        memcache.delete(request_key)

        self.error(204)

        logging.debug('Finished RequestHandler.delete() function')

def main():
    application = webapp.WSGIApplication([(r'/requests/(.*)\.json',
        RequestHandler)], debug=utils._DEBUG)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
