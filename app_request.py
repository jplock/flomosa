#
# Copyright 2010 Flomosa, LLC
#

import logging
import urllib

from django.utils import simplejson
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api import urlfetch

import models
import utils
import cache
import oauthapp


class RequestHandler(oauthapp.OAuthHandler):

    def get(self, request_key=None):
        logging.debug('Begin RequestHandler.get() method')

        try:
            client = self.is_valid()
        except Exception, e:
            logging.error(utils.get_log_message(e, 404))
            return utils.build_json(self, e, 404)

        if not request_key:
            error_msg = 'Missing "request_key" parameter.'
            logging.error(utils.get_log_message(error_msg, 400))
            return utils.build_json(self, error_msg, 400)

        logging.debug('Looking up Request key "%s" in memcache then datastore.' \
            % request_key)
        request = models.Request.get(request_key)
        if not request:
            error_msg = 'Request key "%s" does not exist.' % request_key
            logging.error(utils.get_log_message(error_msg, 404))
            return utils.build_json(self, error_msg, 404)

        if request.client.id != client.id:
            error_msg = 'Permission denied.'
            logging.error(utils.get_log_message(error_msg, 401))
            return utils.build_json(self, error_msg, 401)

        utils.build_json(self, request.to_dict())

        logging.debug('Finished RequestHandler.get() method')

    def post(self, request_key=None):
        logging.debug('Begin RequestHandler.post() method')

        data = self.request.params

        process_key = data.get('process', None)
        if not process_key:
            error_msg = 'Missing "process" parameter.'
            logging.error(utils.get_log_message(error_msg, 400))
            return utils.build_json(self, error_msg, 400)

        process = models.Process.get(process_key)
        if not process:
            error_msg = 'Process "%s" does not exist.' % process_key
            logging.error(utils.get_log_message(error_msg, 404))
            return utils.build_json(self, error_msg, 404)

        if not process.is_valid():
            error_msg = 'Process "%s" is not valid.' % process_key
            logging.error(utils.get_log_message(error_msg, 500))
            return utils.build_json(self, error_msg, 500)

        requestor = data.get('requestor', None)
        if not requestor:
            error_msg = 'Missing "requestor" parameter.'
            logging.error(utils.get_log_message(error_msg, 400))
            return utils.build_json(self, error_msg, 400)

        if request_key:
            request = models.Request.get(request_key)
            if request:
                error_msg = 'Request "%s" already exists.' % request_key
                logging.error(utils.get_log_message(error_msg, 500))
                return utils.build_json(self, error_msg, 500)
        else:
            request_key = utils.generate_key()
            request = None

        if not request:
            request = models.Request(key_name=request_key,
                client=process.client,
                process=process,
                requestor=requestor)

        callback_url = data.get('callback_url', None)
        response_url = data.get('response_url', None)

        reserved_keys = ['callback_url', 'response_url']

        for key, value in data.items():
            if not hasattr(request, key) and key not in reserved_keys:
                setattr(request, key, value)

        try:
            request.put()
        except Exception, e:
            logging.error(utils.get_log_message(e, 500))
            return utils.build_json(self, e, 500)

        step = process.get_start_step()
        step.queue_tasks(request)

        response_fields = {'key': request.id}

        if callback_url:
            form_data = urllib.urlencode(response_fields)

            rpc = urlfetch.create_rpc(deadline=2)
            urlfetch.make_fetch_call(rpc,
                url=callback_url,
                payload=form_data,
                method=urlfetch.POST,
                headers={'Content-Type': 'application/x-www-form-urlencoded'})

            try:
                result = rpc.get_result()
                if result.status_code == 200:
                    logging.info('Submitted POST request to "%s" for Request ' \
                        '"%s".' % (callback_url, request.id))
                else:
                    logging.warning('Could not submit POST request to "%s" ' \
                        'for Request "%s".' % (callback_url, request.id))
            except urlfetch.DownloadError, e:
                logging.warning('Could not submit POST request to "%s" ' \
                    'for Request "%s" (%s).' % (callback_url, request.id, e))

        if response_url:
            logging.info('Permanently redirecting client to "%s".' % \
                response_url)
            self.redirect(response_url, permanent=True)
        else:
            logging.info('Returning Request "%s" as JSON to client.' % \
                request.id)
            utils.build_json(self, response_fields, 201)

        logging.debug('Finished RequestHandler.post() method')

    def delete(self, request_key):
        logging.debug('Begin RequestHandler.delete() method')

        try:
            client = self.is_valid()
        except Exception, e:
            logging.error(utils.get_log_message(e, 404))
            return utils.build_json(self, e, 404)

        request = models.Request.get_by_key_name(request_key)
        if isinstance(request, models.Request):
            if request.client.id != client.id:
                error_msg = 'Permission denied.'
                logging.error(utils.get_log_message(error_msg, 401))
                return utils.build_json(self, error_msg, 401)
            else:
                cache.delete_from_cache(request)
        else:
            logging.info('Request "%s" not found in datastore to delete.' % \
                request_key)

        self.error(204)

        logging.debug('Finished RequestHandler.delete() method')

def main():
    application = webapp.WSGIApplication(
        [(r'/requests/(.*)\.json', RequestHandler),
        (r'/requests/', RequestHandler)], debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
