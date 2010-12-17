# -*- coding: utf-8 -*-

import re, uuid, time, datetime

import email
from email import quoprimime

from email import utils as utils_email
from email import encoders as encoders_email
from email import header as header_email
from email.mime.text import MIMEText
from email.mime.nonmultipart import MIMENonMultipart
from email.mime.multipart import MIMEMultipart
from email import header as header_email

from twisted.mail.smtp import messageid, rfc822date

import _mimetypes

RE_BLANK = re.compile("[\s][\s]*", re.I | re.M, )

def _c (s, ) :
    if type(s) in (unicode, ) :
        return s.encode("utf-8")

    return s

def _decode (s, charset=None, ) :
    if type(s) in (unicode, ) :
        return s

    try :
        if not charset :
            raise
        return s.decode(charset, "ignore")
    except :
        if type(s) in (str, ) :
            s = s.decode("utf-8", "ignore")

        return s

def _decode_header (v, ) :
    _v0 = u""
    if not v.strip().startswith("=?") :
        return v
    if not v.strip().endswith("?=") :
        try :
            v.strip().index("?=")
        except ValueError :
            pass
        else :
            _v = v.strip().rsplit("?=", 1)
            (v, _v0, ) = _v[0] + "?=", _v[1]
    
    _s, _charset = header_email.decode_header(v, )[0]
    return _decode(_s, _charset, ) + _v0


def uid () :
    return str(uuid.uuid1(), )

class SkipThisPayload (Exception, ) :
    pass

class BaseMessage (object, ) :
    @classmethod
    def from_string (cls, s, ) :
        _c = cls()
        _c._msg = email.message_from_string(s, )

        return _c

    def __init__ (self, ) :
        self._msg = None

    def is_valid (self, ) :
        return True not in map(
            lambda x : not self.get_header(x), ("to", "from", "message-id", ),
        )

    def to_string (self, ) :
        return self._msg.as_string()

    def _make_header_string (self, s, ) :
        return "-".join([i.capitalize() for i in s.split("-")])

    def _normalize_header_string (self, s, ) :
        return s.lower()

    def __setitem__ (self, k, v, ) :
        _k = k.lower().replace("-", "_", )
        _e = "_encode_header_%s" % _k
        if not hasattr(self, _e, ) :
            _e = "_encode_header_default"

        return self._msg.__setitem__(
            self._make_header_string(k),
            getattr(self, _e, )(self._normalize_header_string(k, ), _c(v), ),
        )

    def _encode_header_default (self, k, v, ) :
        return v

    def _encode_header_from (self, k, v, ) :
        (_a, _b, ) = utils_email.getaddresses([v, ])[0]
        return utils_email.formataddr(
            ("%s" % header_email.Header(_a, "utf-8").encode(), _b, ),
        )

    _encode_header_to = _encode_header_from
    _encode_header_reply_to = _encode_header_from

    def _encode_header_subject (self, k, v, ) :
        return header_email.Header(v, "utf-8").encode()

    def __delitem__ (self, k, ) :
        return self._msg.__delitem__(k, )

    def __getitem__ (self, k, ) :
        _v = self._msg.__getitem__(k, )

        _k = k.lower().replace("-", "_", )
        _e = "_decode_header_%s" % _k
        if not hasattr(self, _e, ) :
            _e = "_decode_header_default"

        return getattr(self, _e, )(k, _v, )

    def get_header (self, k, raw=False, ) :
        if raw :
            return self._msg.get(k, )

        return self.__getitem__(k, )

    def _decode_header_default (self, k, v, ) :
        if not v :
            return v

        return _decode_header(v, )

    def _decode_header_from (self, k, v, ) :
        if not v :
            return list()

        _as = utils_email.getaddresses(v.split(","), )
        return [i for i in (self._decode_from(k, i, ) for i in _as) if i]

    def _decode_from (self, k, v, ) :
        (_a, _b, ) = v
        try :
            return (
                self._decode_header_default(k, RE_BLANK.sub("", _a, ), ),
                RE_BLANK.sub("", _b, ),
            )
        except :
            return None

    _decode_header_to = _decode_header_from
    _decode_header_reply_to = _decode_header_from
    _decode_header_bcc = _decode_header_from
    _decode_header_cc = _decode_header_from

    def _decode_header_date (self, k, v, ) :
        return datetime.datetime.fromtimestamp(
            time.mktime(utils_email.parsedate(v), ),
        )

    def get_payloads (self, func_test=list(), ) :
        for _msg in self._msg.walk() :
            if _msg.is_multipart() :
                continue

            try :
                for _func in func_test :
                    if not _func(_msg, ) :
                        raise SkipThisPayload
            except SkipThisPayload :
                continue

            _cd = dict(
                _msg.get_params(failobj=dict(), header="content-disposition", ),
            )
            if _cd and _cd.has_key("attachment") :
                continue

            _charset = _msg.get_content_charset()
            _payload = _decode(_msg.get_payload(decode=True, ), _charset, )

            yield dict(
                is_default=self._msg.get_default_type() == _msg.get_content_type(),
                charset=_charset,
                content_type=_msg.get_content_type(),
                payload=_payload.strip(),
            )

    def get_attachments (self, ) :
        for _msg in self._msg.walk() :
            _cd = dict(
                _msg.get_params(
                    failobj=dict(),
                    header="content-disposition",
                ),
            )
            if not _cd or not _cd.has_key("attachment") :
                continue

            _filename = _msg.get_filename()
            yield dict(
                filename     = _filename and _decode_header(_filename) or str(uuid.uuid1(), ),
                mimetype     = _msg.get_content_type(),
                charset      = _msg.get_content_charset(),
                payload      = _msg.get_payload(decode=True, ),
            )

    def get_forwarded_messages (self, ) :
        for _msg in self._msg.walk() :
            _cd = dict(
                _msg.get_params(
                    failobj=dict(),
                    header="content-disposition",
                ),
            )
            if not _cd or not _cd.has_key("attachment") :
                continue
            elif _msg.get_content_type() != "message/rfc822" :
                continue

            _filename = _msg.get_filename()
            yield dict(
                filename     = _filename and _decode_header(_filename) or str(uuid.uuid1(), ),
                mimetype     = _msg.get_content_type(),
                charset      = _msg.get_content_charset(),
                payload      = _msg.get_payload(decode=not _msg.is_multipart(), ),
                is_multipart = _msg.is_multipart(),
            )

    def get_cids (self, decode=True, ) :
        for _msg in self._msg.walk() :
            if _msg.is_multipart() :
                continue

            _cid = dict(
                _msg.get_params(
                    failobj=dict(),
                    header="content-id",
                ),
            )
            if not _cid :
                continue

            _filename = _msg.get_filename()
            yield dict(
                cid         =  _cid.keys()[0][1:-1],
                filename    = _filename and _decode_header(_filename, ) or str(uuid.uuid1(), ),
                mimetype    = _msg.get_content_type(),
                charset     = _msg.get_content_charset(),
                payload     = _msg.get_payload(decode=decode, ),
            )

