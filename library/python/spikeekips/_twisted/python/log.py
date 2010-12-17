# -*- coding: utf-8 -*-

import datetime, logging

from twisted.python import log

class LogObserver (log.PythonLoggingObserver, ) :
    def emit (self, eventDict) :
        if eventDict.get("system") in ("HTTPPageGetter,client", ) :
            return

        super(LogObserver, self).emit(eventDict, )

def _gl (levelname, ) :
    if type(levelname) in (str, unicode, ) :
        return getattr(logging, levelname.upper(), )

    return levelname

def initialize (name, level="info", ) :
    logging.basicConfig(level=_gl(level, ), )

    #log.PythonLoggingObserver(loggerName=name, ).start()
    LogObserver(loggerName=name, ).start()

def _log (msg, level="info", ) :
    log.msg("%s | %s" % (datetime.datetime.now(), msg.strip(), ), logLevel=_gl(level), from_3rdpatty=True, )


debug   = lambda x : _log(x, level="debug", )
error   = lambda x : _log(x, level="error", )
fatal   = lambda x : _log(x, level="fatal", )
info    = lambda x : _log(x, level="info", )
warn    = lambda x : _log(x, level="warn", )
warning = lambda x : _log(x, level="warning", )

class Log (object, ) :
    debug   = lambda a, x : a._do_log(x, level="debug", )
    error   = lambda a, x : a._do_log(x, level="error", )
    fatal   = lambda a, x : a._do_log(x, level="fatal", )
    info    = lambda a, x : a._do_log(x, level="info", )
    warn    = lambda a, x : a._do_log(x, level="warn", )
    warning = lambda a, x : a._do_log(x, level="warning", )

    prefix = ""

    def __init__ (self, cls, prefix="", ) :
        self._classname = cls.__name__
        self._prefix = prefix

    def _do_log (self, msg, level="info", ) :
        globals().get(level)("%s%s: %s" % (self._prefix, self._classname, msg, ), )


