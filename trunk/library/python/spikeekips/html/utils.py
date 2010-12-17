# -*- coding: utf-8 -*-

import re, base64

from spikeekips.http import utils as utils_http

def generate_data_uri (content, mimetype, ) :
    return "data:%s;base64,%s" % (
        mimetype,
        base64.b64encode(content, ),
    )


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
    >>> _urls_found = extract_url_from_plain_text("민효님.http://www.dir.net/kdjflaskjd?ldjflasdj=우리나라", )
    >>> list(_urls_found)[0]
    'http://www.dir.net/kdjflaskjd?ldjflasdj=\\xec\\x9a\\xb0\\xeb\\xa6\\xac\\xeb\\x82\\x98\\xeb\\x9d\\xbc'
    
    
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


