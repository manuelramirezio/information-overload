# -*- coding: utf-8 -*-

"""
Parsing HTML
==================================================

Normally parsing,

>>> _content = file(root + "/merge_test_simple_html.html").read()
>>> _parser = parser_html.HTMLParser(u"http://www.daum.net/", )
>>> _parser.set_content(_content, ).filter().to_string() is not None
True

Remove comemnts
>>> _parser = parser_html.HTMLParser(u"http://www.daum.net/", )
>>> _html = _parser.set_content(_content, ).filter(filters_html.HTMLRemoveCommentFilter, ).to_string()
>>> "<!--" in _html
False
>>> "-->" in _html
False

Remove whitespace and comemnts
>>> _parser = parser_html.HTMLParser(u"http://www.daum.net/", )
>>> _html = _parser.set_content(_content).filter(filters_html.HTMLWhitespaceFilter, filters_html.HTMLRemoveCommentFilter, ).to_string()
>>> ">  <" in _html
False
>>> "<!--" in _html
False
>>> "-->" in _html
False

If not utf-8 document, it will automatically convert the charset to utf-8
>>> _content = file(root + "/merge_test_simple_html-euc_kr.html").read()
>>> _parser = parser_html.HTMLParser(u"http://www.daum.net/", )
>>> "charset=utf-8" in _parser.set_content(_content).filter().to_string()
True
>>> "charset=euc-kr" in _parser.set_content(_content).filter().to_string(make_unicode=False, )
True

Make every uri to absolute url
>>> _content = file(root + "/merge_test_simple_html.html").read()
>>> _base_url = u"http://www.daum.net/"
>>> _parser = parser_html.HTMLParser(_base_url, )
>>> _html = _parser.set_content(_content).filter(filters_html.HTMLAbsolutePathFilter, ).to_string()
>>> "http://www.daum.net/relative_css.css?ver=201010181957" in _html
True
>>> "http://www.daum.net/top/cid_5075.gif" in _html
True

>>> "src=\\"http://www.daum.net/relative_js.js?ver=201010181957\\"" in _html
True

Filtering title
>>> _content = file(root + "/merge_test_simple_html-euc_kr.html").read()
>>> _parser = parser_html.HTMLParser(u"http://www.daum.net/", )
>>> _parser.set_content(_content).filter(filters_html.HTMLTitleFilter, ).to_string()
u'Daum \uc2a4\ud3ec\uce20'

Remove useless attribute
>>> _content = file(root + "/merge_test_simple_html.html").read()
>>> _parser = parser_html.HTMLParser(u"http://www.daum.net/", )
>>> _parser.set_content(_content).filter(filters_html.HTMLRemoveUselessAttrsFilter, ).to_string() is not None
True

Remove script.
>>> _content = file(root + "/merge_test_simple_html.html").read()
>>> _parser = parser_html.HTMLParser(u"http://www.daum.net/", )
>>> "<script" not in _parser.set_content(_content).filter(filters_html.HTMLRemoveCommentFilter, filters_html.HTMLRemoveScript, ).to_string()
True

Filtering links

>>> _content = file(root + "/email_html_links0.html").read()
>>> _parser = parser_html.HTMLParser(u"http://www.daum.net/", encoding="utf-8", )
>>> _links = _parser.set_content(_content).filter(filters_html.HTMLLinkExtracter, ).nodes
>>> list(_links)
[{'data': u'http://www.hannal.net/cb/', 'type': 'Characters'}, {'data': u'http://www.dir.net/kdjflaskjd?ldjflasdj=\uc6b0\ub9ac\ub098\ub77c', 'type': 'Characters'}, {'data': u'http://www.cloudgifts.com', 'type': 'Characters'}]

Extract links from html email

>>> _content = file(root + "/email_html_links1.html").read()
>>> _parser = parser_html.HTMLParser(u"http://www.daum.net/", encoding="utf-8", )
>>> _links = _parser.set_content(_content).filter(filters_html.HTMLEmailLinkExtracter, ).nodes
>>> list(_links)
[{'data': u'http://blog.basho.com/2010/10/11/riak-0.13-released/', 'type': 'Characters'}]

>>> _content = file(root + "/email0.message").read()
>>> _parser = parser_html.HTMLParser(u"http://www.daum.net/", encoding="utf-8", )
>>> _links = _parser.set_content(_content).filter(filters_html.HTMLLinkExtracter, ).nodes
>>> list(_links)
[{'data': u'http://www.ibm.com/developerworks/opensource/library/os-django-models/index.html?ccy=zz&cmp=dw&cpb=dwope&cr=twitter&csr=djangomodels&ct=dwgra', 'type': 'Characters'}]

>>> _content = file(root + "/email_html0.message").read()
>>> _parser = parser_html.HTMLParser(u"http://www.daum.net/", encoding="utf-8", )
>>> _links = _parser.set_content(_content).filter(filters_html.HTMLLinkExtracter, ).nodes
>>> list(_links)
[{'data': u'http://pypi.python.org/pypi/django-mockups/0.4.4', 'type': 'Characters'}]

>>> _content = file(root + "/email_html0.message").read()
>>> _parser = parser_html.HTMLParser(None, encoding="utf-8", )
>>> list(_parser.set_content(_content).filter(filters_html.HTMLStripContent, ).nodes)
[u'django-mockups 0.4.4', u'http://pypi.python.org/pypi/django-mockups/0.4.4', u'(Sent from', u' ', u'Flipboard', u')', u'Sent from my iPad', u'\\n\\n']


>>> _content = u"django-mockups 0.4.4 http://pypi.python.org/pypi/django-mockups/0.4.4 (Sent from   Flipboard ) Sent from my iPad"
>>> _parser = parser_html.HTMLParser(None, encoding="utf-8", )
>>> list(_parser.set_content(_content).filter(filters_html.HTMLStripContent, ).nodes)
[u'django-mockups 0.4.4 http://pypi.python.org/pypi/django-mockups/0.4.4 (Sent from   Flipboard ) Sent from my iPad']

>>> _content = u"django-mockups 0.4.4 http://pypi.python.org/pypi/django-mockups/0.4.4 (Sent from   Flipboard ) Sent from my iPad".encode("euc-kr")
>>> _parser = parser_html.HTMLParser(None, encoding="euc-kr", )
>>> list(_parser.set_content(_content).filter(filters_html.HTMLStripContent, ).nodes)
[u'django-mockups 0.4.4 http://pypi.python.org/pypi/django-mockups/0.4.4 (Sent from   Flipboard ) Sent from my iPad']


"""


if __name__ == "__main__" :
    from spikeekips.html import parser as parser_html, filters as filters_html

    import os
    root = os.path.dirname(__file__)

    import doctest
    doctest.testmod()





