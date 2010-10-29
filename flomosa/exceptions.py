#!/usr/bin/env python2.5
# -*- coding: utf8 -*-
#
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2010 Flomosa, LLC
# All Rights Reserved.
#


class HTTPException(Exception):
    """
    An HTTPException indicates some sort of HTTP error condition (probably a
    4XX) that should be returned as an HTTP response to the client.

    """
    type = 'error'

    def __init__(self, status=400, headers=None, body=''):
        self.status = status
        self.headers = headers if headers is not None else []
        self.body = body
        super(HTTPException, self).__init__(body)

    def __unicode__(self):
        return '%s (#%d)' % (self.body, self.status)

    def __str__(self):
        return self.__unicode__()


class UnauthorizedException(HTTPException):
    """A client is unauthorized to access a process or request."""
    type = 'unauthorized'

    def __init__(self, body=''):
        super(UnauthorizedException, self).__init__(403, body=body)


class UnauthenticatedException(HTTPException):
    """The user did not provide a valid OAuth signature."""
    type = 'unauthenticated'

    def __init__(self, body=''):
        super(UnauthenticatedException, self).__init__(401, body=body)


class NotFoundException(HTTPException):
    """The requested resource was not found in the datastore."""
    type = 'notfound'

    def __init__(self, body=''):
        super(NotFoundException, self).__init__(404, body=body)


class MaintenanceException(HTTPException):
    """The datastore is down for maintenance."""
    type = 'maintenance'

    def __init__(self, body=''):
        super(MaintenanceException, self).__init__(503, body=body)


class QuotaException(HTTPException):
    """The client exceeded their monthly quota."""
    type = 'quota'

    def __init__(self, body=''):
        super(QuotaException, self).__init__(503, body=body)


class InternalException(HTTPException):
    """An internal error occurred."""
    type = 'error'

    def __init__(self, body=''):
        super(InternalException, self).__init__(500, body=body)


class MissingException(HTTPException):
    """A required value was missing from the request."""
    type = 'missing'

    def __init__(self, body=''):
        super(MissingException, self).__init__(400, body=body)


class ValidationException(HTTPException):
    """A value did not validate properly."""
    type = 'validation'

    def __init__(self, body=''):
        super(ValidationException, self).__init__(500, body=body)
