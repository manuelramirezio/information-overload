# -*- coding: utf-8 -*-

import re

from html5lib import html5parser, treewalkers, serializer, treebuilders
from html5lib.filters._base import Filter
from http import utils as utils_http

class HTMLLinkFilter (Filter, ) :
    IS_PASS_PASS = True
    IS_PASS_SKIP = False
    IS_PASS_STOP = -1

    def __init__ (self, base_url, *a, **kw) :
        super(HTMLLinkFilter, self).__init__(*a, **kw)
        self._base_url = base_url

        self._in_tag = False
        self._characters = list()

    def __iter__ (self, ) :
        for token in super(HTMLLinkFilter, self).__iter__() :
            if token.get("type") in ("StartTag", "EndTag", ) :
                self._in_tag = token.get("type") == "StartTag"

            if not self._in_tag and self._characters :
                for j in extract_url_from_plain_text("".join(self._characters), ) :
                    yield j.encode("utf-8")

                self._characters = list()

            _e = self.is_pass(token)
            if _e  == self.IS_PASS_SKIP :
                continue
            elif _e == self.IS_PASS_STOP :
                break

            if token.get("type") == "Characters" and self._in_tag :
                self._characters.append(token.get("data"), )

            elif token.get("name", "", ) == "a" :
                try :
                    _link = dict(token.get("data", list())).get("href", "").strip()
                except :
                    continue
                else :
                    if not _link or not utils_http.is_url(_link) :
                        continue

                yield _link.encode("utf-8")

    def is_pass (self, token, ) :
        return self.IS_PASS_PASS

class HTMLLink (object, ) :
    def __init__ (self, base_url, filter_class=HTMLLinkFilter, encoding=None, ) :
        self._base_url = base_url
        self._filter_class = filter_class
        self._encoding = encoding

    def strip (self, stream, ) :
        _parser = html5parser.HTMLParser(
            tree=treebuilders.getTreeBuilder("dom"),
        )

        _filter = self._filter_class(
            self._base_url,
            treewalkers.getTreeWalker("dom")(
                _parser.parse(stream, encoding=self._encoding, ),
            ),
        )
        return list(set([i for i in _filter]))

RE_EMAIL_FOOTERS = (
    # (stop sign, re object, ),
    (HTMLLinkFilter.IS_PASS_STOP, re.compile("^[\s]*==[=]*", re.I | re.M | re.U, ), ),
    (HTMLLinkFilter.IS_PASS_STOP, re.compile("^[\s]*\-\-[\-]*", re.I | re.M | re.U, ), ),
    (HTMLLinkFilter.IS_PASS_STOP, re.compile("sent[\s]*from[\s]*", re.I | re.M | re.U, ), ),
)

class EmailHTMLSanitizer (HTMLLinkFilter, ) :
    """
    >>> import os
    >>> _hl = HTMLLink(None, filter_class=EmailHTMLSanitizer, encoding="utf-8", )

    >>> _hl.strip(file(os.path.dirname(__file__) + "tests/email_html_links0.html").read(), )
    ['http://www.dir.net/kdjflaskjd?ldjflasdj=\\xec\\x9a\\xb0\\xeb\\xa6\\xac\\xeb\\x82\\x98\\xeb\\x9d\\xbc', 'http://www.hannal.net/cb/']

    >>> _hl.strip(file(os.path.dirname(__file__) + "tests/email_html_links1.html").read())
    ['http://blog.basho.com/2010/10/11/riak-0.13-released/']

    >>> _hl.strip(file(os.path.dirname(__file__) + "tests/email0.message").read())
    ['http://www.ibm.com/developerworks/opensource/library/os-django-models/index.html?ccy=zz&cmp=dw&cpb=dwope&cr=twitter&csr=djangomodels&ct=dwgra']

    """

    def is_pass (self, token, ) :
        if token.get("type") == "Characters" :
            _s = token.get("data", "", ).strip()
            for _e, _re in RE_EMAIL_FOOTERS :
                if _re.search(_s) :
                    return _e

        return True

RE_LINEBREAK = re.compile("[\n\r]*")
def sanitize_email_plain (s, ) :
    def _is_pass (_s) :
        for _e, _re in RE_EMAIL_FOOTERS :
            if _re.search(_s) :
                return _e

        return HTMLLinkFilter.IS_PASS_PASS

    _b = unicode()
    for _s in RE_LINEBREAK.split(s) :
        _e = _is_pass(_s, )
        if _e  == HTMLLinkFilter.IS_PASS_SKIP :
            continue
        elif _e == HTMLLinkFilter.IS_PASS_STOP :
            break

        _b += u"%s\n" % _s

    return _b

RE_HTML_LINK = re.compile("((http|https)\:\/\/.*)", re.I | re.U | re.M, )
RE_APPENDED_DOTS = re.compile("\.+$")
RE_SPLIT_BLANK = re.compile("[\s][\s]*")
RE_SPLIT_QUOTES = re.compile("['\"\<\>]['\"\<\>]*")
def extract_url_from_plain_text (s) :
    """
    Extract url from strings

    >>> _urls = (
    ...     u"http://www.yahoo.com/",
    ...     u"http://www.yahoo.com/1.html",
    ...     u"http://www.yahoo.com/2.html?a=1&b=2",
    ... )
    >>> _urls_found = extract_url_from_plain_text("%s\\r\\n%s     \\n%s" % _urls)
    >>> _a = list(_urls_found)
    >>> _a
    [u'http://www.yahoo.com/', u'http://www.yahoo.com/1.html', u'http://www.yahoo.com/2.html?a=1&b=2']
    >>> set(_a) == set(list(_urls))
    True

    Quoted urls

    >>> _urls_found = extract_url_from_plain_text("'%s' \\r\\n%s     \\n%s" % _urls)
    >>> set(_urls_found) == set(_urls)
    True
    >>> _urls_found = extract_url_from_plain_text('"%s" \\r\\n%s     \\n%s' % _urls)
    >>> set(_urls_found) == set(_urls)
    True

    >>> _urls_found = extract_url_from_plain_text('<a href="%s">%s</a><%s>'% _urls)
    >>> set(_urls_found) == set(_urls)
    True

    If the appended dots`.` will be removed like this,::

    >>> _urls_found = extract_url_from_plain_text("'http://www.google.com/...", )
    >>> list(_urls_found)
    ['http://www.google.com/']

    If the link precedded by '.', how it works?
    >>> _urls_found = extract_url_from_plain_text("kdfa우리.http://www.google.com/...", )
    >>> list(_urls_found)
    ['http://www.google.com/']

    """

    _l = list()
    [
        _l.extend(
            [
                RE_HTML_LINK.search(RE_APPENDED_DOTS.sub("", j, )).groups()[0]
                for j in RE_SPLIT_QUOTES.split(i) if j.strip() and j not in ("\"", "'") and RE_HTML_LINK.search(j)
            ]
        )
        for i in RE_SPLIT_BLANK.split(s) if RE_HTML_LINK.search(i)
    ]

    for i in _l :
        if not utils_http.is_url(i) :
            continue

        yield i



if __name__ == "__main__" :
    import sys
    import doctest
    doctest.testmod()


