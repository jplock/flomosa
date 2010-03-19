#
# Copyright 2010 Flomosa, LLC
#

import logging

from django.utils import simplejson
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

import models
import utils
import oauthapp

class ProcessHandler(oauthapp.OAuthHandler):

    def get(self, process_key):
        logging.debug('Begin ProcessHandler.get() method')

        try:
            client = self.is_valid()
        except Exception, e:
            logging.error(utils.get_log_message(e, 404))
            return utils.build_json(self, e, 404)

        logging.debug('Looking up Process "%s" in memcache then datastore.' % \
            process_key)
        process = models.Process.get(process_key)
        if not isinstance(process, models.Process):
            error_msg = 'Process key "%s" does not exist.' % process_key
            logging.error(utils.get_log_message(error_msg, 404))
            return utils.build_json(self, error_msg, 404)

        logging.debug('Returning Process "%s" as JSON to client.' % process.id)
        utils.build_json(self, process.to_dict())

        logging.debug('Finished ProcessHandler.get() method')

    def put(self, process_key):
        logging.debug('Begin ProcessHandler.put() method')

        try:
            client = self.is_valid()
        except Exception, e:
            logging.error(utils.get_log_message(e, 404))
            return utils.build_json(self, e, 404)

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

        try:
            process.put()
        except Exception, e:
            logging.error(utils.get_log_message(e, 500))
            return utils.build_json(self, e, 500)

        # Clear out any old steps and actions
        process.delete_steps_actions()

        # Load any steps on this process
        for step_data in data.get('steps', list):
            try:
                step = models.Step.from_dict(step_data)
            except Exception, e:
                logging.error('%s. Continuing.' % e)
                continue

            try:
                step.put()
            except Exception, e:
                logging.error(utils.get_log_message(e, 500))
                return utils.build_json(self, e, 500)

        # Load any actions on this process
        for action_data in data.get('actions', list):
            try:
                action = models.Action.from_dict(action_data)
            except Exception, e:
                logging.error('%s. Continuing.' % e)
                continue

            try:
                action.put()
            except Exception, e:
                logging.error(utils.get_log_message(e, 500))
                return utils.build_json(self, e, 500)

        logging.info('Returning Process "%s" as JSON to client.' % process.id)
        utils.build_json(self, {'key': process.id}, 201)

        logging.debug('Finished ProcessHandler.put() method')

    def delete(self, process_key):
        logging.debug('Begin ProcessHandler.delete() method')

        try:
            client = self.is_valid()
        except Exception, e:
            logging.error(utils.get_log_message(e, 404))
            return utils.build_json(self, e, 404)

        process = models.Process.get_by_key_name(process_key)
        if isinstance(process, models.Process):
            process.delete()
        else:
            logging.info('Process key "%s" not found in datastore to ' \
                'delete.' % process_key)
        self.error(204)

        logging.debug('Finished ProcessHandler.delete() method')

def main():
    application = webapp.WSGIApplication([(r'/processes/(.*)\.json',
        ProcessHandler)], debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