class Message (BaseMessage, ) :
    pass

class MessageWriter (BaseMessage, ) :
    def __init__ (self, ) :
        super(MessageWriter, self).__init__()

        self._msg = MIMEMultipart()
        #self._msg.set_charset("utf-8")

        self._subs = dict()

    def to_string (self, ) :
        self._msg["Date"] = rfc822date()
        self._msg["Message-id"] = messageid()

        return super(MessageWriter, self).to_string()

    def add_attachments (self, f, filename, content_type=None, ) :
        f.seek(0, 0, )
        _headers = (
            (
                "Content-Disposition",
                "attachment",
                dict(
                    filename=filename,
                ),
            ),
        )

        if not content_type : # guess mimetype
            content_type = _mimetypes.get_mimetype_from_filename(filename, )

        return self.add_sub(f.read(), content_type=content_type, headers=_headers, )

    def add_sub (self, s, content_type="text/plain", encoding=None, headers=tuple(), ) :
        if content_type == "text/plain" :
            _msg = MIMEText(_c(s), _charset="utf-8", )
        else :
            _msg = MIMENonMultipart(*content_type.split("/"))
            _msg.set_payload(s, charset=encoding and encoding or None, )

        if headers :
            for (k, v, _params, ) in headers :
                _msg.add_header(k, v, **_params)

        self._msg.attach(_msg, )

        self._subs[uid()] = _msg

        return uid

    def remove_sub (self, uid, ) :
        del self._msg._payload[self._msg._payload.index(self._subs.get(uid))]



