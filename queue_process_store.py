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


class TaskHandler(webapp.RequestHandler):
    def post(self):
        logging.debug('Begin process-store task handler')

        num_tries = self.request.headers['X-AppEngine-TaskRetryCount']
        logging.info('Task has been executed %s times' % num_tries)

        process_key = self.request.get('key', None)
        if not process_key:
            logging.error('Missing "process_key" parameter. Existing.')
            return None
        else:
            logging.info('Found Process key "%s" in request data.' % \
                process_key)

        try:
            data = simplejson.loads(self.request.get('data'))
        except:
            logging.error('Error parsing JSON request. Exiting.')
            return None

        kind = data.get('kind', None)
        if not kind or kind != 'Process':
            logging.error('Invalid "kind" parameter; expected "kind=Process".' \
                ' Exiting.')
            return None

        try:
            process = models.Process.from_dict(data)
        except Exception, e:
            logging.error('%s. Exiting.' % e)
            return None

        if not isinstance(process, models.Process):
            logging.error('Unable to create Process "%s". Exiting.' % \
                process_key)
            return None

        try:
            logging.info('Storing Process "%s" in datastore.' % process.id)
            process.put()
        except:
            logging.error('Unable to save Process key "%s" in datastore. ' \
                'Re-queuing.' % process.id)
            self.error(500)
            return None

        logging.info('Storing Process "%s" in memcache.' % process.id)
        memcache.set(process.id, process)

        # Load any steps on this process
        steps = data.get('steps', list)
        for step_data in steps:
            step_kind = step_data.get('kind', None)
            step_process_key = step_data.get('process', None)
            if not step_kind or step_kind != 'Step':
                logging.error('Data is not a valid Step dict object. ' \
                    'Continuing.')
                continue
            if not step_process_key or step_process_key != process_key:
                logging.error('Step process key "%s" does not match ' \
                    'Process key "%s". Continuing.' % (step_process_key,
                    process_key))
                continue

            try:
                step = models.Step.from_dict(step_data)
            except Exception, e:
                logging.error('%s. Continuing.' % e)
                continue

            try:
                logging.info('Storing Step "%s" in datastore.' % step.id)
                step.put()
            except:
                logging.error('Unable to save Step "%s" in datastore. ' \
                    'Re-queuing.' % step.id)
                self.error(500)
                return None

            logging.info('Storing Step "%s" in memcache.' % step.id)
            memcache.set(step.id, step)

        # Load any actions on this process
        actions = data.get('actions', list)
        for action_data in actions:
            action_kind = action_data.get('kind', None)
            action_process_key = action_data.get('process', None)
            if not action_kind or action_kind != 'Action':
                logging.error('Data is not a valid Action dict object. ' \
                    'Continuing.')
                continue
            if not action_process_key or action_process_key != process_key:
                logging.error('Action process key "%s" does not match ' \
                    'Process key "%s". Continuing.' % (action_process_key,
                    process_key))
                continue

            try:
                action = models.Action.from_dict(action_data)
            except Exception, e:
                logging.error('%s. Continuing.' % e)
                continue

            try:
                logging.info('Storing Action "%s" in datastore.' % action.id)
                action.put()
            except:
                logging.error('Unable to save Action "%s" in datastore. ' \
                    'Re-queuing.' % action.id)
                self.error(500)
                return None

            logging.info('Storing Action "%s" in memcache.' % action.id)
            memcache.set(action.id, action)

        logging.debug('Finished process-store task handler')

def main():
    application = webapp.WSGIApplication([('/_ah/queue/process-store',
        TaskHandler)], debug=utils._DEBUG)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
