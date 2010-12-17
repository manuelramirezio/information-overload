# -*- coding: utf-8 -*-

import re, urllib

from html5lib.filters._base import Filter
from html5lib.sanitizer import HTMLSanitizer

from spikeekips import odict, utils as utils_spikeekips
import utils

class BaseFilter (Filter, ) :
    FILTERING_SKIP = -1
    FILTERING_STOP = -2

    def __init__ (self, source, base_url, *a, **kw) :
        super(BaseFilter, self).__init__(source, *a, **kw)
        self._nodes = None
        self._base_url = base_url

    @classmethod
    def get_filter (cls, *a, **kw) :
        return cls(*a, **kw)

    @property
    def nodes (self, ) :
        return self._nodes

    def __iter__ (self, ) :
        if self._nodes :
            for t in self._nodes.itervalues() :
                yield t
        else :
            self._nodes = odict.OrderedDict()
            for t in super(BaseFilter, self).__iter__() :
                _k = utils_spikeekips.uid()

                # filter the token to do something.
                _m = self.filter(_k, t, )
                if _m == self.FILTERING_SKIP :
                    continue
                elif _m == self.FILTERING_STOP :
                    break

                self._nodes[_k] = t

            for i in self.nodes.itervalues() :
                yield i

    def get_filter_name (self, t, ) :
        return ""

    def get_filter_name_type (self, t, ) :
        return ""

    def _filter_default_type (self, k, t, ) :
        return False

    def _filter_default (self, k, t, ) :
        return False

    def filter (self, k, t, ) :
        _filter_name = self.get_filter_name(t)
        if not hasattr(self, _filter_name, ) :
            _filter_name = "_filter_default"

        _m = getattr(self, _filter_name, )(k, t, )
        if _m in (self.FILTERING_STOP, self.FILTERING_SKIP, ) :
            return _m

        _filter_name = self.get_filter_name_type(t)
        if not hasattr(self, _filter_name, ) :
            _filter_name = "_filter_default_type"

        return getattr(self, _filter_name, )(k, t, )

##################################################
# HTML Filters
##################################################

class HTMLFilter (BaseFilter, ) :
    def get_filter_name (self, token, ) :
        return "_filter_%s" % token.get("name", )

    def get_filter_name_type (self, token, ) :
        return "_filter_type_%s" % token.get("type", "", ).lower()

    def parse_attrs (self, token, ) :
        try :
            return dict(token.get("data", list(), ))
        except :
            return dict()

from html5lib.filters.whitespace import Filter as HTMLWhitespaceFilter
from html5lib.filters.inject_meta_charset import Filter as HTMLInjectMetaCharset

class HTMLRemoveCommentFilter (HTMLFilter, ) :
    def __init__ (self, *a, **kw) :
        super(HTMLRemoveCommentFilter, self).__init__(*a, **kw)

        self._in_comment = None
        self._characters_comment = list()

    def _filter_type_comment (self, k, t, ) :
        return self.FILTERING_SKIP

class HTMLAbsolutePathFilter (HTMLFilter, ) :
    def _filter_img (self, k, t, ) :
        _d = self.parse_attrs(t, )
        _src = _d.get("src", "").strip()
        if not _src :
            return self.FILTERING_SKIP
        elif _src[:5].lower().startswith("data:") :
            return False

        _d["src"] = urllib.basejoin(self._base_url, _src, )
        t["data"] = _d

    _filter_input = _filter_img

    def _filter_link (self, k, t, ) :
        _d = self.parse_attrs(t, )
        _href = _d.get("href", "").strip()
        if _href :
            _d["href"] = urllib.basejoin(self._base_url, _href, )
            t["data"] = _d

    def _filter_script (self, k, t, ) :
        _d = self.parse_attrs(t, )
        _type = _d.get("type", "").lower()
        _lang = _d.get("language", "").lower()
        if (_type == "text/javascript" or _lang == "javascript") and _d.get("src", "").strip() :
            _d["src"] = urllib.basejoin(self._base_url, _d.get("src", "").strip(), )
            t["data"] = _d

class HTMLTitleFilter (HTMLFilter, ) :
    def __init__ (self, *a, **kw) :
        super(HTMLTitleFilter, self).__init__(*a, **kw)
        self._in_head = False
        self._in_title = False

    def _filter_default_type (self, k, t, ) :
        return self.FILTERING_SKIP

    def _filter_head (self, k, t, ) :
        self._in_head = t.get("type") == "StartTag"
        if not self._in_head :
            return self.FILTERING_STOP

        return self.FILTERING_SKIP

    def _filter_title (self, k, t, ) :
        if not self._in_head :
            return self.FILTERING_STOP

        self._in_title = t.get("type") in ("StartTag", )
        if not self._in_title :
            return self.FILTERING_STOP

        return self.FILTERING_SKIP

    def _filter_type_characters (self, k, t, ) :
        if not self._in_title :
            return self.FILTERING_SKIP

    _filter_type_spacecharacters = _filter_type_characters

