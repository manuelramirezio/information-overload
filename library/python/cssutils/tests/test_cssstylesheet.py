# -*- coding: utf-8 -*-
"""Tests for css.CSSStyleSheet"""
__version__ = '$Id: test_cssstylesheet.py 1990 2010-05-30 16:52:39Z cthedot $'

import xml.dom
import basetest
import cssutils.css

class CSSStyleSheetTestCase(basetest.BaseTestCase):

    def setUp(self):
        super(CSSStyleSheetTestCase, self).setUp()
        self.r = cssutils.css.CSSStyleSheet() # used by basetest
        self.s = self.r # used here
        self.rule = cssutils.css.CSSStyleRule()

    def test_init(self):
        "CSSStyleSheet.__init__()"
        self.assertEqual('text/css', self.s.type)
        self.assertEqual(False, self.s._readonly)
        self.assertEqual([], self.s.cssRules)
        self.assertEqual(False, self.s.disabled)
        self.assertEqual(None, self.s.href)
        self.assertEqual(None, self.s.media)
        self.assertEqual(None, self.s.ownerNode)
        self.assertEqual(None, self.s.parentStyleSheet)
        self.assertEqual(u'', self.s.title)
        
        # check that type is readonly
        self.assertRaises(AttributeError, self.r.__setattr__, 'href', 'x')
        self.assertRaises(AttributeError, self.r.__setattr__, 'parentStyleSheet', 'x')
        self.assertRaises(AttributeError, self.r.__setattr__, 'ownerNode', 'x')
        self.assertRaises(AttributeError, self.r.__setattr__, 'type', 'x')

    def test_iter(self):
        "CSSStyleSheet.__iter__()"
        s = cssutils.css.CSSStyleSheet()
        s.cssText = '''@import "x";@import "y";@namespace "u";'''
        types = [cssutils.css.CSSRule.IMPORT_RULE,
                 cssutils.css.CSSRule.IMPORT_RULE,
                 cssutils.css.CSSRule.NAMESPACE_RULE]
        for i, rule in enumerate(s):
            self.assertEqual(rule, s.cssRules[i])
            self.assertEqual(rule.type, types[i])

    def test_refs(self):
        """CSSStylesheet references"""
        s = cssutils.parseString('a {}')
        rules = s.cssRules
        self.assertEqual(s.cssRules[0].parentStyleSheet, s)
        self.assertEqual(rules[0].parentStyleSheet, s)

        # set cssText
        s.cssText = 'b{}'
        
        # from 0.9.7b1
        self.assertNotEqual(rules, s.cssRules)

        # set cssRules 
        s.cssRules = cssutils.parseString('''
            @charset "ascii";
            /**/
            @import "x";
            @namespace "http://example.com/ns0";
            @media all {
                a { color: green; }
                }
            @font-face {
                font-family: x;
                }
            @page {
                font-family: Arial;
                }
            @x;
            b {}').cssRules''').cssRules
        # new object
        self.assertNotEqual(rules, s.cssRules)
        for i, r in enumerate(s.cssRules):
            self.assertEqual(r.parentStyleSheet, s)

        # namespaces
        s = cssutils.parseString('@namespace "http://example.com/ns1"; a {}')
        namespaces = s.namespaces
        self.assertEqual(s.namespaces.items(), [(u'', 'http://example.com/ns1')])
        s.cssText = '@namespace x "http://example.com/ns2"; x|a {}'
        # not anymore!
        self.assertNotEqual(namespaces, s.namespaces)
        self.assertEqual(s.namespaces.items(), [(u'x', 'http://example.com/ns2')])
        
        # variables
        s = cssutils.parseString(u'@variables { a:1}')
        vars1 = s.variables
        self.assertEqual(vars1[u'a'], u'1')
        
        s = cssutils.parseString(u'@variables { a:2}')
        vars2 = s.variables
        self.assertNotEqual(vars1, vars2)
        self.assertEqual(vars1[u'a'], u'1')
        self.assertEqual(vars2[u'a'], u'2')

    def test_cssRules(self):
        "CSSStyleSheet.cssRules"
        s = cssutils.parseString('/*1*/a {x:1}')
        self.assertEqual(2, s.cssRules.length)
        del s.cssRules[0]
        self.assertEqual(1, s.cssRules.length)
        s.cssRules.append('/*2*/')
        self.assertEqual(2, s.cssRules.length)
        s.cssRules.extend(cssutils.parseString('/*3*/x {y:2}').cssRules)
        self.assertEqual(4, s.cssRules.length)
        self.assertEqual(u'a {\n    x: 1\n    }\n/*2*/\n/*3*/\nx {\n    y: 2\n    }', 
                         s.cssText)
        
        for r in s.cssRules:
            self.assertEqual(r.parentStyleSheet, s)

    def test_cssText(self):
        "CSSStyleSheet.cssText"
        tests = {
            u'': None,
            # @charset
            u'@charset "ascii";\n@import "x";': None,
            u'@charset "ascii";\n@media all {}': u'@charset "ascii";',
            u'@charset "ascii";\n@x;': None,
            u'@charset "ascii";\na {\n    x: 1\n    }': None,
            # @import
            u'@x;\n@import "x";': None,
            u'@import "x";\n@import "y";': None,
            u'@import "x";\n@media all {}': u'@import "x";',
            u'@import "x";\n@x;': None,
            u'@import "x";\na {\n    x: 1\n    }': None,
            # @namespace
            u'@x;\n@namespace a "x";': None,
            u'@namespace a "x";\n@namespace b "y";': None,
            u'@import "x";\n@namespace a "x";\n@media all {}': 
                u'@import "x";\n@namespace a "x";',
            u'@namespace a "x";\n@x;': None,
            u'@namespace a "x";\na {\n    x: 1\n    }': None,
            u"""@namespace url("e1");
                @namespace url("e2");
                @namespace x url("x1");
                @namespace x url("x2");
                test{color: green}
                x|test {color: green}""": """@namespace "e2";
@namespace x "x2";
test {
    color: green
    }
x|test {
    color: green
    }"""
#            ur'\1 { \2: \3 }': ur'''\x01 {
#    \x02: \x03
#    }''',
#            ur'''
#            \@ { \@: \@ }
#            \1 { \2: \3 }
#            \{{\::\;;}
#            ''': ur'''\@ {
#    \@: \@
#    }
#\1 {
#    \2: \3
#    }
#\{
#    {\:: \;
#    }'''
            }
        self.do_equal_r(tests)
        self.do_equal_p(tests)

        s = cssutils.css.CSSStyleSheet()
        s.cssText = u'''@charset "ascii";@import "x";@namespace a "x";
        @media all {/*1*/}@page {margin: 0}a {\n    x: 1\n    }@unknown;/*comment*/'''
        for r in s.cssRules:
            self.assertEqual(s, r.parentStyleSheet)

    def test_cssText_HierarchyRequestErr(self):
        "CSSStyleSheet.cssText HierarchyRequestErr"
        tests = {
            # @charset: only one and always 1st
            u' @charset "utf-8";': xml.dom.HierarchyRequestErr,
            u'@charset "ascii";@charset "ascii";': xml.dom.HierarchyRequestErr,            u'/*c*/@charset "ascii";': xml.dom.HierarchyRequestErr,
            u'@import "x"; @charset "ascii";': xml.dom.HierarchyRequestErr,
            u'@namespace a "x"; @charset "ascii";': xml.dom.HierarchyRequestErr,
            u'@media all {} @charset "ascii";': xml.dom.HierarchyRequestErr,
            u'@page {} @charset "ascii";': xml.dom.HierarchyRequestErr,
            u'a {} @charset "ascii";': xml.dom.HierarchyRequestErr,

            # @import: before @namespace, @media, @page, sr
            u'@namespace a "x"; @import "x";': xml.dom.HierarchyRequestErr,
            u'@media all {} @import "x";': xml.dom.HierarchyRequestErr,
            u'@page {} @import "x";': xml.dom.HierarchyRequestErr,
            u'a {} @import "x";': xml.dom.HierarchyRequestErr,

            # @namespace: before @media, @page, sr
            u'@media all {} @namespace a "x";': xml.dom.HierarchyRequestErr,
            u'@page {} @namespace a "x";': xml.dom.HierarchyRequestErr,
            u'a {} @namespace a "x";': xml.dom.HierarchyRequestErr,
            }
        self.do_raise_r(tests)
        self.do_raise_p(tests)

    def test_cssText_SyntaxErr(self):
        """CSSStyleSheet.cssText SyntaxErr

        for single {, } or ;
        """
        tests = {
            u'{': xml.dom.SyntaxErr,
            u'}': xml.dom.SyntaxErr,
            u';': xml.dom.SyntaxErr,
            u'@charset "ascii";{': xml.dom.SyntaxErr,
            u'@charset "ascii";}': xml.dom.SyntaxErr,
            u'@charset "ascii";;': xml.dom.SyntaxErr,
            }
        self.do_raise_r(tests)
        self.do_raise_p(tests)

    def test_encoding(self):
        "CSSStyleSheet.encoding"
        self.s.cssText=''
        self.assertEqual('utf-8', self.s.encoding)

        self.s.encoding = 'ascii'
        self.assertEqual('ascii', self.s.encoding)
        self.assertEqual(1, self.s.cssRules.length)
        self.assertEqual('ascii', self.s.cssRules[0].encoding)

        self.s.encoding = None
        self.assertEqual('utf-8', self.s.encoding)
        self.assertEqual(0, self.s.cssRules.length)

        self.s.encoding = 'UTF-8'
        self.assertEqual('utf-8', self.s.encoding)
        self.assertEqual(1, self.s.cssRules.length)

        self.assertRaises(xml.dom.SyntaxErr, self.s._setEncoding,
                          'INVALID ENCODING')
        self.assertEqual('utf-8', self.s.encoding)
        self.assertEqual(1, self.s.cssRules.length)

    def test_namespaces1(self):
        "CSSStyleSheet.namespaces.namespaces"
        # tests for namespaces internal methods
        s = cssutils.css.CSSStyleSheet()
        self.assertEqual(0, len(s.namespaces))
        
        css = u'''@namespace "default";
@namespace ex "example";
@namespace ex2 "example";
ex2|x { top: 0 }'''
        expcss = u'''@namespace "default";
@namespace ex2 "example";
ex2|x {
    top: 0
    }'''
        s.cssText = css
        self.assertEqual(s.cssText, expcss)
        self.assertEqual(s.namespaces.namespaces,
                         { u'': u'default', u'ex2': u'example'})

        # __contains__
        self.assertTrue('' in s.namespaces)
        self.assertTrue('ex2' in s.namespaces)
        self.assertFalse('NOTSET' in s.namespaces)
        # __delitem__
        self.assertRaises(xml.dom.NoModificationAllowedErr, 
                          s.namespaces.__delitem__, 'ex2')
        s.namespaces['del'] = 'del'
        del s.namespaces['del']
        self.assertRaises(xml.dom.NamespaceErr, s.namespaces.__getitem__, 'del')
        # __getitem__
        self.assertEquals('default', s.namespaces[''])
        self.assertEquals('example', s.namespaces['ex2'])
        self.assertRaises(xml.dom.NamespaceErr, s.namespaces.__getitem__, 'UNSET')
        # __iter__
        self.assertEquals(['', 'ex2'], [n for n in s.namespaces])
        # __len__
        self.assertEqual(2, len(s.namespaces))
        # __setitem__
        self.assertRaises(xml.dom.NoModificationAllowedErr, 
                          s.namespaces.__setitem__, 'ex2', 'NEWURI')
        s.namespaces['n1'] = 'new'
        self.assertEqual(s.namespaces.namespaces,
                         { u'': u'default', u'ex2': u'example', u'n1': 'new'})
        s.namespaces['n'] = 'new' # replaces prefix!
        self.assertEqual(s.namespaces.namespaces,
                         { u'': u'default', u'ex2': u'example', u'n': 'new'})
        # prefixForNamespaceURI
        self.assertEquals('', s.namespaces.prefixForNamespaceURI('default'))
        self.assertEquals('ex2', s.namespaces.prefixForNamespaceURI('example'))
        self.assertRaises(IndexError, 
                          s.namespaces.prefixForNamespaceURI, 'UNSET')
        # .keys
        self.assertEqual(set(s.namespaces.keys()), set(['', 'ex2', 'n']))
        # .get
        self.assertEqual('x', s.namespaces.get('UNKNOWN', 'x'))
        self.assertEqual('example', s.namespaces.get('ex2', 'not used defa'))
        
    def test_namespaces2(self):
        "CSSStyleSheet.namespaces"
        # tests using CSSStyleSheet.namespaces
        
        s = cssutils.css.CSSStyleSheet()
        css = '@namespace n "new";'
        # doubles will be removed
        s.insertRule(css + css)
        self.assertEqual(css, s.cssText)
        r = cssutils.css.CSSNamespaceRule(prefix='ex2', namespaceURI='example')
        s.insertRule(r)
        r = cssutils.css.CSSNamespaceRule(namespaceURI='default')
        s.insertRule(r)
        
        expcss = '''@namespace n "new";
@namespace ex2 "example";
@namespace "default";'''
        self.assertEqual(s.cssText, expcss)
        r.prefix = 'DEFAULT'
        expcss = '''@namespace n "new";
@namespace ex2 "example";
@namespace DEFAULT "default";'''
        self.assertEqual(s.cssText, expcss)

        # CSSMediaRule
        self.assertRaises(xml.dom.NamespaceErr, s.add, '@media all {x|a {left: 0}}')
        mcss = '@media all {\n    ex2|SEL1 {\n        left: 0\n        }\n    }'
        s.add(mcss)
        expcss += '\n' + mcss
        self.assertEqual(s.cssText, expcss)

        # CSSStyleRule
        self.assertRaises(xml.dom.NamespaceErr, s.add, 'x|a {top: 0}')
        scss = 'n|SEL2 {\n    top: 0\n    }'
        s.add(scss)
        expcss += '\n' + scss
        self.assertEqual(s.cssText, expcss)
        
        mr = s.cssRules[3]
        sr = s.cssRules[4]

        # SelectorList @media
        self.assertRaises(xml.dom.NamespaceErr, 
                          mr.cssRules[0]._setSelectorText, 'x|b')
        oldsel, newsel = mr.cssRules[0].selectorText, 'n|SEL3, a'
        mr.cssRules[0].selectorText = newsel
        expcss = expcss.replace(oldsel, newsel)
        self.assertEqual(s.cssText, expcss)
        # SelectorList stylerule
        self.assertRaises(xml.dom.NamespaceErr, 
                          sr._setSelectorText, 'x|b')
        oldsel, newsel = sr.selectorText, 'ex2|SEL4, a'
        sr.selectorText = newsel
        expcss = expcss.replace(oldsel, newsel)
        self.assertEqual(s.cssText, expcss)

        # Selector @media
        self.assertRaises(xml.dom.NamespaceErr, 
                          mr.cssRules[0].selectorList.append, 'x|b')
        oldsel, newsel = mr.cssRules[0].selectorText, 'ex2|SELMR'
        mr.cssRules[0].selectorList.append(newsel)
        expcss = expcss.replace(oldsel, oldsel + ', ' + newsel)
        self.assertEqual(s.cssText, expcss)
        # Selector stylerule
        self.assertRaises(xml.dom.NamespaceErr, 
                          sr.selectorList.append, 'x|b')
        oldsel, newsel = sr.selectorText, 'ex2|SELSR'
        sr.selectorList.append(newsel)
        expcss = expcss.replace(oldsel, oldsel + ', ' + newsel)
        self.assertEqual(s.cssText, expcss)
        
        self.assertEqual(s.cssText, u'''@namespace n "new";
@namespace ex2 "example";
@namespace DEFAULT "default";
@media all {
    n|SEL3, a, ex2|SELMR {
        left: 0
        }
    }
ex2|SEL4, a, ex2|SELSR {
    top: 0
    }''')

    def test_namespaces3(self):
        "CSSStyleSheet.namespaces 3"
        # tests setting namespaces with new {}
        s = cssutils.css.CSSStyleSheet()
        css = u'h|a { top: 0 }'
        self.assertRaises(xml.dom.NamespaceErr, s.add, css)

        s.add('@namespace x "html";')
        self.assert_(s.namespaces['x'] == 'html')

        r = cssutils.css.CSSStyleRule()
        r.cssText = ((css, {'h': 'html'}))
        s.add(r) # uses x as set before! h is temporary only
        self.assertEqual(s.cssText, '@namespace x "html";\nx|a {\n    top: 0\n    }')

        # prefix is now "x"!
        self.assertRaises(xml.dom.NamespaceErr, r.selectorList.append, 'h|b')
        self.assertRaises(xml.dom.NamespaceErr, r.selectorList.append, 'y|b')
        s.namespaces['y'] = 'html'
        r.selectorList.append('y|b')
        self.assertEqual(s.cssText,
            u'@namespace y "html";\ny|a, y|b {\n    top: 0\n    }')

        self.assertRaises(xml.dom.NoModificationAllowedErr, 
                          s.namespaces.__delitem__, 'y')
        self.assertEqual(s.cssText,
            u'@namespace y "html";\ny|a, y|b {\n    top: 0\n    }')
        
        s.cssRules[0].prefix = ''
        self.assertEqual(s.cssText,
            u'@namespace "html";\na, b {\n    top: 0\n    }')

        # remove need of namespace
        s.cssRules[0].prefix = 'x'
        s.cssRules[1].selectorText = 'a, b'
        self.assertEqual(s.cssText,
            u'@namespace x "html";\na, b {\n    top: 0\n    }')


    def test_namespaces4(self):
        "CSSStyleSheet.namespaces 4"
        # tests setting namespaces with new {}
        s = cssutils.css.CSSStyleSheet()
        self.assertEqual({}, s.namespaces.namespaces)

        s.namespaces.namespaces['a'] = 'no setting possible'
        self.assertEqual({}, s.namespaces.namespaces)
         
        s.namespaces[None] = 'default'
        self.assertEqual({u'': 'default'}, s.namespaces.namespaces)

        del s.namespaces['']
        self.assertEqual({}, s.namespaces.namespaces)

        s.namespaces[''] = 'default'
        self.assertEqual({u'': 'default'}, s.namespaces.namespaces)

        del s.namespaces[None]
        self.assertEqual({}, s.namespaces.namespaces)

        s.namespaces['p'] = 'uri'
        # cannot use namespaces.namespaces
        del s.namespaces.namespaces['p'] 
        self.assertEqual({u'p': 'uri'}, s.namespaces.namespaces)
        
        self.assertRaisesMsg(xml.dom.NamespaceErr, u"Prefix 'undefined' not found.", 
                             s.namespaces.__delitem__, 'undefined')
        
    def test_namespaces5(self):
        "CSSStyleSheet.namespaces 5"
        # unknown namespace
        s = cssutils.parseString('a|a { color: red }')
        self.assertEqual(u'', s.cssText)
        
        s = cssutils.css.CSSStyleSheet()
        self.assertRaisesMsg(xml.dom.NamespaceErr, "Prefix u'a' not found.", 
                             s._setCssText, 'a|a { color: red }')        
        
    def test_deleteRuleIndex(self):
        "CSSStyleSheet.deleteRule(index)"
        self.s.cssText = u'@charset "ascii"; @import "x"; @x; a {\n    x: 1\n    }@y;'
        self.assertEqual(5, self.s.cssRules.length)

        self.assertRaises(xml.dom.IndexSizeErr, self.s.deleteRule, 5)

        # end -1
        # check parentStyleSheet
        r = self.s.cssRules[-1]
        self.assertEqual(self.s, r.parentStyleSheet)
        self.s.deleteRule(-1)
        self.assertEqual(None, r.parentStyleSheet)

        self.assertEqual(4, self.s.cssRules.length)
        self.assertEqual(
            u'@charset "ascii";\n@import "x";\n@x;\na {\n    x: 1\n    }', self.s.cssText)
        # beginning
        self.s.deleteRule(0)
        self.assertEqual(3, self.s.cssRules.length)
        self.assertEqual(u'@import "x";\n@x;\na {\n    x: 1\n    }', self.s.cssText)
        # middle
        self.s.deleteRule(1)
        self.assertEqual(2, self.s.cssRules.length)
        self.assertEqual(u'@import "x";\na {\n    x: 1\n    }', self.s.cssText)
        # end
        self.s.deleteRule(1)
        self.assertEqual(1, self.s.cssRules.length)
        self.assertEqual(u'@import "x";', self.s.cssText)

    def test_deleteRule(self):
        "CSSStyleSheet.deleteRule(rule)"
        s = cssutils.css.CSSStyleSheet()
        s.cssText='''
        @namespace x "http://example.com";
        a { color: red; }
        b { color: blue; }
        c { color: green; }
        '''
        n, s1, s2, s3 = s.cssRules
        
        r = cssutils.css.CSSStyleRule()
        self.assertRaises(xml.dom.IndexSizeErr, s.deleteRule, r)

        self.assertEqual(4, s.cssRules.length)
        s.deleteRule(n)
        self.assertEqual(3, s.cssRules.length)
        self.assertEqual(s.cssText, 'a {\n    color: red\n    }\nb {\n    color: blue\n    }\nc {\n    color: green\n    }')
        self.assertRaises(xml.dom.IndexSizeErr, s.deleteRule, n)
        s.deleteRule(s2)
        self.assertEqual(2, s.cssRules.length)
        self.assertEqual(s.cssText, 'a {\n    color: red\n    }\nc {\n    color: green\n    }')
        self.assertRaises(xml.dom.IndexSizeErr, s.deleteRule, s2)

    def _gets(self):
        # complete
        self.cr = cssutils.css.CSSCharsetRule('ascii')
        self.c = cssutils.css.CSSComment(u'/*c*/')
        self.ur = cssutils.css.CSSUnknownRule('@x;')
        self.ir = cssutils.css.CSSImportRule('x')
        self.nr = cssutils.css.CSSNamespaceRule('uri', 'p')
        self.mr = cssutils.css.CSSMediaRule()
        self.mr.cssText = u'@media all { @m; }'
        self.pr = cssutils.css.CSSPageRule()
        self.pr.style = u'margin: 0;'
        self.sr = cssutils.css.CSSStyleRule()
        self.sr.cssText = 'a {\n    x: 1\n    }'

        s = cssutils.css.CSSStyleSheet()
        s.insertRule(self.cr) # 0
        s.insertRule(self.ir) # 1
        s.insertRule(self.nr) # 2
        s.insertRule(self.mr) # 3
        s.insertRule(self.sr) # 4
        s.insertRule(self.mr) # 5
        s.insertRule(self.pr) # 6
        s.insertRule(self.sr) # 7
        self.assertEqual(u'@charset "ascii";\n@import url(x);\n@namespace p "uri";\n@media all {\n    @m;\n    }\na {\n    x: 1\n    }\n@media all {\n    @m;\n    }\n@page {\n    margin: 0\n    }\na {\n    x: 1\n    }', s.cssText)
        return s, s.cssRules.length

    def test_add(self):
        "CSSStyleSheet.add()"
        full = cssutils.css.CSSStyleSheet()
        sheet = cssutils.css.CSSStyleSheet()
        css = ['@charset "ascii";',
               '@import "x";',
               '@namespace p "u";',
               '@page {\n    left: 0\n    }',
               '@font-face {\n    src: local(x)\n    }',
               '@media all {\n    a {\n        color: red\n        }\n    }',
               'a {\n    color: green\n    }',
               '/*comment*/',
               '@x;'
               ]
               
        fullcss = u'\n'.join(css)
        full.cssText = fullcss
        self.assertEqual(full.cssText, fullcss)
        for i, line in enumerate(css):
            # sheet without same ruletype
            before = css[:i]
            after = css[i+1:]
            sheet.cssText = u''.join(before + after)
            
            index = sheet.add(line)
            if i < 3:
                # specific insertion point
                self.assertEqual(fullcss, sheet.cssText)
                self.assertEqual(i, index)
            else:
                # end of sheet
                expected = before
                expected.extend(after)
                expected.append(line)
                self.assertEqual(u'\n'.join(expected), sheet.cssText)
                self.assertEqual(len(expected)-1, index) # no same rule present

            # sheet with the same ruletype
            if i == 1: line = '@import "x2";'
            if i == 2: line = '@namespace p2 "u2";'
            
            full.cssText = fullcss
            index = full.add(line)
            if i < 1:
                self.assertEqual(fullcss, sheet.cssText)
                self.assertEqual(i, index) # no same rule present
            else:
                if i < 3:
                    # in order
                    expected = css[:i+1] # including same rule
                    expected.append(line)
                    expected.extend(css[i+1:])
                    expectedindex = i+1
                else:
                    # just appended as no order needed
                    expected = css[:]
                    expected.append(line)
                    expectedindex = len(expected) - 1

                self.assertEqual(u'\n'.join(expected), full.cssText)
                self.assertEqual(expectedindex, index) # no same rule present

    def test_addimport(self):
        p = cssutils.CSSParser(fetcher=lambda url: (None, '/**/')) 

        cssrulessheet = p.parseString('@import "example.css";')
        imports = (
            '@import "example.css";', # string
            cssutils.css.CSSImportRule(href="example.css"), # CSSRule
            cssrulessheet.cssRules # CSSRuleList
            )
        for imp in imports:
            sheet = p.parseString('', href='http://example.com')
            sheet.add(imp)
            added = sheet.cssRules[0]
            self.assertEqual(sheet, added.parentStyleSheet)
            self.assertEqual(u'example.css', added.href)
            self.assertEqual(u'utf-8', added.styleSheet.encoding)
            self.assertEqual(u'/**/', added.styleSheet.cssText)

        cssrulessheet = p.parseString('@import "example.css";')
        imports = (
            ('@import "example.css";', 'ascii'), # string
            (cssutils.css.CSSImportRule(href="example.css"), 'ascii'), # CSSRule
            # got encoding from old parent already
            (cssrulessheet.cssRules, 'utf-8') # CSSRuleList
            )
        for imp, enc in imports:
            sheet = p.parseString('', href='http://example.com', encoding='ascii')
            sheet.add(imp)
            added = sheet.cssRules[1]
            self.assertEqual(sheet, added.parentStyleSheet)
            self.assertEqual(u'example.css', added.href)
            self.assertEqual(enc, added.styleSheet.encoding)
            if enc == 'ascii':
                self.assertEqual(u'@charset "ascii";\n/**/', added.styleSheet.cssText)
            else:
                self.assertEqual(u'/**/', added.styleSheet.cssText)
            
        # if styleSheet is already there encoding is not set new
        impsheet = p.parseString('@import "example.css";')
        imp = impsheet.cssRules[0]
        sheet = p.parseString('', href='http://example.com', encoding='ascii')
        sheet.add(imp)
        added = sheet.cssRules[1]
        self.assertEqual(sheet, added.parentStyleSheet)
        self.assertEqual(u'example.css', added.href)
        self.assertEqual(u'utf-8', added.styleSheet.encoding)
        self.assertEqual(u'/**/', added.styleSheet.cssText)

    def test_insertRule(self):
        "CSSStyleSheet.insertRule()"
        s, L = self._gets()

        # INVALID index
        self.assertRaises(xml.dom.IndexSizeErr,
                  s.insertRule, self.sr, -1)
        self.assertRaises(xml.dom.IndexSizeErr,
                  s.insertRule, self.sr, s.cssRules.length + 1)
        #   check if rule is really not in
        self.assertEqual(L, s.cssRules.length)

        # insert string
        s.insertRule('a {}')
        self.assertEqual(L+1, s.cssRules.length)
        # insert rule
        s.insertRule(self.sr)
        self.assertEqual(L+2, s.cssRules.length)
        # insert rulelist
        s2, L2 = self._gets()
        rulelist = s2.cssRules
        del rulelist[:-2]
        s.insertRule(rulelist)
        self.assertEqual(L+2 + 2, s.cssRules.length)

    def _insertRule(self, rules, notbefore, notafter, anywhere, 
                    checkdoubles=True):
        """
        helper
        test if any rule in rules cannot be inserted before rules in before
        or after rules in after but before and after rules in anywhere
        """
        for rule in rules:
            for r in notbefore:
                s = cssutils.css.CSSStyleSheet()
                s.insertRule(r)
                self.assertRaises(xml.dom.HierarchyRequestErr,
                                  s.insertRule, rule, 0)
                s = cssutils.css.CSSStyleSheet()
                s.add(r)
                self.assertRaises(xml.dom.HierarchyRequestErr,
                                  s.insertRule, rule, 0)
            for r in notafter:
                s = cssutils.css.CSSStyleSheet()
                s.insertRule(r)
                self.assertRaises(xml.dom.HierarchyRequestErr,
                                  s.insertRule, rule, 1)
                s = cssutils.css.CSSStyleSheet()
                s.add(r)
                s.add(rule) # never raises
                self.assertEqual(s, r.parentStyleSheet)

            for r in anywhere:
                s = cssutils.css.CSSStyleSheet()
                s.insertRule(r)
                s.insertRule(rule, 0) # before
                s.insertRule(rule) # after
                if checkdoubles:
                    self.assertEqual(s.cssRules.length, 3)
                self.assertEqual(s, r.parentStyleSheet)

    def test_insertRule_charset(self):
        "CSSStyleSheet.insertRule(@charset)"
        s, L = self._gets()
        notbefore = (self.cr,)
        notafter = (self.cr, self.ir, self.nr, self.mr, self.pr, self.sr,
                    self.c, self.ur)
        anywhere = ()
        self._insertRule((self.cr,),
                         notbefore, notafter, anywhere)

    def test_insertRule_import(self):
        "CSSStyleSheet.insertRule(@import)"
        s, L = self._gets()
        notbefore = (self.cr,)
        notafter = (self.nr, self.pr, self.mr, self.sr)
        anywhere = (self.c, self.ur, self.ir)
        self._insertRule((self.ir,),
                         notbefore, notafter, anywhere)

    def test_insertRule_namespace(self):
        "CSSStyleSheet.insertRule(@namespace)"
        s, L = self._gets()
        notbefore = (self.cr, self.ir)
        notafter = (self.pr, self.mr, self.sr)
        anywhere = (self.c, self.ur, self.nr)
        self._insertRule((self.nr,), notbefore, notafter, anywhere, 
                         checkdoubles=False)

    def test_insertRule_media_page_style(self):
        "CSSStyleSheet.insertRule(@media, @page, stylerule)"
        s, L = self._gets()
        notbefore = (self.cr, self.ir, self.nr)
        notafter = ()
        anywhere = (self.c, self.ur, self.mr, self.pr, self.sr)
        self._insertRule((self.pr, self.mr, self.sr),
                         notbefore, notafter, anywhere)

    def test_insertRule_unknownandcomment(self):
        "CSSStyleSheet.insertRule(@ unknown, comment)"
        s, L = self._gets()
        notbefore = (self.cr,)
        notafter = ()
        anywhere = (self.c, self.ur, self.ir, self.nr, self.mr, self.pr,
                    self.sr)
        self._insertRule((self.ur,),
                         notbefore, notafter, anywhere)

    def test_HTMLComments(self):
        "CSSStyleSheet CDO CDC"
        css = u'''body { color: red }
<!-- comment -->
body { color: blue }
body { color: pink }
<!-- comment -->
body { color: green }
'''
        exp = u'''body {
    color: red
    }
body {
    color: pink
    }'''
        sheet = cssutils.parseString(css)
        self.assertEqual(sheet.cssText, exp)

    def test_incomplete(self):
        "CSSStyleRule (incomplete)"
        tests = {
            u'@import "a': u'@import "a";', # no }
            u'a { x: 1': u'a {\n    x: 1\n    }', # no }
            u'a { font-family: "arial sans': # no "
                u'a {\n    font-family: "arial sans"\n    }',
        }
        self.do_equal_p(tests) # parse

    def test_NoModificationAllowedErr(self):
        "CSSStyleSheet NoModificationAllowedErr"
        css = cssutils.css.CSSStyleSheet(readonly=True)

        self.assertEqual(True, css._readonly) # internal...

        self.assertRaises(xml.dom.NoModificationAllowedErr,
                          css._setCssText, u'@x;')
        self.assertRaises(xml.dom.NoModificationAllowedErr,
                          css.insertRule, self.rule)
        self.assertRaises(xml.dom.NoModificationAllowedErr,
                          css.insertRule, self.rule, 0)
        self.assertRaises(xml.dom.NoModificationAllowedErr,
                          css.deleteRule, 0)

    def test_reprANDstr(self):
        "CSSStyleSheet.__repr__(), .__str__()"
        href = 'file:foo.css'
        title = 'title-of-css'

        s = cssutils.css.CSSStyleSheet(href=href, title=title)

        self.assert_(href in str(s))
        self.assert_(title in str(s))

        s2 = eval(repr(s))
        self.assert_(isinstance(s2, s.__class__))
        self.assert_(href == s2.href)
        self.assert_(title == s2.title)


if __name__ == '__main__':
    import unittest
    unittest.main()
