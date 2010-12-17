# -*- coding: utf-8 -*-

import re, sys, os, glob, time, cStringIO, gzip

from twisted.application import internet, service, strports
from twisted.internet import reactor
from twisted.python import threadpool, threadable, log
from twisted.python.logfile import DailyLogFile
from twisted.web import server, resource, wsgi, static, http

import twresource

PORT = 8000

for i in filter((lambda x : x.startswith("--prefix=")), sys.argv) :
    PORT = int(i.replace("--prefix=", ""))

# Environment setup for your Django project files:
#sys.path.append("mydjangosite")
#os.environ['DJANGO_SETTINGS_MODULE'] = 'mydjangosite.settings'
from django.core.handlers.wsgi import WSGIHandler
from django.core.servers.basehttp import AdminMediaHandler

def wsgi_resource():
    # Allow Ctrl-C to get you out cleanly:
    _thread = reactor.getThreadPool()
    _thread.adjustPoolsize(0, 100, )

    reactor.addSystemEventTrigger('after', 'shutdown', _thread.stop)

    return wsgi.WSGIResource(reactor, _thread, AdminMediaHandler(WSGIHandler(), ), )

# Twisted Application Framework setup:
application = service.Application('twisted-django')

# WSGI container for Django, combine it with twisted.web.Resource:
# XXX this is the only 'ugly' part: see the 'getChild' method in twresource.Root 
root = wsgi_resource()
#root = twresource.Root(wsgi_root)

# Servce Django media files off of /media:
#staticrsrc = static.File(os.path.join(os.path.abspath("."), "mydjangosite/media"))
#root.putChild("media", staticrsrc)

# The cool part! Add in pure Twisted Web Resouce in the mix
# This 'pure twisted' code could be using twisted's XMPP functionality, etc:
#root.putChild("google", twresource.GoogleResource())

# Serve it up:
#main_site = server.Site(root)
#internet.TCPServer(PORT, main_site).setServiceParent(application)

LOG_FORMAT = """
 ========================================================
 Call Type: %s
 ........................................................
 User From: %s
      Host: %s
    Header: %s
    Status: %s
 Byte Sent: %s
 ........................................................
User-Agnet: %s
   Referer: %s
"""
LOG_FORMAT_APACHE = """%s - %s [%s] "%s" %s %s "%s" "%s"
"""

re_not_log = re.compile("\.(jpg|css|png|js|gif|ico)$")

def FUNC_RE_NOT_LOG (request, ) :
    if re_not_log.search(request.uri.split("?")[0]) :
        return True

    return False

class HTTPFactory (server.Site, ) :
    def __init__ (self, *a, **kw) :
        self._is_stand = kw.get("is_stand", )
        if kw.has_key("is_stand") :
            del kw["is_stand"]

        server.Site.__init__(self, *a, **kw)

    def log (self, request, ) :
        firstLine = "%s %s HTTP/%s" %(
            request.method,
            request.uri,
            ".".join([str(x) for x in request.clientproto]))

        if not self._is_stand and self.logFile :
            self.logFile.write(
                 LOG_FORMAT_APACHE %(
                    request.getClientIP(),
                    # XXX: Where to get user from?
                    "-",
                    http._logDateTime,
                    firstLine,
                    request.code,
                    request.sentLength or "-",
                    self._escape(request.getHeader("referer") or "-"),
                    self._escape(request.getHeader("user-agent") or "-"),
                    )
                )

        if FUNC_RE_NOT_LOG(request) :
            return

        if self._is_stand :
            self.logFile.write(
                LOG_FORMAT % (
                        request.getHeader("x-requested-with") or "",
                        request.getClientIP(),
                        request.host,
                        firstLine,
                        request.code,
                        request.sentLength or "-",
                        self._escape(request.getHeader("user-agent") or "-"),
                        self._escape(request.getHeader("referer") or "-"),
                    )
                )

_factory = HTTPFactory(root, is_stand=True, )

_s = strports.service("tcp:%d" % PORT, _factory, )
_s.setServiceParent(application)


