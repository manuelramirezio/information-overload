# -*- coding: utf-8 -*-

import datetime

from twisted.application import service
from twisted.internet import reactor

from spikeekips._twisted.python import log

import mailclient

import config

class App (object, ) :
    def __init__ (self, config, ) :
        self.log = log.Log(self.__class__, )
        self._client = None

        self._config = config

    def run (self, ) :
        self._client = mailclient.IMapClient(self._config, )

        return self._client.run().addCallbacks(self._cb_run, self._eb_run, )

    def _cb_run (self, r, ) :
        self._client = None

        self.log.debug("finish", )
        reactor.callLater(config.INTERVAL, self.run, )

    def _eb_run (self, f, ) :
        self._client = None

        self.log.error("finish with failure, %s" % f, )
        reactor.callLater(config.INTERVAL, self.run, )


APP_NAME = "IO.dialog.email"
log.initialize(APP_NAME, )

application = service.Application(APP_NAME, )

App(config, ).run()


