"""Testcases for cssutils.css.cssstyledelaration.CSSStyleDeclaration."""
__version__ = '$Id: test_cssstyledeclaration.py 2015 2010-07-06 18:43:53Z cthedot $'

import xml.dom
import basetest
import cssutils

class CSSStyleDeclarationTestCase(basetest.BaseTestCase):

    def setUp(self):
        self.r = cssutils.css.CSSStyleDeclaration()

    def test_init(self):
        "CSSStyleDeclaration.__init__()"
        s = cssutils.css.CSSStyleDeclaration()
        self.assertEqual(u'', s.cssText)
        self.assertEqual(0, s.length)
        self.assertEqual(None, s.parentRule)

        s = cssutils.css.CSSStyleDeclaration(cssText='left: 0')
        self.assertEqual(u'left: 0', s.cssText)
        self.assertEqual('0', s.getPropertyValue('left'))

        sheet = cssutils.css.CSSStyleRule()
        s = cssutils.css.CSSStyleDeclaration(parentRule=sheet)
        self.assertEqual(sheet, s.parentRule)

        # should not be used but ordered parameter test 
        s = cssutils.css.CSSStyleDeclaration('top: 0', sheet)
        self.assertEqual(u'top: 0', s.cssText)
        self.assertEqual(sheet, s.parentRule)

    def test_items(self):
        "CSSStyleDeclaration[CSSName]"
        s = cssutils.css.CSSStyleDeclaration()
        name, value, priority = 'color', 'name', '' 
        s[name] = value
        self.assertEqual(value, s[name])
        self.assertEqual(value, s.__getattribute__(name))
        self.assertEqual(value, s.getProperty(name).value)
        self.assertEqual(priority, s.getProperty(name).priority)

        name, value, priority = 'UnKnown-ProPERTY', 'unknown value', 'important' 
        s[name] = (value, priority)
        self.assertEqual(value, s[name])
        self.assertEqual(value, s[name.lower()]) # will be normalized
        self.assertRaises(AttributeError, s.__getattribute__, name)
        self.assertEqual(value, s.getProperty(name).value)
        self.assertEqual(priority, s.getProperty(name).priority)

        name, value, priority = 'item', '1', '' 
        s[name] = value
        self.assertEqual(value, s[name])
        self.assertEqual(value, s.getProperty(name).value)
        self.assertEqual(priority, s.getProperty(name).priority)
        
        del s[name]
        self.assertEqual(u'', s[name])
        self.assertEqual(u'', s['never set'])
                
    def test__contains__(self):
        "CSSStyleDeclaration.__contains__(nameOrProperty)"
        s = cssutils.css.CSSStyleDeclaration(cssText=r'x: 1;\y: 2')
        for test in ('x', r'x', 'y', r'y'):
            self.assert_(test in s)
            self.assert_(test.upper() in s)
            self.assert_(cssutils.css.Property(test, '1') in s)
        self.assert_('z' not in s)
        self.assert_(cssutils.css.Property('z', '1') not in s)

    def test__iter__item(self):
        "CSSStyleDeclaration.__iter__ and .item"
        s = cssutils.css.CSSStyleDeclaration()
        s.cssText = ur'''
            color: red; c\olor: blue; CO\lor: green;
            left: 1px !important; left: 0;
            border: 0;
        '''
        # __iter__
        ps = []
        for p in s:
            ps.append((p.literalname, p.value, p.priority))
        self.assertEqual(len(ps), 3)
        self.assertEqual(ps[0], (ur'co\lor', 'green', ''))
        self.assertEqual(ps[1], (ur'left', '1px', 'important'))
        self.assertEqual(ps[2], (ur'border', '0', ''))
                
        # item 
        self.assertEqual(s.length, 3)
        self.assertEqual(s.item(0), u'color')
        self.assertEqual(s.item(1), u'left')
        self.assertEqual(s.item(2), u'border')
        self.assertEqual(s.item(10), u'')

    def test_keys(self):
        "CSSStyleDeclaration.keys()"
        s = cssutils.parseStyle('x:1; x:2; y:1')
        self.assertEqual(['x', 'y'], s.keys())
        self.assertEqual(s['x'], '2')
        self.assertEqual(s['y'], '1')
            
    def test_parse(self):
        "CSSStyleDeclaration parse"
        # error but parse
        tests = {
            # property names are caseinsensitive
            u'TOP:0': u'top: 0',
            u'top:0': u'top: 0',
            # simple escape
            u'c\\olor: red; color:green': u'color: green',
            u'color:g\\reen': u'color: g\\reen',
            # http://www.w3.org/TR/2009/CR-CSS2-20090423/syndata.html#illegalvalues
            u'color:green': u'color: green',
            u'color:green; color': u'color: green',
            u'color:red;   color; color:green': u'color: green',
            u'color:green; color:': u'color: green',
            u'color:red;   color:; color:green': u'color: green',
            u'color:green; color{;color:maroon}': u'color: green',
            u'color:red; color{;color:maroon}; color:green': u'color: green',
            # tantek hack
            ur'''color: red;
voice-family: "\"}\"";
voice-family:inherit;
color: green;''': 'voice-family: inherit;\ncolor: green',
            ur'''col\or: blue;
                font-family: 'Courier New Times
                color: red;
                color: green;''': u'color: green',
                
            # special IE hacks are not preserved anymore (>=0.9.5b3)
            u'/color: red; color: green': u'color: green',
            u'/ color: red; color: green': u'color: green',
            u'1px: red; color: green': u'color: green',
            u'0: red; color: green': u'color: green',
            u'1px:: red; color: green': u'color: green',
            ur'$top: 0': u'',
            ur'$: 0': u'', # really invalid!
            # unknown rule but valid
            u'@x;\ncolor: red': None, 
            u'@x {\n    }\ncolor: red': None,
            u'/**/\ncolor: red': None, 
            u'/**/\ncolor: red;\n/**/': None, 
            }
        cssutils.ser.prefs.keepAllProperties = False
        for test, exp in tests.items():
            sh = cssutils.parseString('a { %s }' % test)
            if exp is None:
                exp = u'%s' % test
            elif exp != u'':
                exp = u'%s' % exp
            self.assertEqual(exp, sh.cssRules[0].style.cssText)
        
        cssutils.ser.prefs.useDefaults()
        
    def test_serialize(self):
        "CSSStyleDeclaration serialize"
        s = cssutils.css.CSSStyleDeclaration()
        tests = {
            u'a:1 !important; a:2;b:1': (u'a: 1 !important;\nb: 1',
                                         u'a: 1 !important;\na: 2;\nb: 1')
        }
        for test, exp in tests.items():
            s.cssText = test
            cssutils.ser.prefs.keepAllProperties = False
            self.assertEqual(exp[0], s.cssText)
            cssutils.ser.prefs.keepAllProperties = True
            self.assertEqual(exp[1], s.cssText)
        
        cssutils.ser.prefs.useDefaults()

    def test_children(self):
        "CSSStyleDeclaration.children()"
        style = u'/*1*/color: red; color: green; @x;'
        types = [
            cssutils.css.CSSComment, 
            cssutils.css.Property,
            cssutils.css.Property,
            cssutils.css.CSSUnknownRule
        ] 
        def t(s):
            for i, x in enumerate(s.children()):
                self.assertEqual(types[i], type(x))
                self.assertEqual(x.parent, s)
                                    
        t(cssutils.parseStyle(style))
        t(cssutils.parseString(u'a {'+style+'}').cssRules[0].style)
        t(cssutils.parseString(u'@media all {a {'+style+'}}').cssRules[0].cssRules[0].style)
                
        s = cssutils.parseStyle(style)
        s['x'] = '0'
        self.assertEqual(s, s.getProperty('x').parent)
        s.setProperty('y', '1')
        self.assertEqual(s, s.getProperty('y').parent)

    def test_cssText(self):
        "CSSStyleDeclaration.cssText"
        # empty
        s = cssutils.css.CSSStyleDeclaration()
        tests = {
            u'': u'',
            u' ': u'',
            u' \t \n  ': u'',
            u'/*x*/': u'/*x*/'
            }
        for test, exp in tests.items():
            s.cssText = 'left: 0;' # dummy to reset s
            s.cssText = test
            self.assertEqual(exp, s.cssText)

        # normal
        s = cssutils.css.CSSStyleDeclaration()
        tests = {
            u'left: 0': u'left: 0',
            u'left:0': u'left: 0',
            u' left : 0 ': u'left: 0',
            u'left: 0;': u'left: 0',
            u'left: 0 !important ': u'left: 0 !important',
            u'left:0!important': u'left: 0 !important',
            u'left: 0; top: 1': u'left: 0;\ntop: 1',
            # comments
            # TODO: spaces?
            u'/*1*//*2*/left/*3*//*4*/:/*5*//*6*/0/*7*//*8*/!/*9*//*a*/important/*b*//*c*/;': 
                u'/*1*/\n/*2*/\nleft/*3*//*4*/: /*5*/ /*6*/ 0 /*7*/ /*8*/ !/*9*//*a*/important/*b*//*c*/',
            u'/*1*/left: 0;/*2*/ top: 1/*3*/':
                u'/*1*/\nleft: 0;\n/*2*/\ntop: 1 /*3*/',
            u'left:0; top:1;': u'left: 0;\ntop: 1',
            u'/*1*/left: 0;/*2*/ top: 1;/*3*/':
                u'/*1*/\nleft: 0;\n/*2*/\ntop: 1;\n/*3*/',
            # WS
            u'left:0!important;margin:1px 2px 3px 4px!important;': u'left: 0 !important;\nmargin: 1px 2px 3px 4px !important',
            u'\n\r\f\t left\n\r\f\t :\n\r\f\t 0\n\r\f\t !\n\r\f\t important\n\r\f\t ;\n\r\f\t margin\n\r\f\t :\n\r\f\t 1px\n\r\f\t 2px\n\r\f\t 3px\n\r\f\t 4px;': 
            u'left: 0 !important;\nmargin: 1px 2px 3px 4px',
            }
        for test, exp in tests.items():
            s.cssText = test
            self.assertEqual(exp, s.cssText)

        # exception
        tests = {
            u'top': xml.dom.SyntaxErr,
            u'top:': xml.dom.SyntaxErr,
            u'top : ': xml.dom.SyntaxErr,
            u'top:!important': xml.dom.SyntaxErr,
            u'top:!important;': xml.dom.SyntaxErr,
            u'top:;': xml.dom.SyntaxErr,
            u'top 0': xml.dom.SyntaxErr,
            u'top 0;': xml.dom.SyntaxErr,

            u':': xml.dom.SyntaxErr,
            u':0': xml.dom.SyntaxErr,
            u':0;': xml.dom.SyntaxErr,
            u':0!important': xml.dom.SyntaxErr,
            u':;': xml.dom.SyntaxErr,
            u': ;': xml.dom.SyntaxErr,
            u':!important;': xml.dom.SyntaxErr,
            u': !important;': xml.dom.SyntaxErr,

            u'0': xml.dom.SyntaxErr,
            u'0!important': xml.dom.SyntaxErr,
            u'0!important;': xml.dom.SyntaxErr,
            u'0;': xml.dom.SyntaxErr,

            u'!important': xml.dom.SyntaxErr,
            u'!important;': xml.dom.SyntaxErr,

            u';': xml.dom.SyntaxErr,
            }
        self.do_raise_r(tests)

    def test_getCssText(self):
        "CSSStyleDeclaration.getCssText(separator)"
        s = cssutils.css.CSSStyleDeclaration(cssText=u'a:1;b:2')
        self.assertEqual(u'a: 1;\nb: 2', s.getCssText())
        self.assertEqual(u'a: 1;b: 2', s.getCssText(separator=u''))
        self.assertEqual(u'a: 1;/*x*/b: 2', s.getCssText(separator=u'/*x*/'))

    def test_parentRule(self):
        "CSSStyleDeclaration.parentRule"
        s = cssutils.css.CSSStyleDeclaration()
        sheet = cssutils.css.CSSStyleRule()
        s.parentRule = sheet
        self.assertEqual(sheet, s.parentRule)

        sheet = cssutils.parseString(u'a{x:1}')
        s = sheet.cssRules[0]
        d = s.style
        self.assertEqual(s, d.parentRule)
        
        s = cssutils.parseString('''
        @font-face {
            font-weight: bold;
            }
        a {
            font-weight: bolder;
            }
        @page {
            font-weight: bolder;    
            }
        ''')
        for r in s:
            self.assertEqual(r.style.parentRule, r)

    def test_getProperty(self):
        "CSSStyleDeclaration.getProperty"
        s = cssutils.css.CSSStyleDeclaration()
        P = cssutils.css.Property
        s.cssText = ur'''
            color: red; c\olor: blue; CO\lor: green;
            left: 1px !important; left: 0;
            border: 0;
        '''
        self.assertEqual(s.getProperty('color').cssText, ur'co\lor: green')
        self.assertEqual(s.getProperty(r'COLO\r').cssText, ur'co\lor: green')
        self.assertEqual(s.getProperty('left').cssText, ur'left: 1px !important')
        self.assertEqual(s.getProperty('border').cssText, ur'border: 0')

    def test_getProperties(self):
        "CSSStyleDeclaration.getProperties()"
        s = cssutils.css.CSSStyleDeclaration(cssText=
                                             u'/*1*/y:0;x:a !important;y:1; \\x:b;')
        tests = {
            # name, all
            (None, False): [(u'y', u'1', u''), 
                            (u'x', u'a', u'important')],
            (None, True): [(u'y', u'0', u''),
                           (u'x', u'a', u'important'),
                           (u'y', u'1', u''), 
                           (u'\\x', u'b', u'')
                           ],
            ('x', False): [(u'x', u'a', u'important')],
            ('\\x', False): [(u'x', u'a', u'important')],
            ('x', True): [(u'x', u'a', u'important'),
                           (u'\\x', u'b', u'')],
            ('\\x', True): [(u'x', u'a', u'important'),
                           (u'\\x', u'b', u'')],
            }
        for test in tests:
            name, all = test
            expected = tests[test]
            actual = s.getProperties(name, all)
            self.assertEqual(len(expected), len(actual))
            for i, ex in enumerate(expected):
                a = actual[i]
                self.assertEqual(ex, (a.literalname, a.value, a.priority))
        
        # order is be effective properties set
        s = cssutils.css.CSSStyleDeclaration(cssText=
                                             u'a:0;b:1;a:1')
        self.assertEqual(u'ba', u''.join([p.name for p in s]))
                
    def test_getPropertyCSSValue(self):
        "CSSStyleDeclaration.getPropertyCSSValue()"
        s = cssutils.css.CSSStyleDeclaration(cssText='color: red;c\\olor: green')
        self.assertEqual(u'green', s.getPropertyCSSValue('color').cssText)
        self.assertEqual(u'green', s.getPropertyCSSValue('c\\olor').cssText)
        self.assertEqual(u'red', s.getPropertyCSSValue('color', False).cssText)
        self.assertEqual(u'green', s.getPropertyCSSValue('c\\olor', False).cssText)
