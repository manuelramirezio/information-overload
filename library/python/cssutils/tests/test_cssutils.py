# -*- coding: utf-8 -*-
"""Testcases for cssutils.css.CSSCharsetRule"""
__version__ = '$Id: test_cssutils.py 2010 2010-06-20 16:29:28Z cthedot $'

import basetest
import codecs
import cssutils
import os
import sys
import tempfile
import xml.dom

try:
    from minimock import mock, restore
except ImportError:
    mock = None 


class CSSutilsTestCase(basetest.BaseTestCase):

    exp = u'''@import "import/import2.css";
.import {
    /* ./import.css */
    background-image: url(images/example.gif)
    }'''

    def test_VERSION(self):
        self.assertEqual('0.9.7b3', cssutils.VERSION)

    def test_parseString(self):
        "cssutils.parseString()"
        s = cssutils.parseString(self.exp, 
                                 media='handheld, screen', 
                                 title='from string')
        self.assert_(isinstance(s, cssutils.css.CSSStyleSheet))
        self.assertEqual(None, s.href)
        self.assertEqual(self.exp, s.cssText)
        self.assertEqual(u'utf-8', s.encoding)
        self.assertEqual(u'handheld, screen', s.media.mediaText)
        self.assertEqual(u'from string', s.title)
        self.assertEqual(self.exp, s.cssText)
        
        ir = s.cssRules[0]
        self.assertEqual('import/import2.css', ir.href)
        irs = ir.styleSheet
        self.assertEqual(cssutils.css.CSSStyleSheet, type(irs))

        href = os.path.join(os.path.dirname(__file__), 
                            '..', '..', 'sheets', 'import.css')
        href = cssutils.helper.path2url(href)
        s = cssutils.parseString(self.exp, 
                                 href=href)
        self.assertEqual(href, s.href)

        ir = s.cssRules[0]
        self.assertEqual('import/import2.css', ir.href)
        irs = ir.styleSheet
        self.assert_(isinstance(irs, cssutils.css.CSSStyleSheet))
        self.assertEqual(irs.cssText, '@import "../import3.css";\n@import "import-impossible.css" print;\n.import2 {\n    /* sheets/import2.css */\n    background: url(./../images/example.gif)\n    }')

        tests = {
                 'a {color: red}': u'a {\n    color: red\n    }',
                 'a {color: rgb(1,2,3)}': u'a {\n    color: rgb(1, 2, 3)\n    }'
                 }
        self.do_equal_p(tests)

    def test_parseFile(self):
        "cssutils.parseFile()"
        # name if used with open, href used for @import resolving
        name = os.path.join(os.path.dirname(__file__), 
                            '..', '..', 'sheets', 'import.css')
        href = cssutils.helper.path2url(name)
        
        s = cssutils.parseFile(name, href=href, media='screen', title='from file')
        self.assert_(isinstance(s, cssutils.css.CSSStyleSheet))
        if sys.platform.startswith('java'):
            # on Jython only file:
            self.assert_(s.href.startswith('file:')) 
        else:
            # normally file:/// on win and file:/ on unix
            self.assert_(s.href.startswith('file:/')) 
        self.assert_(s.href.endswith('/sheets/import.css'))
        self.assertEqual(u'utf-8', s.encoding)
        self.assertEqual(u'screen', s.media.mediaText)
        self.assertEqual(u'from file', s.title)
        self.assertEqual(self.exp, s.cssText)
                
        ir = s.cssRules[0]
        self.assertEqual('import/import2.css', ir.href)
        irs = ir.styleSheet
        self.assert_(isinstance(irs, cssutils.css.CSSStyleSheet))
        self.assertEqual(irs.cssText, '@import "../import3.css";\n@import "import-impossible.css" print;\n.import2 {\n    /* sheets/import2.css */\n    background: url(./../images/example.gif)\n    }')
        
        # name is used for open and setting of href automatically
        # test needs to be relative to this test file!
        os.chdir(os.path.dirname(__file__))
        name = os.path.join('..', '..', 'sheets', 'import.css')
        
        s = cssutils.parseFile(name, media='screen', title='from file')
        self.assert_(isinstance(s, cssutils.css.CSSStyleSheet))
        if sys.platform.startswith('java'):
            # on Jython only file:
            self.assert_(s.href.startswith('file:')) 
        else:
            # normally file:/// on win and file:/ on unix
            self.assert_(s.href.startswith('file:/')) 
        self.assert_(s.href.endswith('/sheets/import.css'))
        self.assertEqual(u'utf-8', s.encoding)
        self.assertEqual(u'screen', s.media.mediaText)
        self.assertEqual(u'from file', s.title)
        self.assertEqual(self.exp, s.cssText)
                
        ir = s.cssRules[0]
        self.assertEqual('import/import2.css', ir.href)
        irs = ir.styleSheet
        self.assert_(isinstance(irs, cssutils.css.CSSStyleSheet))
        self.assertEqual(irs.cssText, '@import "../import3.css";\n@import "import-impossible.css" print;\n.import2 {\n    /* sheets/import2.css */\n    background: url(./../images/example.gif)\n    }')
        
        # next test
        css = u'a:after { content: "羊蹄€\u2020" }'

        fd, name = tempfile.mkstemp('_cssutilstest.css')
        t = os.fdopen(fd, 'wb')
        t.write(css.encode('utf-8'))
        t.close()
        
        self.assertRaises(UnicodeDecodeError, cssutils.parseFile, name, 'ascii')
        
        # ???
        s = cssutils.parseFile(name, encoding='iso-8859-1')
        self.assertEqual(cssutils.css.CSSStyleSheet, type(s))
        self.assertEqual(s.cssRules[1].selectorText, 'a:after')
        
        s = cssutils.parseFile(name, encoding='utf-8')
        self.assertEqual(cssutils.css.CSSStyleSheet, type(s))
        self.assertEqual(s.cssRules[1].selectorText, 'a:after')

        css = u'@charset "iso-8859-1"; a:after { content: "ä" }'
        t = codecs.open(name, 'w', 'iso-8859-1')
        t.write(css)
        t.close()
        
        self.assertRaises(
            UnicodeDecodeError, cssutils.parseFile, name, 'ascii')
        
        s = cssutils.parseFile(name, encoding='iso-8859-1')
        self.assertEqual(cssutils.css.CSSStyleSheet, type(s))
        self.assertEqual(s.cssRules[1].selectorText, 'a:after')

        self.assertRaises(
            UnicodeDecodeError, cssutils.parseFile, name, 'utf-8')

        # clean up
        try:
            os.remove(name)
        except OSError, e:
            pass

    def test_parseUrl(self):
        "cssutils.parseUrl()"
        href = os.path.join(os.path.dirname(__file__), 
                            '..', '..', 'sheets', 'import.css')
        #href = u'file:' + urllib.pathname2url(href)
        href = cssutils.helper.path2url(href)
        #href = 'http://seewhatever.de/sheets/import.css'
        s = cssutils.parseUrl(href, 
                              media='tv, print', 
                              title='from url')
        self.assert_(isinstance(s, cssutils.css.CSSStyleSheet))
        self.assertEqual(href, s.href)
        self.assertEqual(self.exp, s.cssText)
        self.assertEqual(u'utf-8', s.encoding)
        self.assertEqual(u'tv, print', s.media.mediaText)
        self.assertEqual('from url', s.title)
        
        sr = s.cssRules[1]
        img = sr.style.getProperty('background-image').cssValue.getStringValue()
        self.assertEqual(img, 'images/example.gif')
        
        ir = s.cssRules[0]
        self.assertEqual(u'import/import2.css', ir.href)
        irs = ir.styleSheet
        self.assertEqual(irs.cssText, '@import "../import3.css";\n@import "import-impossible.css" print;\n.import2 {\n    /* sheets/import2.css */\n    background: url(./../images/example.gif)\n    }')

        ir2 = irs.cssRules[0]
        self.assertEqual(u'../import3.css', ir2.href)
        irs2 = ir2.styleSheet
        self.assertEqual(irs2.cssText, '/* import3 */\n.import3 {\n    /* from ./import/../import3.css */\n    background: url(import/images2/../../images/example3.gif)\n    }')

    def test_setCSSSerializer(self):
        "cssutils.setSerializer() and cssutils.ser"
        s = cssutils.parseString('a { left: 0 }')
        exp4 = '''a {
    left: 0
    }'''
        exp1 = '''a {
 left: 0
 }'''
        self.assertEqual(exp4, s.cssText)
        newser = cssutils.CSSSerializer(cssutils.serialize.Preferences(indent=' '))
        cssutils.setSerializer(newser)
        self.assertEqual(exp1, s.cssText)
        newser = cssutils.CSSSerializer(cssutils.serialize.Preferences(indent='    '))
        cssutils.ser = newser
        self.assertEqual(exp4, s.cssText)

    def test_parseStyle(self):
        "cssutils.parseStyle()"
        s = cssutils.parseStyle('x:0; y:red')
        self.assertEqual(type(s), cssutils.css.CSSStyleDeclaration)
        self.assertRaises(xml.dom.SyntaxErr, cssutils.parseStyle, '@import "x";')

        tests = [
            (u'content: "ä"', 'iso-8859-1'),
            (u'content: "€"', 'utf-8')
        ]
        for v, e in tests:
            s = cssutils.parseStyle(v.encode(e), encoding=e)
            self.assertEqual(s.cssText, v)

        self.assertRaises(UnicodeDecodeError, cssutils.parseStyle, 
                          u'content: "ä"'.encode('utf-8'), 'ascii')


    def test_getUrls(self):
        "cssutils.getUrls()"
        cssutils.ser.prefs.keepAllProperties = True

        css='''
        @import "im1";
        @import url(im2);
        @import url( im3 );
        @import url( "im4" );
        @import url( 'im5' );
        a {
            background-image: url(c) !important;
            background-\image: url(b);
            background: url(a) no-repeat !important;
            }'''
        s = cssutils.parseString(css)
        urls = set(cssutils.getUrls(s))
        self.assertEqual(urls, set(["im1", "im2", "im3", "im4", "im5", 
                                    "c", "b", "a"]))

        cssutils.ser.prefs.keepAllProperties = False

    def test_replaceUrls(self):
        "cssutils.replaceUrls()"
        cssutils.ser.prefs.keepAllProperties = True

        css='''
        @import "im1";
        @import url(im2);
        a {
            background-image: url(c) !important;
            background-\image: url(b);
            background: url(a) no-repeat !important;
            }'''
        s = cssutils.parseString(css)
        cssutils.replaceUrls(s, lambda old: "NEW" + old)
        self.assertEqual(u'@import "NEWim1";', s.cssRules[0].cssText)
        self.assertEqual(u'NEWim2', s.cssRules[1].href)
        self.assertEqual(u'''background-image: url(NEWc) !important;
background-\\image: url(NEWb);
background: url(NEWa) no-repeat !important''', s.cssRules[2].style.cssText)

        cssutils.ser.prefs.keepAllProperties = False

    def test_resolveImports(self):
        "cssutils.resolveImports(sheet)"
        if mock:
            self._tempSer()
            cssutils.ser.prefs.useMinified()

            a = u'@charset "iso-8859-1";@import"b.css";ä{color:green}'.encode('iso-8859-1')
            b = u'@charset "ascii";\E4 {color:red}'.encode('ascii')
            
            # normal
            mock("cssutils.util._defaultFetcher", 
                 mock_obj=self._make_fetcher(None, b))
            s = cssutils.parseString(a)
            restore()            
            self.assertEqual(a, s.cssText)
            self.assertEqual(b, s.cssRules[1].styleSheet.cssText)
            c = cssutils.resolveImports(s)
            self.assertEqual('\xc3\xa4{color:red}\xc3\xa4{color:green}', 
                             c.cssText)

            c.encoding = 'ascii'
            self.assertEqual(r'@charset "ascii";\E4 {color:red}\E4 {color:green}', 
                             c.cssText)

            # b cannot be found
            mock("cssutils.util._defaultFetcher", 
                 mock_obj=self._make_fetcher(None, None))
            s = cssutils.parseString(a)
            restore()            
            self.assertEqual(a, s.cssText)
            self.assertEqual(cssutils.css.CSSStyleSheet, 
                             type(s.cssRules[1].styleSheet))
            c = cssutils.resolveImports(s)
            self.assertEqual('@import"b.css";\xc3\xa4{color:green}', 
                             c.cssText)

            # @import with media
            a = u'@import"b.css";@import"b.css" print, tv ;@import"b.css" all;'
            b = u'a {color: red}'            
            mock("cssutils.util._defaultFetcher", 
                 mock_obj=self._make_fetcher(None, b))
            s = cssutils.parseString(a)
            restore()            
            c = cssutils.resolveImports(s)
            self.assertEqual('a{color:red}@media print,tv{a{color:red}}a{color:red}', 
                             c.cssText)
            
            # cannot resolve with media => keep original
            a = u'@import"b.css"print;'
            b = u'@namespace "http://example.com";'            
            mock("cssutils.util._defaultFetcher", 
                 mock_obj=self._make_fetcher(None, b))
            s = cssutils.parseString(a)
            restore()            
            c = cssutils.resolveImports(s)
            self.assertEqual(a, c.cssText)

            # urls are adjusted too, layout:
            # a.css
            # c.css
            # img/img.gif
            # b/
            #     b.css
            #     subimg/subimg.gif
            a = u'''
                 @import"b/b.css";
                 a {
                     x: url(/img/abs.gif); 
                     y: url(img/img.gif); 
                     z: url(b/subimg/subimg.gif); 
                     }''' 
            def fetcher(url):
                c = {
                     'b.css': u'''
                         @import"../c.css";
                         b {
                             x: url(/img/abs.gif); 
                             y: url(../img/img.gif); 
                             z: url(subimg/subimg.gif); 
                             }''',
                     'c.css': u'''
                         c {
                             x: url(/img/abs.gif); 
                             y: url(./img/img.gif); 
                             z: url(./b/subimg/subimg.gif); 
                             }''' 
                     }
                return 'utf-8', c[os.path.split(url)[1]]  

            mock("cssutils.util._defaultFetcher", 
                 mock_obj=fetcher)
            s = cssutils.parseString(a)
            r = cssutils.resolveImports(s)
            restore()            
            cssutils.ser.prefs.useDefaults()
            cssutils.ser.prefs.keepComments = False
            self.assertEqual(u'''c {
    x: url(/img/abs.gif);
    y: url(img/img.gif);
    z: url(b/subimg/subimg.gif)
    }
b {
    x: url(/img/abs.gif);
    y: url(img/img.gif);
    z: url(b/subimg/subimg.gif)
    }
a {
    x: url(/img/abs.gif);
    y: url(img/img.gif);
    z: url(b/subimg/subimg.gif)
    }''', r.cssText)
        else:
            self.assertEqual(False, u'Minimock needed for this test')


if __name__ == '__main__':
    import unittest
    unittest.main()
