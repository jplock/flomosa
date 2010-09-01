#
# Copyright 2010 Flomosa, LLC
#

import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api.labs import taskqueue

from exceptions import MissingException
import models
import queueapp
import utils


class TaskHandler(queueapp.QueueHandler):

    def post(self):
        logging.debug('Begin execution-creation task handler')

        num_tries = self.request.headers['X-AppEngine-TaskRetryCount']
        logging.info('Task has been executed %s times' % num_tries)

        step_key = self.request.get('step_key')
        if not step_key:
            raise MissingException('Missing "step_key" parameter.')

        request_key = self.request.get('request_key')
        if not request_key:
            raise MissingException('Missing "request_key" parameter.')

        member = self.request.get('member')
        if not member:
            raise MissingException('Missing "member" parameter.')

        step = models.Step.get(step_key)
        request = models.Request.get(request_key)

        team = None
        team_key = self.request.get('team_key')
        if team_key:
            try:
                team = models.Team.get(team_key)
            except:
                team = None

        execution_key = utils.generate_key()
        execution = models.Execution(key_name=execution_key, step=step,
            process=step.process, member=member, team=team)

        execution.put()

        task = taskqueue.Task(params={'key': execution_key})
        queue = taskqueue.Queue('execution-process')
        queue.add(task)

        logging.debug('Finished execution-creation task handler')

def main():
    application = webapp.WSGIApplication([('/_ah/queue/execution-creation',
        TaskHandler)], debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()