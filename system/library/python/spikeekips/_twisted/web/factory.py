# -*- coding: utf-8 -*-

import logging
from twisted.web import client as client_http, error
from twisted.python import failure

class OverCapacity (error.Error, ) :
    def __init__ (self, message=None, ) :
        super(OverCapacity, self).__init__(code=413, message=message, )

class LengthLimitHTTPClient (client_http.HTTPPageGetter, ) :
    def __init__ (self, *a, **kw) :
        self._length_limit = None

    def _set_length_limit (self, v, ) :
        self._length_limit = int(v)

    def _get_length_limit (self, ) :
        return self._length_limit

    length_limit = property(_get_length_limit, _set_length_limit, )

    def _check_length_limit (self, length=None, ) :
        _length = self.length
        if length :
            _length = length

        if not self.length_limit or not _length or _length < self.length_limit :
            return True

        logging.debug("Overcapacity(%s), it exceed size limit, %s." % (
            _length,
            self.length_limit,
        ))
        self.factory.noPage(
            failure.Failure(
                OverCapacity(
                    "Content length is too large, current limit is %0.1fK" % (
                        float(self.length_limit) / float(1000), ), ),
            )
        )
        self.queitLoss = True
        self.transport.loseConnection()

        return False

    def handleStatus_200 (self, *a, **kw) :
        if not self._check_length_limit() :
            return

        return client_http.HTTPPageGetter.handleStatus_200(self, *a, **kw)

    def handleResponse (self, response, ) :
        if not self._check_length_limit(len(response, )) :
            return

        client_http.HTTPPageGetter.handleResponse(self, response, )

class LengthLimitHTTPClientFactory (client_http.HTTPClientFactory, ) :
    protocol = LengthLimitHTTPClient
    _length_limit = None

    def __init__ (self, *a, **kw) :
        self._length_limit = self.__class__._length_limit
        if kw.has_key("length_limit") :
            try :
                self._length_limit = int(kw.get("length_limit"))
            except (ValueError, TypeError, ) :
                self._length_limit = None

            del kw["length_limit"]

        if self._length_limit is None :
            self.protocol = client_http.HTTPPageGetter

        client_http.HTTPClientFactory.__init__(self, *a, **kw)

    def buildProtocol (self, *a, **kw) :
        _p = client_http.HTTPClientFactory.buildProtocol(self, *a, **kw)
        _p.length_limit = self._length_limit

        return _p





