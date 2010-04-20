#
# Copyright 2010 Flomosa, LLC
#

import calendar
import copy
import datetime
import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

import models
import oauthapp
import utils

_STAT_TUPLE = (
    'num_requests',
    'num_requests_completed',
    'min_request_seconds',
    'max_request_seconds',
    'avg_request_seconds',
    'total_request_seconds'
)

# TODO: has to be an internal function to do this
def list_to_dict(keys, default_value=0):
    new_dict = {}
    for key in keys:
        new_dict[key] = default_value
    return new_dict


class YearHandler(oauthapp.OAuthHandler):
    def get(self, process_key):
        logging.debug('Begin YearHandler.get() method')

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

        year = self.request.get('year')
        if not year:
            error_msg = 'Missing "year" parameter.'
            logging.error(utils.get_log_message(error_msg, 400))
            return utils.build_json(self, error_msg, 400)
        else:
            year = int(year)

        return_stats = []
        filter = self.request.get('filter')
        if filter:
            filter_list = filter.split(',')
            for key in filter_list:
                if key in _STAT_TUPLE:
                    return_stats.append(key)
        if not return_stats:
            return_stats = _STAT_TUPLE

        stats = {}
        keys = list_to_dict(return_stats)
        for month in range(1, 13):
            if len(keys) == 1:
                stats[month] = 0
            else:
                stats[month] = copy.copy(keys)

        query = models.Statistic.all()
        query.filter('process =', process)
        query.filter('year =', year)
        query.filter('type =', 'monthly')
        query.order('month')

        results = query.fetch(12)
        for result in results:
            month = int(result.month)

            if len(keys) == 1:
                stats[month] = getattr(result, return_stats[0])
            else:
                for key in return_stats:
                    stats[month][key] = getattr(result, key, 0)

        logging.info('Returning JSON response to client.')
        utils.build_json(self, stats, 200)

        logging.debug('Finished YearHandler.get() method')


class MonthHandler(oauthapp.OAuthHandler):
    def get(self, process_key):
        logging.debug('Begin MonthHandler.get() method')

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

        year = self.request.get('year')
        if not year:
            error_msg = 'Missing "year" parameter.'
            logging.error(utils.get_log_message(error_msg, 400))
            return utils.build_json(self, error_msg, 400)
        else:
            year = int(year)

        month = self.request.get('month')
        if not month:
            error_msg = 'Missing "month" parameter.'
            logging.error(utils.get_log_message(error_msg, 400))
            return utils.build_json(self, error_msg, 400)
        else:
            month = int(month)

        return_stats = []
        filter = self.request.get('filter')
        if filter:
            filter_list = filter.split(',')
            for key in filter_list:
                if key in _STAT_TUPLE:
                    return_stats.append(key)
        if not return_stats:
            return_stats = _STAT_TUPLE

        stats = {}
        keys = list_to_dict(return_stats)

        cal = calendar.Calendar()
        for day in cal.itermonthdays(year, month):
            if len(keys) == 1:
                stats[day] = 0
            else:
                stats[day] = copy.copy(keys)

        query = models.Statistic.all()
        query.filter('process =', process)
        query.filter('year =', year)
        query.filter('month =', month)
        query.filter('type =', 'daily')
        query.order('day')

        results = query.fetch(32)
        for result in results:
            day = int(result.day)

            if len(keys) == 1:
                stats[day] = getattr(result, return_stats[0])
            else:
                for key in return_stats:
                    stats[day][key] = getattr(result, key, 0)

        logging.info('Returning JSON response to client.')
        utils.build_json(self, stats, 200)

        logging.debug('Finished MonthHandler.get() method')


class WeekHandler(oauthapp.OAuthHandler):
    def get(self, process_key):
        logging.debug('Begin WeekHandler.get() method')

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

        year = self.request.get('year')
        if not year:
            error_msg = 'Missing "year" parameter.'
            logging.error(utils.get_log_message(error_msg, 400))
            return utils.build_json(self, error_msg, 400)
        else:
            year = int(year)

        week_num = self.request.get('week_num')
        if not week_num:
            error_msg = 'Missing "week_num" parameter.'
            logging.error(utils.get_log_message(error_msg, 400))
            return utils.build_json(self, error_msg, 400)
        else:
            week_num = int(week_num)

        return_stats = []
        filter = self.request.get('filter')
        if filter:
            filter_list = filter.split(',')
            for key in filter_list:
                if key in _STAT_TUPLE:
                    return_stats.append(key)
        if not return_stats:
            return_stats = _STAT_TUPLE

        stats = {}
        keys = list_to_dict(return_stats)

        for day in range(1, 8):
            if len(keys) == 1:
                stats[day] = 0
            else:
                stats[day] = copy.copy(keys)

        query = models.Statistic.all()
        query.filter('process =', process)
        query.filter('year =', year)
        query.filter('week_num =', week_num)
        query.filter('type =', 'daily')
        query.order('week_day')

        results = query.fetch(7)
        for result in results:
            week_day = int(result.week_day)

            if len(keys) == 1:
                stats[week_day] = getattr(result, return_stats[0])
            else:
                for key in return_stats:
                    stats[week_day][key] = getattr(result, key, 0)

        logging.info('Returning JSON response to client.')
        utils.build_json(self, stats, 200)

        logging.debug('Finished WeekHandler.get() method')


class DayHandler(oauthapp.OAuthHandler):
    def get(self, process_key):
        logging.debug('Begin DayHandler.get() method')

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

        year = self.request.get('year')
        if not year:
            error_msg = 'Missing "year" parameter.'
            logging.error(utils.get_log_message(error_msg, 400))
            return utils.build_json(self, error_msg, 400)
        else:
            year = int(year)

        month = self.request.get('month')
        if not month:
            error_msg = 'Missing "month" parameter.'
            logging.error(utils.get_log_message(error_msg, 400))
            return utils.build_json(self, error_msg, 400)
        else:
            month = int(month)

        day = self.request.get('day')
        if not day:
            error_msg = 'Missing "day" parameter.'
            logging.error(utils.get_log_message(error_msg, 400))
            return utils.build_json(self, error_msg, 400)
        else:
            day = int(day)

        return_stats = []
        filter = self.request.get('filter')
        if filter:
            filter_list = filter.split(',')
            for key in filter_list:
                if key in _STAT_TUPLE:
                    return_stats.append(key)
        if not return_stats:
            return_stats = _STAT_TUPLE

        stats = {}
        keys = list_to_dict(return_stats)

        for hour in range(0, 24):
            if len(keys) == 1:
                stats[hour] = 0
            else:
                stats[hour] = copy.copy(keys)

        query = models.Statistic.all()
        query.filter('process =', process)
        query.filter('year =', year)
        query.filter('month =', month)
        query.filter('day =', day)
        query.filter('type =', 'hourly')
        query.order('hour')

        results = query.fetch(25)
        for result in results:
            hour = int(result.hour)

            if len(keys) == 1:
                stats[hour] = getattr(result, return_stats[0])
            else:
                for key in return_stats:
                    stats[hour][key] = getattr(result, key, 0)

        logging.info('Returning JSON response to client.')
        utils.build_json(self, stats, 200)

        logging.debug('Finished DayHandler.get() method')


def main():
    application = webapp.WSGIApplication([
        (r'/stats/by-year/(.*)\.json', YearHandler),
        (r'/stats/by-month/(.*)\.json', MonthHandler),
        (r'/stats/by-week/(.*)\.json', WeekHandler),
        (r'/stats/by-day/(.*)\.json', DayHandler)], debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
