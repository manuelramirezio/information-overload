# -*- coding: utf-8 -*-

import os, sys, StringIO, logging

from twisted.internet import reactor, defer
from twisted.mail.smtp import ESMTPSenderFactory

from spikeekips._twisted.python import log

from spikeekips.htmlmerger import merger, filters as filters_merger
from spikeekips.html import filters as filters_html

capacity=10000000
capacity=3000000
capacity=1000000
capacity=2000000
capacity=1500000


def _cb_get (response, ) :
    def _cb_done (r, ) :
        with file("/tmp/1.html", "w") as f :
            f.write(r.encode("utf-8"))

        print "done. "
        return
        from spikeekips import _email
        _content = r.encode("utf-8")
        _msg = _email.MessageWriter()
        _msg["from"] = "spikeekips+readitemail@gmail.com"
        _msg["reply-to"] = "spikeekips@gmail.com"
        _msg["subject"] = "%d" % capacity

        _msg.add_sub(
            _content,
            content_type="text/html",
            encoding="utf-8",
        )

        server_info = dict(
            imap=("imap.gmail.com", 993, "spikeekips@gmail.com", "abu333spike", ),
            smtp=("smtp.gmail.com", 587, "spikeekips@gmail.com", "abu333spike", ),
        )

        _d = defer.Deferred()
        factory = ESMTPSenderFactory(
            server_info.get("smtp")[2],
            server_info.get("smtp")[3],
            _msg.get_header("from", )[1],
            ["spikeekips@gmail.com", ],
            StringIO.StringIO(_msg.to_string(), ),
            _d,
        )

        reactor.connectTCP(
            server_info.get("smtp")[0],
            server_info.get("smtp")[1],
            factory,
        )

        def _cb_smtp_done (r, *a, **kw) :
            print "done", r

        _d.addCallbacks(
            _cb_smtp_done,
        )


    with file("/tmp/1-orig.html", "w") as f :
        f.write(response.content, )

    _merger = merger.HTMLMerger(
        response.content,
        response.url,
        merger.Context(
            capacity=capacity,
            current_size=response.length,
        ),
    )

    _merger.filter(
        filters_html.HTMLWhitespaceFilter,
        filters_html.HTMLRemoveUselessLink,
        filters_html.HTMLRemoveJavascript,
        filters_html.HTMLRemoveCommentFilter,
        filters_html.HTMLRemoveScript,
        filters_html.HTMLRemoveUselessAttrsFilter,
        filters_html.HTMLAbsolutePathFilter,
        filters_merger.HTMLImageFilter,
        filters_merger.HTMLCSSMerge,
    ).addCallback(
        _merger.to_string,
    ).addCallback(
        _cb_done,
    )


from spikeekips._twisted.web.client import Client as client_twisted

root = os.path.dirname(__file__)

url = "http://www.ibm.com/developerworks/opensource/library/wa-appsecurity/index.html?ccy=zz&cmp=dw&cpb=dwope&cr=twitter&csr=webappsecuritytools&ct=dwgra"
url = "http://pypi.python.org/pypi/MapProxy/0.9.0"
url = "http://www.readwriteweb.com/archives/the_top_10_domains_on_twitter_bitly_rules_them_all.php"
url = "http://mashable.com/2010/10/18/dell-led-displays/"


client_twisted(url, ).get(None, ).addCallback(_cb_get, )

APP_NAME = "ReadItEmail"
log.initialize(APP_NAME, "info", )

reactor.run()



