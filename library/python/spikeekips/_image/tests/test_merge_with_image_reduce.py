# -*- coding: utf-8 -*-

import sys, logging

import re, os, logging, StringIO, string, datetime

from twisted.internet import reactor

from html import merger, download_and_merge

def _cb_dm (r, filename, ) :
    (_r, _response, ) = r
    (_content, _encoding, ) = _r

    with file(filename, "w") as f :
        f.write(_content.encode(_encoding, ), )

    print "done"

def _eb (f, ) :
    print f

logging.basicConfig(level=logging.INFO, )

url = "http://24ways.org/2007/supersleight-transparent-png-in-ie6"
url = "http://www.ibm.com/developerworks/linux/library/l-vim-script-1/index.html"
url = "http://www.techopsguru.com/blog"

from readitemail import utils as utils_readitemail

if sys.argv[1] == "1" : # full merge
    download_and_merge(
        url,
        func_get_page=utils_readitemail.GetPage(use_cache=True, reduce_size=False, ).get,
    ).addCallback(
        _cb_dm,
        "/tmp/full.html",
    )

elif sys.argv[1] == "2" : # not merge CSS merge
    download_and_merge(
        url,
        func_get_page=utils_readitemail.GetPage(use_cache=True, reduce_size=False, ).get,
        htmlfilter=merger.HTMLTitleWithoutCSS_Filter,
    ).addCallback(
        _cb_dm,
        "/tmp/not-merge-css.html",
    )

elif sys.argv[1] == "3" : # image size-reduce merge
    download_and_merge(
        url,
        func_get_page=utils_readitemail.GetPage(use_cache=True, reduce_size=True, ).get,
    ).addCallback(
        _cb_dm,
        "/tmp/reduce-image-size.html",
    )

elif sys.argv[1] == "4" : # not merge CSS and image size-reduce merge
    download_and_merge(
        url,
        func_get_page=utils_readitemail.GetPage(use_cache=True, reduce_size=True, ).get,
        htmlfilter=merger.HTMLTitleWithoutCSS_Filter,
    ).addCallback(
        _cb_dm,
        "/tmp/not-merge-css-and-reduce-image-size.html",
    ).addErrback(
        _eb
    )

reactor.run()



