#
# Copyright 2010 Flomosa, LLC
#

import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api.labs import taskqueue

import models
import utils


class TaskHandler(webapp.RequestHandler):
    def post(self):
        logging.debug('Begin execution-creation task handler')

        num_tries = self.request.headers['X-AppEngine-TaskRetryCount']
        logging.info('Task has been executed %s times' % num_tries)

        step_key = self.request.get('step_key')
        if not step_key:
            logging.error('Missing "step_key" parameter. Exiting.')
            return None

        step = models.Step.get(step_key)
        if not execution:
            logging.error('Step "%s" not found in datastore. Exiting.' % \
                step_key)
            return None

        request_key = self.request.get('request_key')
        if not request_key:
            logging.error('Missing "request_key" parameter. Exiting.')
            return None

        request = models.Request.get(request_key)
        if not request:
            logging.error('Request "%s" not found in datastore. Exiting.' % \
                request_key)
            return None

        member = self.request.get('member')
        if not member:
            logging.error('Missing "member" parameter. Exiting.')
            return None

        team = None
        team_key = self.request.get('team_key')
        if team_key:
            team = models.Team.get(team_key)

        execution_key = utils.generate_key()
        execution = models.Execution(key_name=execution_key, step=step,
            process=step.process, member=member, team=team)

        execution.put()

        task = taskqueue.Task(params={'key': execution_key})
        queue = taskqueue.Queue('execution-process')
        queue.add(task)

        logging.debug('Finished execution-creation task handler')

def main():
    application = webapp.WSGIApplication([('/_ah/queue/request-process',
        TaskHandler)], debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
