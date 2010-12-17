# -*- coding: utf-8 -*-

import re, logging

from html5lib import html5parser, treewalkers, serializer, treebuilders
import cssutils
from cssutils.css.cssvalue import CSSValue, CSSPrimitiveValue
from cssutils.css.property import Property

from spikeekips.html import filters as filters_html

class BaseParser (object, ) :
    def __init__ (self, base_url, encoding=None, ) :
        self._base_url = base_url
        self._encoding = encoding
        self._content = None
        self.nodes = None

    def _get_encoding (self, ) :
        return self._encoding

    def _set_encoding (self, e, ) :
        self._encoding = e

    encoding = property(_get_encoding, _set_encoding, )

    def set_encoding (self, e, ) :
        self.encoding = e

        return self

    def _get_content (self, ) :
        return self._content

    def _set_content (self, content, ) :
        return self.set_content(content, )

    content = property(_get_content, _set_content, )

    def set_content (self, content, ) :
        self._content = content
        return self

    def filter (self, *filters) :
        if not filters :
            filters = list()

        _n = self.nodes
        for i in filters :
            if type(i) not in (list, tuple, ) :
                i = (i, )

            _filter_class, _a = i[0], i[1:]

            if issubclass(_filter_class, filters_html.BaseFilter, ) :
                _n = _filter_class(_n, self._base_url, *_a)
            else :
                _n = _filter_class(_n, *_a)

        self.nodes = _n
        logging.debug("filtered, %s" % repr(
            [(type(i) in (list, tuple, ) and i[0] or i).__class__.__name__ for i in filters]),
        )

        return self

    def parse (self, ) :
        self.nodes = None
        return self

    def to_string (self, r, ) :
        raise NotImplementedError

class HTMLParser (BaseParser, ) :
    def __init__ (self, *a, **kw) :
        super(HTMLParser, self).__init__(*a, **kw)

        self._parser = html5parser.HTMLParser(
            tree=treebuilders.getTreeBuilder("dom"),
        )
        self._treewalker = None

    def set_content (self, content, ) :
        super(HTMLParser, self).set_content(content, )
        _parser = self.parse()
        return _parser

    def parse (self, ) :
        self.nodes = treewalkers.getTreeWalker("dom")(
            self._parser.parse(
                self._content,
                encoding=(self.encoding and self.encoding or None),
            ),
        )

        if not self.encoding :
            # get real encoding.
            try :
                self.encoding = self._parser.phases.get("inHead"
                    ).parser.tokenizer.stream.charEncoding[0].lower()
                logging.debug("detected encoding: %s" % self.encoding, )
            except IndexError :
                logging.debug("failed to detecte, use default encoding, %s" % self.encoding, )

        logging.debug("encoding: %s" % self.encoding, )

        return self

    def to_string (self, make_unicode=True, **kw) :
        if not self.nodes :
            raise ValueError("not yet parsed.")

        _nodes = self.nodes
        if make_unicode and self.encoding != "utf-8" :
            kw["inject_meta_charset"] = True
            _nodes = filters_html.HTMLInjectMetaCharset(self.nodes, "utf-8", )

        return serialize(_nodes, **kw)

def serialize (nodes, **kw) :
    kw.update(dict(
        omit_optional_tags=False,
        quote_attr_values=True,
        use_trailing_solidus=True,
    ))

    _s = serializer.htmlserializer.HTMLSerializer(**kw)
    
    return u"".join(_s.serialize(nodes ), )

cssutils.ser.prefs.useMinified()
cssutils.ser.prefs.useDefaults()
cssutils.ser.prefs.lineSeparator = "\n"
cssutils.ser.prefs.indent = " "
cssutils.ser.prefs.indentSpecificities = False
cssutils.ser.prefs.keepComment = False
cssutils.ser.prefs.keepEmptyRules = False
cssutils.ser.prefs.omitLastSemicolon = False
cssutils.ser.prefs.paranthesisSpacer = " "
cssutils.ser.prefs.listItemSpacer = ""

class CSSParser (BaseParser, ) :
    def __init__ (self, *a, **kw) :
        super(CSSParser, self).__init__(*a, **kw)

        if not self.encoding :
            self.encoding = "utf-8"

        self._sheet = None

    @property
    def sheet (self, ) :
        return self._sheet

    def set_content (self, content, ) :
        super(CSSParser, self).set_content(content, )
        self.parse()

        return self

    def parse (self, ) :
        super(CSSParser, self).parse()
        self._sheet = self._get_parser().parseString(
            self._content.decode(self.encoding),
            encoding="utf-8", # it's optional
        )

        return self

    def _get_parser (self, ) :
        return cssutils.CSSParser(
            fetcher=lambda x : (None, None, ),
            parseComments=False,
            loglevel=logging.CRITICAL,
        )

    def filter (self, *filters) :
        if not filters :
            filters = list()

        _n = self._sheet.cssRules
        for i in filters :
            if type(i) not in (list, tuple, ) :
                i = (i, )

            _n = i[0](_n, self._base_url, *i[1:])

        self.nodes = _n

        logging.debug("filtered, %s" % repr(
            [(type(i) in (list, tuple, ) and i[0] or i).__class__.__name__ for i in filters]),
        )

        return self

    def to_string (self, make_unicode=True, remove_blank=True, **kw) :
        if not self.nodes :
            raise ValueError("not yet parsed.")

        return serialize_css(self._sheet, self.nodes, make_unicode=make_unicode, remove_blank=remove_blank, )


def _sub (m) :
    return u"%s " % m.group().strip()

RE_CSS_REMOVE_BLANK = (
    (re.compile("([^)])(;)[\s][\s]*", re.I | re.U, ), _sub, ),
    (re.compile("({)[\s][\s]*", re.I | re.U, ), _sub, ),
)

def serialize_css (sheet, cssRules, make_unicode=True, remove_blank=True, ) :
    if sheet.cssRules != cssRules :
        sheet.cssRules = cssutils.css.CSSRuleList()
        for i in cssRules :
            sheet.insertRule(i, )
    
    _s = sheet.cssText.decode("utf-8")
    if remove_blank :
        for _re, _sub in RE_CSS_REMOVE_BLANK :
            _s = _re.sub(_sub, _s, )
    
    return _s
    
    
