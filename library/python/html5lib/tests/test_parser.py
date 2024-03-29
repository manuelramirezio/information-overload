import os
import sys
import traceback
import StringIO
import unittest
import warnings

warnings.simplefilter("error")

from support import html5lib_test_files, TestData, convert, convertExpected
import html5lib
from html5lib import html5parser, treebuilders, constants

treeTypes = {"simpletree":treebuilders.getTreeBuilder("simpletree"),
             "DOM":treebuilders.getTreeBuilder("dom")}

#Try whatever etree implementations are avaliable from a list that are
#"supposed" to work
try:
    import xml.etree.ElementTree as ElementTree
    treeTypes['ElementTree'] = treebuilders.getTreeBuilder("etree", ElementTree, fullTree=True)
except ImportError:
    try:
        import elementtree.ElementTree as ElementTree
        treeTypes['ElementTree'] = treebuilders.getTreeBuilder("etree", ElementTree, fullTree=True)
    except ImportError:
        pass

try:
    import xml.etree.cElementTree as cElementTree
    treeTypes['cElementTree'] = treebuilders.getTreeBuilder("etree", cElementTree, fullTree=True)
except ImportError:
    try:
        import cElementTree
        treeTypes['cElementTree'] = treebuilders.getTreeBuilder("etree", cElementTree, fullTree=True)
    except ImportError:
        pass
    
try:
    try:
        import lxml.html as lxml
    except ImportError:
        import lxml.etree as lxml
    treeTypes['lxml'] = treebuilders.getTreeBuilder("lxml", lxml, fullTree=True)
except ImportError:
    pass

try:
    import BeautifulSoup
    treeTypes["beautifulsoup"] = treebuilders.getTreeBuilder("beautifulsoup", fullTree=True)
except ImportError:
    pass

#Try whatever dom implementations are avaliable from a list that are
#"supposed" to work
try:
    import pxdom
    treeTypes["pxdom"] = treebuilders.getTreeBuilder("dom", pxdom)
except ImportError:
    pass

#Run the parse error checks
checkParseErrors = False

#XXX - There should just be one function here but for some reason the testcase
#format differs from the treedump format by a single space character
def convertTreeDump(data):
    return "\n".join(convert(3)(data).split("\n")[1:])

import re
attrlist = re.compile(r"^(\s+)\w+(?:\s\w+)?=.*(?:\n\1\w+(?:\s\w+)?=.*)+",re.M)
def sortattrs(x):
  lines = x.group(0).split("\n")
  lines.sort()
  return "\n".join(lines)
namespaceExpected = re.compile(r"^(\s*)<(\S+)>", re.M).sub

class TestCase(unittest.TestCase):
    def runParserTest(self, innerHTML, input, expected, errors, treeClass,
        namespaceHTMLElements):
        #XXX - move this out into the setup function
        #concatenate all consecutive character tokens into a single token
        try:
            p = html5parser.HTMLParser(tree = treeClass,
                                       namespaceHTMLElements=namespaceHTMLElements)
        except constants.DataLossWarning:
            return

        try:
            if innerHTML:
                document = p.parseFragment(input, innerHTML)
            else:
                try:
                    document = p.parse(input)
                except constants.DataLossWarning:
                    return 
        except:
            errorMsg = u"\n".join([u"\n\nInput:", input, u"\nExpected:", expected,
                                   u"\nTraceback:", traceback.format_exc()])
            self.assertTrue(False, errorMsg.encode("utf8"))
        
        output = convertTreeDump(p.tree.testSerializer(document))
        output = attrlist.sub(sortattrs, output)
        
        expected = convertExpected(expected)
        expected = attrlist.sub(sortattrs, expected)
        if namespaceHTMLElements:
            expected = namespaceExpected(r"\1<html \2>", expected)
        
        errorMsg = u"\n".join([u"\n\nInput:", input, u"\nExpected:", expected,
                               u"\nReceived:", output])
        self.assertEquals(expected, output, errorMsg.encode("utf8"))
        errStr = [u"Line: %i Col: %i %s"%(line, col, 
                                          constants.E[errorcode] % datavars if isinstance(datavars, dict) else (datavars,)) for
                  ((line,col), errorcode, datavars) in p.errors]
        
        errorMsg2 = u"\n".join([u"\n\nInput:", input,
                                u"\nExpected errors (" + str(len(errors)) + u"):\n" + u"\n".join(errors),
                                u"\nActual errors (" + str(len(p.errors)) + u"):\n" + u"\n".join(errStr)])
        if checkParseErrors:
            self.assertEquals(len(p.errors), len(errors), errorMsg2.encode("utf-8"))

def buildTestSuite():
    sys.stdout.write('Testing tree builders '+ " ".join(treeTypes.keys()) + "\n")

    for treeName, treeCls in treeTypes.iteritems():
        files = html5lib_test_files('tree-construction')
        #files = [f for f in files if 
        #         not f.split(".")[-2][-2:] in ("s9", "10", "11", "12")] #skip namespace tests for now
        for filename in files:
            testName = os.path.basename(filename).replace(".dat","")

            tests = TestData(filename, "data")

            for index, test in enumerate(tests):
                input, errors, innerHTML, expected = [test[key] for key in
                                                      'data', 'errors',
                                                      'document-fragment',
                                                      'document']
                if errors:
                    errors = errors.split("\n")
                
                for namespaceHTMLElements in (True, False):
                    def testFunc(self, innerHTML=innerHTML, input=input,
                        expected=expected, errors=errors, treeCls=treeCls,
                        namespaceHTMLElements=namespaceHTMLElements): 
                        return self.runParserTest(innerHTML, input, expected,
                                                  errors, treeCls,
                                                  namespaceHTMLElements)
                    testFunc.__name__ = "test_%s_%d_%s_%s" % (testName,index+1,treeName, namespaceHTMLElements and "namespaced" or "no_html_namespace")
                    setattr(TestCase, testFunc.__name__,
                         testFunc)
                    break
        break

    return unittest.TestLoader().loadTestsFromTestCase(TestCase)

def main():
    # the following is temporary while the unit tests for parse errors are
    # still in flux
    if '-p' in sys.argv: # suppress check for parse errors
        sys.argv.remove('-p')
        global checkParseErrors
        checkParseErrors = False
    buildTestSuite()
    try:
        unittest.main()
    except SystemExit:
	    pass

if __name__ == "__main__":
    print sys.argv
    main()
