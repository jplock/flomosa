#!/usr/bin/env python
#
# Copyright 2010 Flomosa, LLC
#

import logging
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp import util
from google.appengine.api import memcache
from google.appengine.api.labs import taskqueue
import models
import utils

_EXECUTION_QUERY = db.GqlQuery("SELECT __key__ FROM Execution " \
    "WHERE process = :process AND request = :request AND step = :step " \
    "AND team = :team AND member = :member LIMIT 1")

class TaskHandler(webapp.RequestHandler):
    def post(self):
        logging.debug('Begin request-store task handler')

        num_tries = self.request.headers['X-AppEngine-TaskRetryCount']
        logging.info('Task has been executed %s times' % num_tries)

        data = self.request.params.items()
        if not data:
            logging.error('No request data found')
            return None

        request_key = self.request.get('_id')
        process_key = self.request.get('process')
        requestor = self.request.get('requestor')

        process = utils.load_from_cache(process_key, models.Process)
        if not process:
            logging.error('Process "%s" was not found. Exiting.' % process_key)
            return None
        elif not process.is_valid():
            logging.error('Process "%s" is not valid. Exiting.' % process_key)
            return None

        request = models.Request.get_by_key_name(request_key)
        if not request:
            logging.info('Request "%s" not found in datastore, creating.' % \
                request_key)
            request = models.Request(key_name=request_key, process=process,
                requestor=requestor)
            for key, value in data:
                if not hasattr(request, key):
                    setattr(request, key, value)

            try:
                request.put()
            except:
                logging.error('Unable to save request object in datastore. ' \
                    'Re-queuing.')
                self.error(500)
                return None

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
                    logging.info('Execution "%s" previously queued for "%s".' % \
                        (execution_key.name(), member))
                    continue

                execution_key = utils.generate_key()
                execution = models.Execution(key_name=execution_key,
                    process=process, request=request, step=step, team=team,
                    member=member)

                try:
                    execution.put()
                except:
                    logging.error('Unable to save execution object in ' \
                        'datastore. Re-queuing.')
                    self.error(500)
                    return None

                memcache.set(execution_key, execution)

                params = {'execution_key': execution_key}
                task = taskqueue.Task(params=params)
                queue.add(task)

        logging.debug('Finished request-store task handler')

def main():
    application = webapp.WSGIApplication([('/_ah/queue/request-store',
        TaskHandler)], debug=utils._DEBUG)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
