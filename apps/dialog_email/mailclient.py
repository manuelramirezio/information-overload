# -*- coding: utf-8 -*-

import time, re, string, StringIO

from twisted.internet import reactor, protocol, defer, ssl
from twisted.python import failure
from twisted.mail import imap4
from twisted.mail.smtp import rfc822, ESMTPSenderFactory

from spikeekips import _email, _mimetypes
from spikeekips._twisted.python import log
from spikeekips._twisted.web.client import Client as client_twisted

import config

RE_MIMETYPE_HANDLER = re.compile("[^a-z]", re.I)

class IMapClient (object, ) :
    def __init__ (self, config, ) :
        """
        server_info:
            (<host>, <port>, [<username>, <secret>, ] )
        """
        self.log = log.Log(self.__class__, )

        self._config = config
        self._mailbox = self._config.MAILBOX

        self._client = None
        self._flag_default = "\\Flagged"
        #self._flag_default = "\\Answered"

        self.log.debug("> start imap client.")

        self._time_s = None

    def run (self, ) :
        return self.connect(
            ).addErrback(
                self._eb_connect,
            ).addBoth(
                lambda x : self.connected and self._client.logout(
                        ).addCallbacks(self._cb_close, ) or None,
            )

    @property
    def connected (self, ) :
        _r = bool(self._client)
        if not _r :
            return _r

        if self._client and hasattr(
                self._client, "transport") and not self._client.transport.connected :
            self._client = None
            return False

        return True

    def connect (self, ) :
        if self.connected :
            return self.select_mailbox(None, )
        else :
            self.log.debug(
                "> trying to connect, %s" %
                    ":".join(map(str, self._config.MAIL_SERVER_IMAP, ), ),
            )

            _c = protocol.ClientCreator(reactor, imap4.IMAP4Client, )

            return _c.connectSSL(
                self._config.MAIL_SERVER_IMAP[0],
                self._config.MAIL_SERVER_IMAP[1],
                ssl.ClientContextFactory(),
            ).addCallbacks(
                self._cb_connect,
                self._eb_connect,
            )

    def _cb_close (self, *a, **kw) :
        if self._time_s :
            self.log.debug("elapsed time: %f" % (time.time() - self._time_s), )

        self._client = None
        return

    def _eb_default (self, f, ) :
        self.log.debug("< failed, %s" % f, )
        f.raiseException()
        return

    def _eb_connect (self, f, ) :
        self.log.debug("< failed to connect, %s" % f, )

        return

    def _cb_connect (self, client, ) :
        self.log.debug("> connected.")
        self._client = client

        if not self._config.CREDENTIAL :
            return self.select_mailbox(None, )

        self.log.debug("> trying to login with %s" %
            ", ".join(map(str, self._config.CREDENTIAL[:1], ), ), )

        return self._client.login(*self._config.CREDENTIAL).addCallbacks(
            self.select_mailbox,
            self._eb_login,
        )

    def _eb_login (self, f, ) :
        self.log.error("< failed to login, %s" % f, )
        return

    def _set_flags (self, r, mids) :
        self.log.debug("> trying to set flags, %s" % repr(mids), )

        if len(mids) < 1 :
            return

        return self._client.addFlags(
            ",".join(map(str, mids, ), ),
            (self._flag_default, ),
        )

    def select_mailbox (self, r, ) :
        self.log.debug("< logined", )

        self.log.debug("> trying to select mailbox, %s" % self._mailbox, )
        return self._client.select(self._mailbox, ).addCallbacks(
            self._cb_select_mailbox,
            self._eb_select_mailbox,
        )

    def _cb_select_mailbox (self, info, ) :
        _flags = info.get("FLAGS")
        if self._flag_default not in _flags :
            self._flag_default == "\\Flagged"

        self.log.debug("< selected mailbox", )

        self.log.debug("> trying to search the un%s messages." % self._flag_default, )
        _q = dict((
            ("sorted", 1, ),
            ("un%s" % self._flag_default.replace("\\", "").lower(), 1, ),
        ), )

        return self._client.search(
            imap4.Query(**_q),
            uid=True,
        ).addCallbacks(
            self._cb_search_messages,
            self._eb_search_messages,
        )

    def _eb_select_mailbox (self, f, ) :
        self.log.debug("< failed to select mailbox", )

        return

    def _cb_search_messages (self, ids, ) :
        self.log.debug("< searched messages.", )
        self._time_s = time.time()

        if len(ids) < 1 :
            self.log.debug("> there are no messages in here, %s" % self._mailbox, )
            return

        self.log.debug("> trying to get the messages.", )

        _dlist = list()
        _iter = iter(ids[:config.NUMBER_OF_EMAIL_PER_SESSION], )
        while True :
            _uids = list()
            try :
                for j in range(config.NUMBER_OF_EMAIL_ASYNC) :
                    _uids.append(_iter.next(), )
            except StopIteration :
                pass

            if len(_uids) < 1 :
                break

            _dlist.append(
                self.fetch_messages(None, iter(_uids, ), )
            )

        self.log.debug("> %d handlers running" % len(_dlist), )
        return defer.DeferredList(_dlist, )

    def _eb_search_messages (self, f, ) :
        self.log.debug("< failed to search messages.", )
        return

    def fetch_messages (self, r, ids, ) :
        try :
            _uid = ids.next()
        except StopIteration :
            return

        self.log.debug("> trying to fetch message, %d" % _uid, )
        return self._client.fetchMessage(_uid, uid=True, ).addCallbacks(
            self.handle_message,
        ).addCallback(
            self.fetch_messages,
            ids,
        )

    def handle_message (self, r, ) :
        (_mid, _message, ) = r.items()[0]

        return defer.maybeDeferred(
            self._handle_message,
            _message.get("RFC822"),
            _mid,
        ).addCallback(
            self._cb_handle_message,
            [_mid, ],
        )

    def _cb_handle_message (self, r, mids, ) :
        if r is True :
            self.log.debug(
                "< registered to the api, message(%s)." % ", ".join(map(str, mids, )), )
            return self._set_flags(r, mids, )

        self.log.debug(
            "< failed to register to the api, message(%s)." % ", ".join(map(str, mids, )), )
        return

    def _handle_message (self, raw_message, mid, ) :
        self.log.debug("> trying to call the api.")

        with file(config.STORAGE_PATH + "/%s.eml" % mid, "w", ) as f :
            f.write(raw_message, )

        _client = client_twisted(config.API_URL, )
        return _client.post(None, postdata=dict(message=raw_message, )).addCallback(
            self._cb_request_api,
            (mid, ),
        ).addErrback(
            self._eb_request_api,
            (mid, ),
        )

    def _cb_request_api (self, r, mids, ) :
        return r.success

    def _eb_request_api (self, f, mids, ) :
        return False


