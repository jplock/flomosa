#!/usr/bin/env python2.5
# -*- coding: utf8 -*-
#
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2010 Flomosa, LLC
# All Rights Reserved.
#

import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api import taskqueue

from flomosa import exceptions, models, utils
from flomosa.queue import QueueHandler


class TaskHandler(QueueHandler):
    """Handles creating execution objects."""

    def post(self):
        logging.debug('Begin execution-creation task handler')

        num_tries = self.request.headers['X-AppEngine-TaskRetryCount']
        logging.info('Task has been executed %s times', num_tries)

        step_key = self.request.get('step_key')
        if not step_key:
            raise exceptions.MissingException('Missing "step_key" parameter.')

        request_key = self.request.get('request_key')
        if not request_key:
            raise exceptions.MissingException(
                'Missing "request_key" parameter.')

        member = self.request.get('member')
        if not member:
            raise exceptions.MissingException('Missing "member" parameter.')

        step = models.Step.get(step_key)
        request = models.Request.get(request_key)

        team = None
        team_key = self.request.get('team_key')
        if team_key:
            try:
                team = models.Team.get(team_key)
            except Exception:
                team = None

        execution_key = utils.generate_key()
        execution = models.Execution(key_name=execution_key, parent=request,
                                     request=request, step=step,
                                     process=step.process, member=member,
                                     team=team)

        execution.put()

        task = taskqueue.Task(params={'key': execution_key})
        queue = taskqueue.Queue('execution-process')
        queue.add(task)

        logging.debug('Finished execution-creation task handler')


def main():
    """Handles creating execution objects."""
    application = webapp.WSGIApplication([('/_ah/queue/execution-creation',
        TaskHandler)], debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
