# -*- coding: utf-8 -*-

import logging, urllib, gzip, StringIO
from twisted.internet import reactor, defer
from twisted.web import client as client_http, error
from twisted.web2.http_headers import MimeType
from twisted.python import failure

from spikeekips import _mimetypes

class Response (object, ) :
    def __init__ (self, url, url_original=None, content=None, factory=None, ) :
        self.url = url
        self.url_original = url_original and url_original or url

        self.content = None
        self.mimeytpe = None
        self.headers = dict()
        self.mimetype = None

        self.errors = None
        self._status = None

        if factory :
            self.update_from_factory(content, factory, )

    def to_dict (self, ) :
        return dict(self.__dict__.iteritems(), )

    @classmethod
    def from_dict (cls, d, ) :
        _c = cls(d.get("url"))
        for k, v in d.items() :
            setattr(_c, k, v, )

        return _c

    def update_from_factory (self, content, factory, ) :
        self.status = factory.status
        self.headers = factory.response_headers

        _mt = MimeType.fromString(self.headers.get("content-type", ["", ])[0], )
        if _mt :
            _mt = "/".join((_mt.mediaType, _mt.mediaSubtype, ), )

        if not _mt :
            _mt = _mimetypes.get_mimetype_from_filename(self.url, )

        if not _mt :
            _mt = "text/html"

        self.mimetype = _mt

        if content :
            _ce = self.headers.get("content-encoding")
            if _ce and "gzip" in self.headers.get("content-encoding") :
                with gzip.GzipFile(fileobj=StringIO.StringIO(content, ), ) as _gz :
                    content = _gz.read()

        self.content = content

    def update_from_failure (self, f, ) :
        _status = self._status
        if isinstance(f.value, error.Error, ) :
            _status = f.value.status
        else :
            if f.type == defer.TimeoutError :
                _status = 408

        self.status = _status
        self.errors = str(f.value)

    def _get_status (self, ) :
        return self._status

    def _set_status (self, v, ) :
        self._status = v and int(v) or None

    status = property(_get_status, _set_status, )

    @property
    def is_redirected (self, ) :
        return self.url and self.url == self.url_original

    @property
    def length (self, ) :
        return self.content and len(self.content, ) or 0

    @property
    def success (self, ) :
        return self.status >= 200 and self.status < 300

    def __repr__ (self, ) :
        _d = self.to_dict()
        _d["success"] = self.success
        _d["status"] = self.status
        _d["is_redirected"] = self.is_redirected
        _d["length"] = self.length

        return """<Response:
           url: %(url)s
  url_original: %(url_original)s
       success: %(success)s
        status: %(status)s
 is_redirected: %(is_redirected)s
      mimetype: %(mimetype)s
content-length: %(length)d
        errors: %(errors)s
/>""" % _d

class Client (object, ) :
    def __init__ (self, base_url, client_factory=client_http.HTTPClientFactory, ) :
        self._base_url = base_url
        self._client_factory = client_factory

    def _request (self, method, url, *a, **kw) :
        if not url or (not url.startswith("http://") and not url.startswith("https://")) :
            if not self._base_url :
                return defer.maybeDeferred(lambda x : Response(url, ), )

            url = urllib.basejoin(self._base_url, (url and url or ""), )

        _scheme, _host, _port, _path = client_http._parse(url, )

        kw["method"] = method
        _factory = self._client_factory(url, *a, **kw)

        if _scheme == "https" :
            from twisted.internet import ssl
            #_contextFactory = kw.get("contextFactory")
            #if _contextFactory is None :
            #    _contextFactory = ssl.ClientContextFactory()
            _contextFactory = ssl.ClientContextFactory()

            reactor.connectSSL(_host, _port, _factory, _contextFactory, )
        else:
            reactor.connectTCP(_host, _port, _factory)

        return _factory.deferred.addCallback(
            self._cb_request, _factory, url,
        ).addCallback(
            self._cb_request_debug,
        )

    def _cb_request (self, content, factory, url_original, ) :
        _response = Response(factory.url, url_original, content=content, factory=factory, )

        if not _response.success :
            return _response

        return _response

    def _cb_request_debug (self, response, ) :
        logging.debug(response, )
        return response

    def get (self, url, *a, **kw) :
        return self._request("GET", url, *a, **kw)

    def post (self, url, *a, **kw) :
        if isinstance(kw.get("postdata", dict(), ), dict) :
            kw["postdata"] = urllib.urlencode(kw.get("postdata").items(), )

        return self._request("POST", url, *a, **kw)




