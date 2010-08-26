#
# Copyright 2010 Flomosa, LLC
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
    type = 'unauthorized'
    def __init__(self, body=''):
        super(UnauthorizedException, self).__init__(403, body=body)


class UnauthenticatedException(HTTPException):
    type = 'unauthenticated'
    def __init__(self, body=''):
        super(UnauthenticatedException, self).__init__(401, body=body)


class NotFoundException(HttpException):
    type = 'notfound'
    def __init__(self, body=''):
        super(NotFoundException, self).__init__(404, body=body)


class MaintenanceException(HttpException):
    type = 'maintenance'
    def __init__(self, body=''):
        super(MaintenanceException, self).__init__(503, body=body)


class InternalException(HttpException):
    type = 'error'
    def __init__(self, body=''):
        super(InternalException, self).__init__(500, body=body)


class MissingException(HttpException):
    type = 'missing'
    def __init__(self, body=''):
        super(MissingException, self).__init__(400, body=body)