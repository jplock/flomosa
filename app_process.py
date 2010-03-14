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

class ProcessHandler(webapp.RequestHandler):

    def get(self, process_key):
        logging.debug('Begin ProcessHandler.get() function')

        logging.info('Looking up Process "%s" in memcache then datastore.' % \
            process_key)
        process = utils.load_from_cache(process_key, models.Process)
        if not isinstance(process, models.Process):
            error_msg = 'Process key "%s" does not exist.' % process_key
            logging.error(utils.get_log_message(error_msg, 404))
            return utils.build_json(self, error_msg, 404)

        logging.info('Returning Process "%s" as JSON to client.' % process.id)
        utils.build_json(self, process.to_dict())

        logging.debug('Finished ProcessHandler.get() function')

    def put(self, process_key):
        logging.debug('Begin ProcessHandler.put() function')

        try:
            data = simplejson.loads(self.request.body)
        except:
            error_msg = 'Error parsing JSON request.'
            logging.error(utils.get_log_message(error_msg, 500))
            return utils.build_json(self, error_msg, 500)

        if not data.get('name'):
            error_msg = 'Missing "name" parameter.'
            logging.error(utils.get_log_message(error_msg, 400))
            return utils.build_json(self, error_msg, 400)

        if data.get('kind') != 'Process':
            error_msg = 'Invalid "kind" parameter; expected "kind=Process".'
            logging.error(utils.get_log_message(error_msg, 400))
            return utils.build_json(self, error_msg, 400)

        # Load the process data
        try:
            process = models.Process.from_dict(data)
        except Exception, e:
            logging.error(utils.get_log_message(e, 400))
            return utils.build_json(self, e, 400)

        if not isinstance(process, models.Process):
            error_msg = 'Unable to create Process "%s".' % process_key
            logging.error(utils.get_log_message(error_msg, 500))
            return utils.build_json(self, error_msg, 500)

        logging.info('Storing Process "%s" in datastore.' % process.id)
        try:
            process.put()
        except apiproxy_errors.CapabilityDisabledError:
            error_msg = 'Unable to save Process "%s" due to maintenance. ' % \
                process.id
            logging.error(utils.get_log_message(error_msg, 500))
            return utils.build_json(self, error_msg, 500)
        except:
            error_msg = 'Unable to save Process "%s" in datastore.' % \
                process.id
            logging.error(utils.get_log_message(error_msg, 500))
            return utils.build_json(self, error_msg, 500)

        logging.info('Storing Process "%s" in memcache.' % process.id)
        memcache.set(process.id, process)

        # Load any steps on this process
        for step_data in data.get('steps'):
            try:
                step = models.Step.from_dict(step_data)
            except Exception, e:
                logging.error('%s. Continuing.' % e)
                continue

            try:
                logging.info('Storing Step "%s" in datastore.' % step.id)
                step.put()
            except apiproxy_errors.CapabilityDisabledError:
                error_msg = 'Unable to save Step "%s" due to maintenance.' % \
                    step.id
                logging.error(utils.get_log_message(error_msg, 500))
                return utils.build_json(self, error_msg, 500)
            except:
                error_msg = 'Unable to save Step "%s" in datastore.' % step.id
                logging.error(utils.get_log_message(error_msg, 500))
                return utils.build_json(self, error_msg, 500)

            logging.info('Storing Step "%s" in memcache.' % step.id)
            memcache.set(step.id, step)

        # Load any actions on this process
        for action_data in data.get('actions'):
            try:
                action = models.Action.from_dict(action_data)
            except Exception, e:
                logging.error('%s. Continuing.' % e)
                continue

            logging.info('Storing Action "%s" in datastore.' % action.id)
            try:
                action.put()
            except apiproxy_errors.CapabilityDisabledError:
                error_msg = 'Unable to save Action "%s" due to maintenance.' \
                    % action.id
                logging.error(utils.get_log_message(error_msg, 500))
                return utils.build_json(self, error_msg, 500)
            except:
                error_msg = 'Unable to save Action "%s" in datastore.' % \
                    action.id
                logging.error(utils.get_log_message(error_msg, 500))
                return utils.build_json(self, error_msg, 500)

            logging.info('Storing Action "%s" in memcache.' % action.id)
            memcache.set(action.id, action)

        logging.info('Returning Process "%s" as JSON to client.' % process.id)
        utils.build_json(self, {'key': process.id}, 201)

        logging.debug('Finished ProcessHandler.put() function')

    def delete(self, process_key):
        logging.debug('Begin ProcessHandler.delete() function')

        process = models.Process.get_by_key_name(process_key)
        if isinstance(process, models.Process):
            process.delete_steps_actions()

            logging.info('Deleting Process "%s" from memcache.' % process.id)
            memcache.delete_multi([process_key, process.id])

            logging.info('Deleting Process "%s" from datastore.' % process.id)
            try:
                process.delete()
            except apiproxy_errors.CapabilityDisabledError:
                logging.warning('Unable to delete Process "%s" due to ' \
                    'maintenance.' % process.id)
        else:
            logging.warning('Process key "%s" not found in datastore to ' \
                'delete.' % process_key)

        self.error(204)

        logging.debug('Finished ProcessHandler.delete() function')

def main():
    application = webapp.WSGIApplication([(r'/processes/(.*)\.json',
        ProcessHandler)], debug=utils._DEBUG)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