class HTMLRemoveUselessAttrsFilter (HTMLFilter, ) :
    acceptable_attributes = HTMLSanitizer.acceptable_attributes + [
        "xmlns",
        "content",
        "http-equiv",
    ]

    def filter (self, k, t, ) :
        if t.get("type") in ("StartTag", "EndTag", "EmptyTag", ) :
            t["data"] = [(i, j, ) for i, j in self.parse_attrs(t, ).items() if i.lower() in self.acceptable_attributes and j.strip()]

        return super(HTMLRemoveUselessAttrsFilter, self).filter(k, t, )

class HTMLRemoveScript (HTMLFilter, ) :
    def __init__ (self, *a, **kw) :
        super(HTMLRemoveScript, self).__init__(*a, **kw)

        self._in_script = False

    def _filter_type_characters (self, k, t, ) :
        if self._in_script :
            return self.FILTERING_SKIP

    _filter_type_spacecharacters = _filter_type_characters

    def _filter_script (self, k, t, ) :
        self._in_script = t.get("type") == "StartTag"
        return self.FILTERING_SKIP

class HTMLRemoveUselessLink (HTMLFilter, ) :
    available_css_meda = (
        "screen",
        "all",
        None,
    )

    not_available_meta_attributes = (
        "keywords",
        "description",
    )

    def __init__ (self, *a, **kw) :
        super(HTMLRemoveUselessLink, self).__init__(*a, **kw)
        self._found = False

    def _filter_type_characters (self, k, t, ) :
        if self._found :
            return self.FILTERING_SKIP

    _filter_type_spacecharacters = _filter_type_characters

    def _filter_link (self, k, t, ) :
        _a = self.parse_attrs(t, )
        _type = _a.get("type", "").strip().lower()
        _rel = _a.get("rel", "").strip().lower()
        _media = _a.get("media", "").strip()

        if _type != "text/css" or _rel != "stylesheet" :
            return self.FILTERING_SKIP
        elif _media not in self.available_css_meda :
            return self.FILTERING_SKIP

        return

    def _filter_meta (self, k, t, ) :
        _a = self.parse_attrs(t, )
        if _a.get("name", "").strip().lower() in self.not_available_meta_attributes :
            return self.FILTERING_SKIP
        elif not _a.get("content", "").strip() :
            return self.FILTERING_SKIP

    def _filter_style (self, k, t, ) :
        if t.get("type") == "StartTag" :
            _a = self.parse_attrs(t, )
            if _a.get("media", "").strip() not in self.available_css_meda :
                self._found = True
                return self.FILTERING_SKIP
        elif self._found :
            self._found = False
            return self.FILTERING_SKIP

        self._found = False
        return

class HTMLRemoveJavascript (HTMLFilter, ) :
    def __init__ (self, *a, **kw) :
        super(HTMLRemoveJavascript, self).__init__(*a, **kw)

        self._found = False

    def _filter_type_characters (self, k, t, ) :
        if self._found :
            return self.FILTERING_SKIP

    _filter_type_spacecharacters = _filter_type_characters

    def _filter_script (self, k, t, ) :
        _a = self.parse_attrs(t, )
        _type = _a.get("type", "").strip().lower()
        _rel = _a.get("rel", "").strip().lower()
        _src = _a.get("src", "").strip()

        if t.get("type") == "StartTag" :
            self._found = True
        elif self._found :
            self._found = False

        return self.FILTERING_SKIP

class HTMLLinkExtracter (HTMLFilter, ) :
    def __init__ (self, *a, **kw) :
        super(HTMLLinkExtracter, self).__init__(*a, **kw)

        self._in_body = False
        self._characters = [" ", ]

    def __iter__ (self, ) :
        list(super(HTMLLinkExtracter, self).__iter__())

        for j in utils.extract_url_from_plain_text("".join(self._characters), ) :
            if not j.strip() :
                return

            if j.strip()[0] in ("#", "?", "&", ) :
                continue

            _link = urllib.basejoin(self._base_url, j.strip(), )
            if not _link.strip() :
                continue

            yield dict(
                type="Characters",
                data=_link,
            )

    def _filter_body (self, k, t, ) :
        self._in_body = t.get("type") == "StartTag"

        return self.FILTERING_SKIP

    def _filter_type_characters (self, k, t, ) :
        if self._in_body :
            self._characters.append(t.get("data", "", ))

        return self.FILTERING_SKIP

    _filter_type_spacecharacters = _filter_type_characters

    def _filter_default (self, k, t, ) :
        if t.get("type") in ("Characters", "SpaceCharacters", ) :
            return

        if self._characters[-1] != " " :
            self._characters.append(" ")

        return self.FILTERING_SKIP

    def _filter_type_default (self, k, t, ) :
        return self.FILTERING_SKIP

