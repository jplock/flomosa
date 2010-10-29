#!/usr/bin/env python2.5
# -*- coding: utf8 -*-
#
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2010 Flomosa, LLC
# All Rights Reserved.
#

import calendar
import copy
import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

from flomosa import exceptions, models
from flomosa.api import OAuthHandler, build_json


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
    """Returns a dict based on a list of keys and a default value."""
    new_dict = {}
    for key in keys:
        new_dict[key] = default_value
    return new_dict


class StatHandler(OAuthHandler):
    """Base handler process statistics requests."""

    def get_param(self, name, required=True):
        """Get a request parameter, raising an exception if not valid.

        If we are getting the 'filter' parameter, split the values by a comma
        and return the valid list of filters. If no filters found, return the
        entire list of statistic keys.

        """

        value = self.request.get(name, None)
        if name == 'filter':
            return_stats = []
            if value:
                filter_list = value.split(',')
                for key in filter_list:
                    if key in _STAT_TUPLE:
                        return_stats.append(key)
            if not return_stats:
                return_stats = _STAT_TUPLE
            return return_stats
        if not value:
            if required:
                raise exceptions.MissingException(
                    'Missing "%s" parameter.' % name)
        else:
            value = int(value)
            return value


class YearHandler(StatHandler):
    """Handles requests for yearly process statistics."""

    def get(self, process_key):
        logging.debug('Begin YearHandler.get() method')

        process = self.is_client_allowed(process_key)

        year = self.get_param('year')
        return_stats = self.get_param('filter')

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
        build_json(self, stats)

        logging.debug('Finished YearHandler.get() method')


class MonthHandler(StatHandler):
    """Handles requests for monthly process statistics."""

    def get(self, process_key):
        logging.debug('Begin MonthHandler.get() method')

        process = self.is_client_allowed(process_key)

        year = self.get_param('year')
        month = self.get_param('month')
        return_stats = self.get_param('filter')

        stats = {}
        keys = list_to_dict(return_stats)

        cal = calendar.Calendar()
        for day in cal.itermonthdays(year, month):
            if day < 1:
                continue
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
        build_json(self, stats)

        logging.debug('Finished MonthHandler.get() method')


class WeekHandler(StatHandler):
    """Handles requests for weekly process statistics."""

    def get(self, process_key):
        logging.debug('Begin WeekHandler.get() method')

        process = self.is_client_allowed(process_key)

        year = self.get_param('year')
        week_num = self.get_param('week_num')
        return_stats = self.get_param('filter')

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
        build_json(self, stats)

        logging.debug('Finished WeekHandler.get() method')


class DayHandler(StatHandler):
    """Handles requests for daily process statistics."""

    def get(self, process_key):
        logging.debug('Begin DayHandler.get() method')

        process = self.is_client_allowed(process_key)

        year = self.get_param('year')
        month = self.get_param('month')
        day = self.get_param('day')
        return_stats = self.get_param('filter')

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
        build_json(self, stats)

        logging.debug('Finished DayHandler.get() method')


def main():
    """Handles requests for process statistics."""
    application = webapp.WSGIApplication([
        (r'/stats/by-year/(.*)\.json', YearHandler),
        (r'/stats/by-month/(.*)\.json', MonthHandler),
        (r'/stats/by-week/(.*)\.json', WeekHandler),
        (r'/stats/by-day/(.*)\.json', DayHandler)], debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
