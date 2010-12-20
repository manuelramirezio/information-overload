# -*- coding: utf-8 -*-

from twisted.internet import defer

from spikeekips.html import parser as parser_html, filters as filters_html
from spikeekips._twisted.python import log

import filters as filters_htmlmerger

class Throttle (object, ) :
    capacity = None
    current_size = 0

    def __init__ (self, ) :
        self.capacity = self.__class__.capacity
        self.current_size = self.__class__.current_size

    def __repr__ (self, ) :
        return u"<Throttle: %s>" % (
            ", ".join([": ".join(map(str, i, ), ) for i in self.__dict__.items()]),
        )

    @property
    def remains (self, ) :
        if self.capacity is None :
            return None

        return self.capacity - self.current_size

    def check (self, n, ) :
        return self.capacity > (self.current_size + n)

    def __add__ (self, v, ) :
        self.current_size += v
        return self

class Context (object, ) :
    throttle = None
    timeout = 100
    client = None # http(s) client class

    def __init__ (self, **kw) :
        self.throttle = Throttle()
        self.timeout = self.__class__.timeout

        for k, v in kw.items() :
            if hasattr(Throttle, k) :
                setattr(self.throttle, k, v, )
            else :
                setattr(self, k, v, )

    def __repr__ (self, ) :
        return u"<Context: %s, throttle: %s>" % (
            ", ".join([": ".join(map(str, i, ), )
                for i in self.__dict__.items() if i[0] != "throttle"]),
            str(repr(self.throttle)),
        )


class BaseMerger (object, ) :

    def __init__ (self, content, base_url, context=None, ) :
        self.log = log.Log(self.__class__, )

        self._content = content
        self._base_url = base_url

        if context is None :
            context = Context()

        self._context = context

        self.log.info("initialized with context, %s" % self._context, )

    def filter (self, *filters) :
        self.log.info("filtering '%s'" % ", ".join([i.__name__ for i in filters]), )

    def _cb_filter (self, r, ) :
        self.log.info("filtered.")
        return r

    def _get_callback (self, filter_class, *a) :
        _callback = lambda x : defer.maybeDeferred(lambda : x, )
        try :
            if issubclass(filter_class, filters_htmlmerger.DeferredFilter, ) :
                _callback = lambda x : defer.maybeDeferred(
                    filter_class(x, self._base_url, self._context, *a).merge,
                )
            elif issubclass(filter_class, filters_html.BaseFilter, ) :
                _callback = lambda x : defer.maybeDeferred(filter_class, x, self._base_url, )
            else :
                _callback = lambda x : defer.maybeDeferred(filter_class, x, )
        except :
            self.log.error(
                "failed to get filter class callback, %s, %s" % (filter_class, _a, ), )

        return _callback

    def to_string (self, nodes, ) :
        self.log.info("generate as string")

class HTMLMerger (BaseMerger, ) :
    def __init__ (self, content, base_url, context=None, ) :
        super(HTMLMerger, self).__init__(content, base_url, context=context, )

        self._parser = parser_html.HTMLParser(self._base_url, )
        self._parser.set_content(self._content, )

    def to_string (self, nodes, **kw) :
        super(HTMLMerger, self).to_string(nodes, )
        return parser_html.serialize(nodes, **kw)

    def filter (self, *filters) :
        super(HTMLMerger, self).filter(*filters)

        if not filters :
            return defer.maybeDeferred(lambda : self._parser.nodes)

        _d = None
        for i in filters :
            if type(i) not in (list, tuple, ) :
                i = (i, )

            _fclass, _a = i[0], i[1:]

            _callback = self._get_callback(_fclass, *_a)
            if _d is None :
                _d = _callback(self._parser.nodes, )
            else :
                _d.addCallback(_callback, )

        return _d.addCallback(
            self._cb_filter,
        )

class CSSMerger (BaseMerger, ) :
    def __init__ (self, *a, **kw) :
        super(CSSMerger, self).__init__(*a, **kw)

        self._parser = parser_html.CSSParser(self._base_url, )
        self._parser.set_content(self._content, )

    def to_string (self, nodes, **kw) :
        super(CSSMerger, self).to_string(nodes, )
        return parser_html.serialize_css(self._parser.sheet, nodes, **kw)

    def filter (self, *filters) :
        super(CSSMerger, self).filter(*filters)

        if not filters :
            return defer.maybeDeferred(lambda : self._parser.sheet.cssRules, )

        _d = None
        for i in filters :
            if type(i) not in (list, tuple, ) :
                i = (i, )

            _fclass, _a = i[0], i[1:]

            _callback = self._get_callback(_fclass, *_a)
            if _d is None :
                _d = _callback(self._parser.sheet.cssRules, )
            else :
                _d.addCallback(_callback, )

        return _d.addCallback(
            self._cb_filter,
        )




