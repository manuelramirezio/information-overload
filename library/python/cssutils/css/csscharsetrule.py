"""CSSCharsetRule implements DOM Level 2 CSS CSSCharsetRule."""
__all__ = ['CSSCharsetRule']
__docformat__ = 'restructuredtext'
__version__ = '$Id: csscharsetrule.py 1949 2010-03-26 22:16:33Z cthedot $'

import codecs
import cssrule
import cssutils
import xml.dom

class CSSCharsetRule(cssrule.CSSRule):
    """
    The CSSCharsetRule interface represents an @charset rule in a CSS style
    sheet. The value of the encoding attribute does not affect the encoding
    of text data in the DOM objects; this encoding is always UTF-16
    (also in Python?). After a stylesheet is loaded, the value of the
    encoding attribute is the value found in the @charset rule. If there
    was no @charset in the original document, then no CSSCharsetRule is
    created. The value of the encoding attribute may also be used as a hint
    for the encoding used on serialization of the style sheet.

    The value of the @charset rule (and therefore of the CSSCharsetRule)
    may not correspond to the encoding the document actually came in;
    character encoding information e.g. in an HTTP header, has priority
    (see CSS document representation) but this is not reflected in the
    CSSCharsetRule.
    
    This rule is not really needed anymore as setting 
    :attr:`CSSStyleSheet.encoding` is much easier.

    Format::

        charsetrule:
            CHARSET_SYM S* STRING S* ';'

    BUT: Only valid format is (single space, double quotes!)::
    
        @charset "ENCODING";
    """
    def __init__(self, encoding=None, parentRule=None, 
                 parentStyleSheet=None, readonly=False):
        """
        :param encoding:
            a valid character encoding
        :param readonly:
            defaults to False, not used yet
        """
        super(CSSCharsetRule, self).__init__(parentRule=parentRule, 
                                             parentStyleSheet=parentStyleSheet)
        self._atkeyword = '@charset'
        
        if encoding:
            self.encoding = encoding
        else:
            self._encoding = None

        self._readonly = readonly

    def __repr__(self):
        return u"cssutils.css.%s(encoding=%r)" % (
                self.__class__.__name__, 
                self.encoding)

    def __str__(self):
        return u"<cssutils.css.%s object encoding=%r at 0x%x>" % (
                self.__class__.__name__, 
                self.encoding, 
                id(self))

    def _getCssText(self):
        """The parsable textual representation."""
        return cssutils.ser.do_CSSCharsetRule(self)

    def _setCssText(self, cssText):
        """
        :param cssText:
            A parsable DOMString.
        :exceptions:
            - :exc:`~xml.dom.SyntaxErr`:
              Raised if the specified CSS string value has a syntax error and
              is unparsable.
            - :exc:`~xml.dom.InvalidModificationErr`:
              Raised if the specified CSS string value represents a different
              type of rule than the current one.
            - :exc:`~xml.dom.HierarchyRequestErr`:
              Raised if the rule cannot be inserted at this point in the
              style sheet.
            - :exc:`~xml.dom.NoModificationAllowedErr`:
              Raised if the rule is readonly.
        """
        super(CSSCharsetRule, self)._setCssText(cssText)

        wellformed = True
        tokenizer = self._tokenize2(cssText)
        
        if self._type(self._nexttoken(tokenizer)) != self._prods.CHARSET_SYM: 
            wellformed = False
            self._log.error(u'CSSCharsetRule must start with "@charset "',
                            error=xml.dom.InvalidModificationErr)
        
        encodingtoken = self._nexttoken(tokenizer)
        encodingtype = self._type(encodingtoken)
        encoding = self._stringtokenvalue(encodingtoken)
        if self._prods.STRING != encodingtype or not encoding:
            wellformed = False
            self._log.error(u'CSSCharsetRule: no encoding found; %r.' % 
                            self._valuestr(cssText))
            
        semicolon = self._tokenvalue(self._nexttoken(tokenizer))
        EOFtype = self._type(self._nexttoken(tokenizer))
        if u';' != semicolon or EOFtype not in ('EOF', None):
            wellformed = False
            self._log.error(u'CSSCharsetRule: Syntax Error: %r.' % 
                            self._valuestr(cssText))
        
        if wellformed:
            self.encoding = encoding
            
    cssText = property(fget=_getCssText, fset=_setCssText,
                       doc=u"(DOM) The parsable textual representation.")

    def _setEncoding(self, encoding):
        """
        :param encoding:
            a valid encoding to be used. Currently only valid Python encodings
            are allowed.
        :exceptions:
            - :exc:`~xml.dom.NoModificationAllowedErr`:
              Raised if this encoding rule is readonly.
            - :exc:`~xml.dom.SyntaxErr`:
              Raised if the specified encoding value has a syntax error and
              is unparsable.  
        """
        self._checkReadonly()
        tokenizer = self._tokenize2(encoding)
        encodingtoken = self._nexttoken(tokenizer)
        unexpected = self._nexttoken(tokenizer)

        if not encodingtoken or unexpected or\
           self._prods.IDENT != self._type(encodingtoken):
            self._log.error(u'CSSCharsetRule: Syntax Error in encoding value '
                            u'%r.' % encoding)
        else:
            try:
                codecs.lookup(encoding)
            except LookupError:
                self._log.error(u'CSSCharsetRule: Unknown (Python) encoding %r.'
                                % encoding)
            else:
                self._encoding = encoding.lower()

    encoding = property(lambda self: self._encoding, _setEncoding,
        doc=u"(DOM)The encoding information used in this @charset rule.")

    type = property(lambda self: self.CHARSET_RULE, 
                    doc=u"The type of this rule, as defined by a CSSRule "
                        u"type constant.")

    wellformed = property(lambda self: bool(self.encoding))
