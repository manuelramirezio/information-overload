# -*- coding: utf-8 -*-

"""
Parsing CSS
==================================================

Normally parsing,

>>> _content = file(root + "/merge_test_simple_css.css").read()
>>> _parser = parser_html.CSSParser(u"http://www.daum.net/", )
>>> _parser.set_content(_content, ).filter().to_string()
u'@charset "utf-8"; body,div,dl,dt,dd,ul,ol,li,h1,h2,h3,h4,form,fieldset,p,button { margin: 0; padding: 0; }\\nbody,h1,h2,h3,h4,th,td,input { color: #333; font-family: "\\ub3cb\\uc6c0",dotum,sans-serif; font-size: 12px; font-weight: normal; }\\nbody { background: #fff url(http://deco.daum-img.net/top/2010v2/bg_top_v01.gif) repeat-x; text-align: center; }\\nhr { display: none; }\\nimg,fieldset { border: 0; }\\nul,ol,li { list-style: none; }'

With difference encoding,

>>> _content = file(root + "/merge_test_simple_css-euc_kr.css").read()
>>> _parser = parser_html.CSSParser(u"http://www.daum.net/", encoding="euc-kr", )
>>> _parser.set_content(_content, ).filter().to_string()
u'@charset "utf-8"; @import url(http://photo-media.daum-img.net/css/media3/n_common.css?ver=20101012152422);\\nbody,div,dl,dt,dd,ul,ol,li,h1,h2,h3,h4,form,fieldset,p,button { margin: 0; padding: 0; }\\nbody,h1,h2,h3,h4,th,td,input { color: #333; font-family: "\\ub3cb\\uc6c0",dotum,sans-serif; font-size: 12px; font-weight: normal; }\\nbody { background: #fff url(http://deco.daum-img.net/top/2010v2/bg_top_v01.gif) repeat-x; text-align: center; }\\nhr { display: none; }\\nimg,fieldset { border: 0; }\\nul,ol,li { list-style: none; }'

Filtering

>>> _content = file(root + "/merge_test_simple_css-euc_kr.css").read()
>>> _parser = parser_html.CSSParser(u"http://www.daum.net/", encoding="euc-kr", )
>>> _parser.set_content(_content, ).filter(filters_html.CSSRemoveUseless, ).to_string()
u'@import url(http://photo-media.daum-img.net/css/media3/n_common.css?ver=20101012152422);\\nbody,div,dl,dt,dd,ul,ol,li,h1,h2,h3,h4,form,fieldset,p,button { margin: 0; padding: 0; }\\nbody,h1,h2,h3,h4,th,td,input { color: #333; font-family: "\\ub3cb\\uc6c0",dotum,sans-serif; font-size: 12px; font-weight: normal; }\\nbody { background: #fff url(http://deco.daum-img.net/top/2010v2/bg_top_v01.gif) repeat-x; text-align: center; }\\nhr { display: none; }\\nimg,fieldset { border: 0; }\\nul,ol,li { list-style: none; }'

Make URI to absolute uri

>>> _base_url = u"http://www.daum.net/"
>>> _content = file(root + "/merge_test_simple_css_relative_uri-euc_kr.css").read()
>>> _parser = parser_html.CSSParser(_base_url, encoding="euc-kr", )
>>> _parser.set_content(_content, ).filter(filters_html.CSSAbsoluteURI, ).to_string()
u'@charset "utf-8"; @import url(http://www.daum.net/css/media3/n_common.css?ver=20101012152422);\\nbody,div,dl,dt,dd,ul,ol,li,h1,h2,h3,h4,form,fieldset,p,button { margin: 0; padding: 0; }\\nbody,h1,h2,h3,h4,th,td,input { color: #333; font-family: "\\ub3cb\\uc6c0",dotum,sans-serif; font-size: 12px; font-weight: normal; }\\nbody { background: #fff url(http://www.daum.net/top/2010v2/bg_top_v01.gif) repeat-x; text-align: center; }\\ntable { background-image: url(http://www.daum.net/top/2010v2/bg_top_v01.gif);\\n }\\nhr { display: none; }\\nimg,fieldset { border: 0; }\\nul,ol,li { list-style: none; }'

Chaining filters

>>> _base_url = u"http://www.daum.net/"
>>> _content = file(root + "/merge_test_simple_css_relative_uri-euc_kr.css").read()
>>> _parser = parser_html.CSSParser(_base_url, encoding="euc-kr", )
>>> _parser.set_content(_content, ).filter(filters_html.CSSRemoveUseless, filters_html.CSSAbsoluteURI, ).to_string()
u'@import url(http://www.daum.net/css/media3/n_common.css?ver=20101012152422);\\nbody,div,dl,dt,dd,ul,ol,li,h1,h2,h3,h4,form,fieldset,p,button { margin: 0; padding: 0; }\\nbody,h1,h2,h3,h4,th,td,input { color: #333; font-family: "\\ub3cb\\uc6c0",dotum,sans-serif; font-size: 12px; font-weight: normal; }\\nbody { background: #fff url(http://www.daum.net/top/2010v2/bg_top_v01.gif) repeat-x; text-align: center; }\\ntable { background-image: url(http://www.daum.net/top/2010v2/bg_top_v01.gif);\\n }\\nhr { display: none; }\\nimg,fieldset { border: 0; }\\nul,ol,li { list-style: none; }'

"""

if __name__ == "__main__" :
    from spikeekips.html import parser as parser_html, filters as filters_html

    import os
    root = os.path.dirname(__file__)

    import doctest
    doctest.testmod()





