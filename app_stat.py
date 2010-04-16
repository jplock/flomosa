#
# Copyright 2010 Flomosa, LLC
#

import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

import models
import oauthapp
import utils


class StatHandler(oauthapp.OAuthHandler):

    def _check_param(self, name, min=None, max=None, valid=None):
        """Check that a variable exists in the request parameters.

        Optionally check that the value is between min and max or exists in a
        given list.
        """

        error_msg = None
        if valid is None:
            valid = []

        value = self.request.params.get(name, None)
        if not value:
            error_msg = 'Missing "%s" parameter.' % name
        else:
            if min and max and not min < value < max:
                error_msg = '%d is not between %d and %d' % (value, min, max)
            elif min and value < min:
                error_msg = '%d is not greater than %d' % (value, min)
            elif max and value > max:
                error_msg = '%d is greater than %d' % (value, max)
            elif valid and value not in valid:
                error_msg = '%s is not in (%s)' % (value, valid)
        if error_msg:
            logging.error(utils.get_log_message(error_msg, 400))
            return utils.build_json(self, error_msg, 400)
        return value

    def get(self, process_key):
        logging.debug('Begin StatHandler.get() method')

        try:
            client = self.is_valid()
        except Exception, e:
            logging.error(utils.get_log_message(e, 401))
            return utils.build_json(self, e, 401)

        logging.debug('Looking up Process "%s" in memcache then datastore.' % \
            process_key)
        process = models.Process.get(process_key)
        if not isinstance(process, models.Process):
            error_msg = 'Process key "%s" does not exist.' % process_key
            logging.error(utils.get_log_message(error_msg, 404))
            return utils.build_json(self, error_msg, 404)

        if process.client.id != client.id:
            error_msg = 'Permission denied.'
            logging.error(utils.get_log_message(error_msg, 401))
            return utils.build_json(self, error_msg, 401)

        valid_types = ('by-month', 'by-week', 'by-year')
        type = self._check_param('type', valid=valid_types)

        query = models.Statistic.all()
        query.filter('process =', process)

        stats = {}

        if type == 'by-month':
            required_params = ('month', 'year')
            params = {}
            for param in required_params:
                min = None
                max = None
                if param == 'month':
                    min = 1
                    max = 12
                elif param == 'year':
                    min = 2010
                params[param] = self._check_param(param, min=min, max=max)

            query.filter('year =', params['year'])
            query.filter('month =', params['month'])
            query.filter('type =', 'daily')
            query.order('date_key')
            results = query.fetch(32)
            for result in results:
                stats[result.day] = {
                    'num_requests': result.num_requests,
                    'num_requests_completed': result.num_requests_completed,
                    'min_request_seconds': result.min_request_seconds,
                    'max_request_seconds': result.max_request_seconds,
                    'avg_request_seconds': result.avg_request_seconds,
                    'total_request_seconds': result.total_request_seconds
                }
        elif type == 'by-week':
            required_params = ('year', 'week_num')
            params = {}
            for param in required_params:
                min = None
                max = None
                if param == 'year':
                    min = 2010
                elif param == 'week_num':
                    min = 1
                    max = 53
                params[param] = self._check_param(param, min=min, max=max)

            query.filter('year =', params['year'])
            query.filter('week_num =', params['week_num'])
            query.filter('type =', 'daily')
            query.order('date_key')
            results = query.fetch(7)
            for result in results:
                stats[result.day] = {
                    'num_requests': result.num_requests,
                    'num_requests_completed': result.num_requests_completed,
                    'min_request_seconds': result.min_request_seconds,
                    'max_request_seconds': result.max_request_seconds,
                    'avg_request_seconds': result.avg_request_seconds,
                    'total_request_seconds': result.total_request_seconds
                }
        elif type == 'by-year':
            required_params = ('year')
            year = self._check_param('year', min=2010)

            query.filter('year =', year)
            query.filter('type =', 'monthly')
            query.order('date_key')
            results = query.fetch(12)
            for result in results:
                stats[result.month] = {
                    'num_requests': result.num_requests,
                    'num_requests_completed': result.num_requests_completed,
                    'min_request_seconds': result.min_request_seconds,
                    'max_request_seconds': result.max_request_seconds,
                    'avg_request_seconds': result.avg_request_seconds,
                    'total_request_seconds': result.total_request_seconds
                }

        logging.info('Returning JSON response to client.')
        utils.build_json(self, stats, 200)

        logging.debug('Finished StatHandler.get() method')


def main():
    application = webapp.WSGIApplication([(r'/stats/process/(.*)\.json',
        StatHandler),], debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
