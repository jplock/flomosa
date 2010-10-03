#!/usr/bin/env python
# -*- coding: utf8 -*-
#
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2010 Flomosa, LLC
# All Rights Reserved.
#

from flomosa import models, exceptions
from flomosa.test import HandlerTestBase
from flomosa.web.client import ClientHandler, main


class ClientTest(HandlerTestBase):
    """Test Case for clients"""

    handler_class = ClientHandler

    def test_web_create_client(self):
        self.handle('get')
        self.assertEqual(self.response_code(), 200, 'Response code is not 200')
        self.assertEqual(self.response_body(), 'Test account created',
                         'Response body is not "Test account created"')

    def test_to_dict(self):
        client_key = 'test'
        data = {'oauth_secret': 'secret', 'email_address': 'test@flomosa.com',
                'password': 'password'}
        client = models.Client(key_name=client_key, **data)

        client_dict = client.to_dict()
        for key, value in data.items():
            self.assertEqual(value, client_dict[key])

        client.put()

        self.assertEqual(client.to_dict()['key'], client_key)

        client.delete()

    def test_client_methods(self):
        client_key = 'test'
        data = {'oauth_secret': 'secret', 'email_address': 'test@flomosa.com',
                'password': 'password'}
        client = models.Client(key_name=client_key, **data)
        client.put()

        self.assertEqual(client.id, client_key)
        self.assertEqual(str(client), client_key)
        self.assertEqual(unicode(client), client_key)
        self.assertEqual(client.secret, data['oauth_secret'])
        self.assertEqual(client.email_address, data['email_address'])

    def test_client_not_found(self):
        self.assertRaises(exceptions.NotFoundException, models.Client.get,
                          'test')
        self.assertRaises(exceptions.MissingException, models.Client.get, None)

    def test_client_main(self):
        main()