#        # shorthand CSSValue should be None
#        SHORTHAND = [
#            u'background',
#            u'border',
#            u'border-left', u'border-right',
#            u'border-top', u'border-bottom',
#            u'border-color', u'border-style', u'border-width',
#            u'cue',
#            u'font',
#            u'list-style',
#            u'margin',
#            u'outline',
#            u'padding',
#            u'pause']
#        for short in SHORTHAND:
#            s.setProperty(short, u'inherit')
#            self.assertEqual(None, s.getPropertyCSSValue(short))

    def test_getPropertyValue(self):
        "CSSStyleDeclaration.getPropertyValue()"
        s = cssutils.css.CSSStyleDeclaration()
        self.assertEqual(u'', s.getPropertyValue('unset'))

        s.setProperty(u'left', '0')
        self.assertEqual(u'0', s.getPropertyValue('left'))

        s.setProperty(u'border', '1px  solid  green')
        self.assertEqual(u'1px solid green', s.getPropertyValue('border'))

        s = cssutils.css.CSSStyleDeclaration(cssText='color: red;c\\olor: green')
        self.assertEqual(u'green', s.getPropertyValue('color'))
        self.assertEqual(u'green', s.getPropertyValue('c\\olor'))
        self.assertEqual(u'red', s.getPropertyValue('color', False))
        self.assertEqual(u'green', s.getPropertyValue('c\\olor', False))

        tests = {
            ur'color: red; color: green': 'green',
            ur'c\olor: red; c\olor: green': 'green',
            ur'color: red; c\olor: green': 'green',
            ur'color: red !important; color: green !important': 'green',
            ur'color: green !important; color: red': 'green',
            }
        for test in tests:
            s = cssutils.css.CSSStyleDeclaration(cssText=test)
            self.assertEqual(tests[test], s.getPropertyValue('color'))

    def test_getPropertyPriority(self):
        "CSSStyleDeclaration.getPropertyPriority()"
        s = cssutils.css.CSSStyleDeclaration()
        self.assertEqual(u'', s.getPropertyPriority('unset'))

        s.setProperty(u'left', u'0', u'!important')
        self.assertEqual(u'important', s.getPropertyPriority('left'))

        s = cssutils.css.CSSStyleDeclaration(cssText=
            'x: 1 !important;\\x: 2;x: 3 !important;\\x: 4')
        self.assertEqual(u'important', s.getPropertyPriority('x'))
        self.assertEqual(u'important', s.getPropertyPriority('\\x'))
        self.assertEqual(u'important', s.getPropertyPriority('x', True))
        self.assertEqual(u'', s.getPropertyPriority('\\x', False))

    def test_removeProperty(self):
        "CSSStyleDeclaration.removeProperty()"
        cssutils.ser.prefs.useDefaults()
        s = cssutils.css.CSSStyleDeclaration()
        css = ur'\x:0 !important; x:1; \x:2; x:3'

        # normalize=True DEFAULT
        s.cssText = css
        self.assertEqual(u'0', s.removeProperty('x'))        
        self.assertEqual(u'', s.cssText)        

        # normalize=False
        s.cssText = css
        self.assertEqual(u'3', s.removeProperty('x', normalize=False))        
        self.assertEqual(ur'\x: 0 !important;\x: 2', s.getCssText(separator=u''))        
        self.assertEqual(u'0', s.removeProperty(r'\x', normalize=False))        
        self.assertEqual(u'', s.cssText)        

        s.cssText = css
        self.assertEqual(u'0', s.removeProperty(r'\x', normalize=False))        
        self.assertEqual(ur'x: 1;x: 3', s.getCssText(separator=u''))        
        self.assertEqual(u'3', s.removeProperty('x', normalize=False))        
        self.assertEqual(u'', s.cssText)        

    def test_setProperty(self):
        "CSSStyleDeclaration.setProperty()"
        s = cssutils.css.CSSStyleDeclaration()
        s.setProperty('top', '0', '!important')
        self.assertEqual('0', s.getPropertyValue('top'))
        self.assertEqual('important', s.getPropertyPriority('top'))
        s.setProperty('top', '1px')
        self.assertEqual('1px', s.getPropertyValue('top'))
        self.assertEqual('', s.getPropertyPriority('top'))

        s.setProperty('top', '2px')
        self.assertEqual('2px', s.getPropertyValue('top'))

        s.setProperty('\\top', '3px')
        self.assertEqual('3px', s.getPropertyValue('top'))

        s.setProperty('\\top', '4px', normalize=False)
        self.assertEqual('4px', s.getPropertyValue('top'))
        self.assertEqual('4px', s.getPropertyValue('\\top', False))
        self.assertEqual('3px', s.getPropertyValue('top', False))

        # case insensitive
        s.setProperty('TOP', '0', '!IMPORTANT')
        self.assertEqual('0', s.getPropertyValue('top'))
        self.assertEqual('important', s.getPropertyPriority('top'))

        tests = {
            (u'left', u'0', u''): u'left: 0',
            (u'left', u'0', u'important'): u'left: 0 !important',
            (u'LEFT', u'0', u'important'): u'left: 0 !important',
            (u'left', u'0', u'important'): u'left: 0 !important',
            }
        for test, exp in tests.items():
            s = cssutils.css.CSSStyleDeclaration()
            n, v, p = test
            s.setProperty(n, v, p)
            self.assertEqual(exp, s.cssText)
            self.assertEqual(v, s.getPropertyValue(n))
            self.assertEqual(p, s.getPropertyPriority(n))
        
        # empty 
        s = cssutils.css.CSSStyleDeclaration()
        self.assertEqual('', s.top)
        s.top = '0'
        self.assertEqual('0', s.top)
        s.top = ''
        self.assertEqual('', s.top)
        s.top = None
        self.assertEqual('', s.top)

    def test_length(self):
        "CSSStyleDeclaration.length"
        s = cssutils.css.CSSStyleDeclaration()

        # cssText
        s.cssText = u'left: 0'
        self.assertEqual(1, s.length)
        self.assertEqual(1, len(s.seq))
        s.cssText = u'/*1*/left/*x*/:/*x*/0/*x*/;/*2*/ top: 1;/*3*/'
        self.assertEqual(2, s.length)
        self.assertEqual(5, len(s.seq))

        # set
        s = cssutils.css.CSSStyleDeclaration()
        s.setProperty('top', '0', '!important')
        self.assertEqual(1, s.length)
        s.setProperty('top', '1px')
        self.assertEqual(1, s.length)
        s.setProperty('left', '1px')

    def test_nameParameter(self):
        "CSSStyleDeclaration.XXX(name)"
        s = cssutils.css.CSSStyleDeclaration()
        s.setProperty('top', '1px', '!important')

        self.assertEqual('1px', s.getPropertyValue('top'))
        self.assertEqual('1px', s.getPropertyValue('TOP'))
        self.assertEqual('1px', s.getPropertyValue('T\op'))

        self.assertEqual('important', s.getPropertyPriority('top'))
        self.assertEqual('important', s.getPropertyPriority('TOP'))
        self.assertEqual('important', s.getPropertyPriority('T\op'))

        s.setProperty('top', '2px', '!important')
        self.assertEqual('2px', s.removeProperty('top'))
        s.setProperty('top', '2px', '!important')
        self.assertEqual('2px', s.removeProperty('TOP'))
        s.setProperty('top', '2px', '!important')
        self.assertEqual('2px', s.removeProperty('T\op'))

    def test_css2properties(self):
        "CSSStyleDeclaration.$css2property get set del"
        s = cssutils.css.CSSStyleDeclaration(
            cssText='left: 1px;color: red; font-style: italic')

        s.color = 'green'
        s.fontStyle = 'normal'
        self.assertEqual('green', s.color)
        self.assertEqual('normal', s.fontStyle)
        self.assertEqual('green', s.getPropertyValue('color'))
        self.assertEqual('normal', s.getPropertyValue('font-style'))
        self.assertEqual(
            u'''left: 1px;\ncolor: green;\nfont-style: normal''',
            s.cssText)

        del s.color
        self.assertEqual(
            u'''left: 1px;\nfont-style: normal''',
            s.cssText)
        del s.fontStyle
        self.assertEqual(u'left: 1px', s.cssText)

        self.assertRaises(AttributeError, s.__setattr__, 'UNKNOWN', 'red')
        # unknown properties must be set with setProperty!
        s.setProperty('UNKNOWN', 'red')
        # but are still not usable as property!
        self.assertRaises(AttributeError, s.__getattribute__, 'UNKNOWN')
        self.assertRaises(AttributeError, s.__delattr__, 'UNKNOWN')
        # but are kept
        self.assertEqual('red', s.getPropertyValue('UNKNOWN'))
        self.assertEqual(
            '''left: 1px;\nunknown: red''', s.cssText)

    def test_reprANDstr(self):
        "CSSStyleDeclaration.__repr__(), .__str__()"
        s = cssutils.css.CSSStyleDeclaration(cssText='a:1;b:2')

        self.assert_("2" in str(s)) # length

        s2 = eval(repr(s))
        self.assert_(isinstance(s2, s.__class__))


if __name__ == '__main__':
    import unittest
    unittest.main()
