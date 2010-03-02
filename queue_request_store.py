#!/usr/bin/env python

import uuid
import logging
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api import memcache
from google.appengine.api.labs import taskqueue
import models

class TaskHandler(webapp.RequestHandler):
    def post(self):
        data = self.request.params.items()
        if not data:
            return

        id = self.request.get('_id')
        process_key = self.request.get('process')
        requestor = self.request.get('requestor')

        process = memcache.get(process_key)
        if not process:
            process = models.Process.get_by_key_name(process_key)
            if process is None:
                return None
            memcache.set(process_key, process)

        request = models.Request(key_name=id, process=process,
            requestor=requestor)
        for key, value in data:
            if not hasattr(request, key):
                setattr(request, key, value)
        request.put()

        step = process.get_start_step()
        if not step:
            return None

        queue = taskqueue.Queue('request-process')
        for team_key in step.teams:
            team = memcache.get(team_key.name())
            if not team:
                team = models.Team.get(team_key)
                if team is None:
                    continue
                memcache.set(team_key.name(), team)

            for member in team.members:
                id = str(uuid.uuid4())
                execution = models.Execution(key_name=id, process=process,
                    request=request, step=step, team=team, member=member)
                execution_key = execution.put()
                memcache.set(execution_key.name(), execution)

                params = {'id': execution_key}
                task = taskqueue.Task(params=params)
                queue.add(task)

def main():
    application = webapp.WSGIApplication([('/_ah/queue/request-store',
        TaskHandler),], debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()