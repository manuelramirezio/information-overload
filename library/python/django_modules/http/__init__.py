# -*- coding: utf-8 -*-


import re, sys

from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect as HttpResponseRedirect_django, Http404
from django.utils.encoding import iri_to_uri

try :
    import cjson
    _dumps = lambda x : cjson.encode(x, )
except :
    from django.utils import simplejson as json
    _dumps = json.dumps

##################################################
# Exception
class HttpResponseUnAuthorized (HttpResponse) :
    status_code = 401
    message = "<h1>UnAuthorized Access</h1>"

##################################################
# Response
class HttpResponseListJSON (HttpResponse) :

    def __init__ (self, content=list(), mimetype="application/json", status=200,
            content_type=None, ) :
        super(HttpResponseListJSON, self).__init__(
            content="[%s]" % ",".join(content),
            mimetype=mimetype,
            status=status,
            content_type=content_type,
        )

class HttpResponseJSON (HttpResponse) :

    def __init__ (self, content="", mimetype="application/json", status=200, content_type=None, ) :
        if settings.DEBUG :
            mimetype = "text/html"

        super(HttpResponseJSON, self).__init__(content=_dumps(content), mimetype=mimetype, status=status, content_type=content_type, )

class HttpResponseGoBack (HttpResponseRedirect_django) :
    def __init__ (self, request, *a, **kw) :
        location = request.META.get("HTTP_REFERER")
        super(HttpResponseGoBack, self).__init__(location, *a, **kw)

def get_host (request, ) :
    _host = request.get_host()
    _h0 = _host.split(":")
    if len(_h0) > 1 and _h0[1] in ("80", ) or (hasattr(settings, "DEFAULT_PORT") and settings.DEFAULT_PORT) :
        _host = _h0[0]
    
    _scheme = request.META.get("REQUEST_SCHEME")
    if _scheme is None and request.META.get("wsgi.url_scheme") :
        _scheme = request.META.get("wsgi.url_scheme")
    
    return "%s://%s" % (
        _scheme,
        _host,
    )

def get_current_url (request, path=False, ) :
    _uri = request.META.get("REQUEST_URI")
    _qs = request.META.get("QUERY_STRING")
    if _uri is None :
        _uri = "%s%s" % (
            request.META.get("PATH_INFO"), _qs and ("?%s" % _qs) or "", )
    
    if path :
        return _uri
    else :
        _host = request.get_host()
        _h0 = _host.split(":")
        if len(_h0) > 1 and _h0[1] in ("80", ) :
            _host = _h0[0]

        _scheme = request.META.get("REQUEST_SCHEME")
        if _scheme is None and request.META.get("wsgi.url_scheme") :
            _scheme = request.META.get("wsgi.url_scheme")

        return "%s://%s%s" % (
            _scheme,
            _host,
            _uri,
        )


__author__ =  "Spike^ekipS <spikeekips@gmail.com>"

