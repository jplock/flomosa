#
# Copyright 2010 Flomosa, LLC
#

import logging

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
            logging.error(utils.get_log_message(e, 401))
            return utils.build_json(self, e, 401)

        process = models.Process.get(process_key)
        if not process:
            error_msg = 'Process key "%s" does not exist.' % process_key
            logging.error(utils.get_log_message(error_msg, 404))
            return utils.build_json(self, error_msg, 404)

        if process.client.id != client.id:
            error_msg = 'Permission denied.'
            logging.error(utils.get_log_message(error_msg, 401))
            return utils.build_json(self, error_msg, 401)

        logging.debug('Returning Process "%s" as JSON to client.' % process.id)
        utils.build_json(self, process.to_dict())

        logging.debug('Finished ProcessHandler.get() method')

    def put(self, process_key):
        logging.debug('Begin ProcessHandler.put() method')

        try:
            client = self.is_valid()
        except Exception, e:
            logging.error(utils.get_log_message(e, 401))
            return utils.build_json(self, e, 401)

        from django.utils import simplejson
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
            process = models.Process.from_dict(client, data)
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
        logging.info('Loading steps for Process "%s".' % process.id)
        for step_data in data.get('steps', list):
            try:
                step = process.add_step(step_data.get('name'),
                    description=step_data.get('description'),
                    team=step_data.get('team'),
                    members=step_data.get('members'),
                    is_start=step_data.get('is_start'),
                    step_key=step_data.get('key'))
            except Exception, e:
                logging.error('%s. Continuing.' % e)
                continue

        # Load any actions on this process
        logging.info('Loading actions for Process "%s".' % process.id)
        for action_data in data.get('actions', list):
            try:
                action = process.add_action(action_data.get('name'),
                    incoming=action_data.get('incoming'),
                    outgoing=action_data.get('outgoing'),
                    is_complete=action_data.get('is_complete'),
                    action_key=action_data.get('key'))
            except Exception, e:
                logging.error('%s. Continuing.' % e)
                continue

        logging.info('Returning Process "%s" as JSON to client.' % process.id)
        utils.build_json(self, {'key': process.id}, 201)

        logging.debug('Finished ProcessHandler.put() method')

    def delete(self, process_key):
        logging.debug('Begin ProcessHandler.delete() method')

        try:
            client = self.is_valid()
        except Exception, e:
            logging.error(utils.get_log_message(e, 401))
            return utils.build_json(self, e, 401)

        process = models.Process.get_by_key_name(process_key)
        if isinstance(process, models.Process):
            if process.client.id != client.id:
                error_msg = 'Permission denied.'
                logging.error(utils.get_log_message(error_msg, 401))
                return utils.build_json(self, error_msg, 401)
            else:
                process.delete()
        else:
            logging.info('Process "%s" not found in datastore to delete.' % \
                process_key)

        self.error(204)

        logging.debug('Finished ProcessHandler.delete() method')

def main():
    application = webapp.WSGIApplication([(r'/processes/(.*)\.json',
        ProcessHandler)], debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