RE_EMAIL_FOOTERS = (
    re.compile("^[\s]*==[=]*", re.I | re.M | re.U, ),
    re.compile("^[\s]*\-\-[\-]*", re.I | re.M | re.U, ),
    re.compile("sent[\s]*from[\s]*", re.I | re.M | re.U, ),
)

class HTMLEmailLinkExtracter (HTMLLinkExtracter, ) :
    def _filter_type_characters (self, k, t, ) :
        _s = t.get("data", "", ).strip()
        for _re in RE_EMAIL_FOOTERS :
            if _re.search(_s) :
                return self.FILTERING_STOP

        return super(HTMLEmailLinkExtracter, self)._filter_type_characters(k, t, )

RE_LINEBREAK = re.compile("[\n\r]*")
def sanitize_email_plain (s, ) :
    def _is_pass (_s) :
        for _re in RE_EMAIL_FOOTERS :
            if _re.search(_s) :
                return _e

        return -1

    _b = unicode()
    for _s in RE_LINEBREAK.split(s) :
        if _is_pass(_s, )  == -1 :
            break

        _b += u"%s\n" % _s

    return _b

class HTMLStripContent (HTMLFilter, ) :
    def __init__ (self, *a, **kw) :
        super(HTMLStripContent, self).__init__(*a, **kw)

        self._inbody = False
        self._content = list()

    def _filter_default_type (self, k, t, ) :
        self._content.append(t.get("data", ), )

        return False

    def _filter_default (self, k, t, ) :
        if not self._inbody :
            self._inbody = t.get("name") == "body"

        if not self._inbody :
            return self.FILTERING_SKIP

        if t.get("name") or t.get("type") in ("SerializeError", ) :
            return self.FILTERING_SKIP

    def __iter__ (self, ) :
        list(super(HTMLStripContent, self).__iter__())

        for i in self._content :
            yield i


##################################################
# CSS Filters
##################################################

from cssutils.css.cssvalue import CSSValue, CSSPrimitiveValue
from cssutils.css.property import Property

def get_style_properties (t, name, ) :
    _ks = list()

    _style = t.style
    _nname = _style._normalize(name, )
    for _item in reversed(_style.seq):
        _val = _item.value
        if isinstance(_val, Property):
            if (_nname == _val.name) or name == _val.literalname :
                _ks.append(_val, )

    return _ks

def check_css_uri (cssvalue, ) :
    return cssvalue.primitiveType == CSSPrimitiveValue.CSS_URI

def check_cssstylerule_has_uri (cssstylerule, func=None, ) :
    if func is None :
        func = lambda x : None

    _found = False
    for _p in cssstylerule.style.getProperties() :
        _ks = get_style_properties(cssstylerule, _p.name, )
        if not _ks :
            continue

        for _k in _ks :
            if _k.cssValue.cssValueType in (CSSValue.CSS_PRIMITIVE_VALUE, ) :
                if check_css_uri(_k.cssValue) :
                    func(_k.cssValue, )
                    _found = True
            elif _k.cssValue.cssValueType in (CSSValue.CSS_VALUE_LIST, ) :
                for i in _k.cssValue :
                    if not check_css_uri(i) :
                        continue

                    func(i, )
                    _found = True

    return _found

class CSSFilter (BaseFilter, ) :
    def get_filter_name (self, t, ) :
        return "_filter_%s" % t.__class__.__name__.lower()

class CSSRemoveUseless (CSSFilter, ) :
    def _filter_csscharsetrule (self, k, t, ) :
        return self.FILTERING_SKIP

class CSSAbsoluteURI (CSSFilter, ) :
    def _absolutize (self, cssValue, ) :
        cssValue.setStringValue(
            CSSPrimitiveValue.CSS_URI,
            urllib.basejoin(
                self._base_url,
                cssValue.getStringValue(),
            ),
        )

    def _filter_cssstylerule (self, k, t, ) :
        check_cssstylerule_has_uri(t, self._absolutize, )
        return

    def _filter_cssimportrule (self, k, t, ) :
        t.href = urllib.basejoin(
            self._base_url,
            t.href,
        )

if __name__ == "__main__" :
    import doctest
    doctest.testmod()




