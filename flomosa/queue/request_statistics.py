#!/usr/bin/env python2.5
# -*- coding: utf8 -*-
#
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2010 Flomosa, LLC
# All Rights Reserved.
#

from datetime import datetime
import logging

from google.appengine.ext import db, webapp
from google.appengine.ext.webapp import util

from flomosa import exceptions, models
from flomosa.queue import QueueHandler


class TaskHandler(QueueHandler):

    def post(self):
        logging.debug('Begin request-statistics task handler')

        num_tries = self.request.headers['X-AppEngine-TaskRetryCount']
        logging.info('Task has been executed %s times' % num_tries)

        request_key = self.request.get('request_key')
        if not request_key:
            raise exceptions.MissingException(
                'Missing "request_key" parameter.')

        process_key = self.request.get('process_key')
        if not process_key:
            raise exceptions.MissingException(
                'Missing "process_key" parameter.')

        timestamp = self.request.get('timestamp')  # POSIX UTC timestamp
        if not timestamp:
            raise exceptions.MissingException('Missing "timestamp" parameter.')

        stat_time = datetime.utcfromtimestamp(float(timestamp))
        request = models.Request.get(request_key)
        process = models.Process.get(process_key)

        try:
            db.run_in_transaction(models.Statistic.store_stats, request,
                                  process, stat_time)
        except db.TransactionFailedError:
            logging.critical('Storing statistics failed for Request "%s". ' \
                'Re-queuing.' % request.id)
            return self.halt_requeue()

        logging.debug('Finished request-statistics task handler')


def main():
    application = webapp.WSGIApplication([('/_ah/queue/request-statistics',
        TaskHandler)], debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
