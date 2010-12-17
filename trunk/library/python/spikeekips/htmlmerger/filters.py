# -*- coding: utf-8 -*-

from twisted.internet import defer
from twisted.python import failure

from cssutils.css.cssvalue import CSSValue, CSSPrimitiveValue
from cssutils.css.property import Property

from spikeekips._twisted.python import log
from spikeekips._twisted.web import client as client_twisted, factory as factory_twisted
from spikeekips._twisted.web.factory import OverCapacity
from spikeekips.html import filters as filters_html, utils as utils_html
from spikeekips.utils import uid


class DeferredFilter (filters_html.BaseFilter, ) :
    def __init__ (self, source, base_url, context, ) :
        super(DeferredFilter, self).__init__(source, base_url, )
        self.log = log.Log(self.__class__, prefix="\t", )

        self._context = context
        self._client_class = self._context.client and self._context.client or client_twisted.Client

        self._targets = list()

    def _cb_client (self, response, ) :
        if not response.success :
            failure.Failure(Exception(response.errors, ), ).raiseException()
            return

        if not self._context.throttle.check(response.length) :
            failure.Failure(OverCapacity(), ).raiseException()
            return

        return response

    def _client (self, url, ) :
        return self._client_class(
                None,
                client_factory=factory_twisted.LengthLimitHTTPClientFactory,
            ).get(
                url,
                length_limit=self._context.throttle.remains,
                timeout=self._context.timeout,
            ).addCallback(
                self._cb_client,
            )

    def get_merge (self, t, ) :
        raise NotImplementedError

    def merge (self, ) :
        self.log.info("merging", )

        self._targets = list()

        [i for i in self]

        _dlist = list()
        for i in self._targets :
            _t = self.nodes.get(i)
            _dlist.append(
                defer.maybeDeferred(self.get_merge(_t, ), _t, i, ),
            )

        return defer.DeferredList(_dlist, ).addCallbacks(self._cb_merge, self._eb_merge, )

    def _cb_merge (self, r, ) :
        return self

    def _eb_merge (self, f, ) :
        self.log.error("merge error %s" % f, )
        return self

    def _merge_default (self, t, k, ) :
        return

    def _eb_merge_default (self, f, t, *a, **kw) :
        self.log.error("token merge error, %s, %s, %s, %s" % (t, f, a, kw, ), )
        return

class HTMLFilter (filters_html.HTMLFilter, DeferredFilter, ) :
    def get_merge (self, t, ) :
        _merge_name = "_merge_%s" % t.get("name", )
        if not hasattr(self, _merge_name, ) :
            _merge_name = "_merge_default"

        return getattr(self, _merge_name, )

class HTMLImageFilter (HTMLFilter, ) :
    """
    * Must be used with `spikeekips.html.filters.HTMLAbsolutePathFilter`.
    * filter and merge by image size, big size will be first merged.
    """

    def __init__ (self, *a, **kw) :
        super(HTMLImageFilter, self).__init__(*a, **kw)
        self._images = list()
        self._sorted_image = dict()

    def _filter_img (self, k, t, ) :
        _d = self.parse_attrs(t, )
        _src = _d.get("src", "").strip()
        if not _src :
            return self.FILTERING_SKIP
        elif _src[:5].lower().startswith("data:") :
            return

        self._images.append(k, )

    _filter_input = _filter_img

    def merge (self, *a, **kw) :
        super(HTMLImageFilter, self).merge(*a, **kw)

        _dlist = list()
        for k in self._images :
            _t = self.nodes.get(k)
            _dlist.append(
                self._download_img(_t, k, ),
            )

        return defer.DeferredList(_dlist, ).addCallbacks(self._analyze_image, self._eb_merge, )

    def _download_img (self, t, k, ) :
        return self._client(
            self.parse_attrs(t, ).get("src").encode("utf-8"),
        ).addCallback(
            self._cb_download_img, k, t,
        ).addErrback(
            self._eb_merge_default, t,
        )

    def _cb_download_img (self, response, k, t, ) :
        if not response.mimetype.startswith("image/") :
            raise failure.Failure(Exception(), )

        return (k, t, response, )

    def _analyze_image (self, r, ) :
        self._targets = list()
        _sorted_image = list()

        for i in r :
            if not i[0] or not i[1] :
                continue

            _sorted_image.append(i[1], )

        if len(_sorted_image) < 1 :
            return self

        _sorted_image.sort(
            lambda x, y : (x[2].length > y[2].length) and -1 or 1,
        )

        for _k, _t, _response in _sorted_image :
            _v = utils_html.generate_data_uri(_response.content, _response.mimetype, )

            if not self._context.throttle.check(len(_v)) :
                #failure.Failure(OverCapacity(), ).raiseException()
                continue

            self._context.throttle += len(_v)

            _a = self.parse_attrs(_t, )
            _a["src"] = _v

            _t["data"] = _a

        return self

class HTMLCSSMerge (HTMLFilter, ) :
    def _filter_link (self, k, t, ) :
        _a = self.parse_attrs(t, )
        _href = _a.get("href", "").strip()
        if not _href :
            return

        self._targets.append(k, )

    def _merge_link (self, t, k, ) :
        _src = self.parse_attrs(t, ).get("href").encode("utf-8")

        return self._client(_src, ).addCallback(
            self._cb_merge_link, t, k
        ).addErrback(
            self._eb_merge_default, t,
        )

    def _cb_merge_link (self, response, token, k, ) :
        if not response.mimetype == "text/css" :
            return

        def _cb_done (content, ) :
            _a = self.parse_attrs(token, )

            self.nodes[k] = {
                "namespace": token.get("namespace"),
                "type": "StartTag",
                "name": "style",
                "data": _a.items(),
            }

            _new_key = uid()
            self.nodes.append_to(
                k,
                _new_key,
                {
                    "namespace": token.get("namespace"),
                    "type": "Characters",
                    "data": "/* %s */\n%s" % (_a["href"], content, ),
                },
            )

            self.nodes.append_to(
                _new_key,
                uid(),
                {
                    "namespace": token.get("namespace"),
                    "type": "EndTag",
                    "name": "style",
                }
            )

            del _a["href"]

        if not self._context.throttle.check(response.length) :
            failure.Failure(OverCapacity(), ).raiseException()
            return

        self._context.throttle += response.length

        import merger
        _merger = merger.CSSMerger(
            response.content,
            response.url,
            context=self._context,
        )
        return _merger.filter(
            filters_html.CSSRemoveUseless,
            filters_html.CSSAbsoluteURI,
            CSSImportRule,
            CSSMergeURI,
        ).addCallback(
            _merger.to_string,
        ).addCallback(
            _cb_done,
        )


class CSSFilter (DeferredFilter, filters_html.CSSFilter, ) :
    def get_merge (self, t, ) :
        _merge_name = "_merge_%s" % t.__class__.__name__.lower()

        if not hasattr(self, _merge_name, ) :
            _merge_name = "_merge_default"

        return getattr(self, _merge_name, )

class CSSImportRule (CSSFilter, ) :
    def _filter_cssimportrule (self, k, t, ) :
        if not t.href.strip() :
            return

        self._targets.append(k)

    def _merge_cssimportrule (self, t, k, ) :
        return self._client(t.href.encode("utf-8"), ).addCallback(
            self._cb_merge_cssimportrule, t, k,
        ).addErrback(
            self._eb_merge_default, t,
        )

    def _cb_merge_cssimportrule (self, response, t, k, ) :
        if not response.mimetype.startswith("text/css") :
            return

        def _cb_done (r, ) :
            for i in r :
                self.nodes.append_to(k, uid(), i, )

            del self.nodes[k]

        if not self._context.throttle.check(response.length) :
            failure.Failure(OverCapacity(), ).raiseException()
            return

        self._context.throttle += response.length

        import merger
        return merger.CSSMerger(
            response.content,
            response.url,
            context=self._context,
        ).filter(
            filters_html.CSSRemoveUseless,
            filters_html.CSSAbsoluteURI,
            self.__class__,
            CSSMergeURI,
        ).addCallback(
            _cb_done,
        )

class CSSMergeURI (CSSFilter, ) :
    def __init__ (self, *a, **kw) :
        super(CSSMergeURI, self).__init__(*a, **kw)

        self._uris = dict()

    def _filter_cssstylerule (self, k, t, ) :
        _cssvalues = list()
        filters_html.check_cssstylerule_has_uri(
            t,
            lambda x : _cssvalues.append(x, ),
        )

        for i in _cssvalues :
            _v = i.getStringValue()
            if not _v.strip() or _v[:5].startswith("data:") :
                continue

            self._uris.setdefault(_v, list(), )
            self._uris[_v].append(i, )

    def merge (self, ) :
        super(CSSMergeURI, self).merge().cancel()

        _dlist = list()
        for _url, _cssvalues, in self._uris.iteritems() :
            _dlist.append(
                self._client(_url.encode("utf-8"), ).addCallback(
                    self._cb_merge_uri, _cssvalues,
                ).addErrback(
                    self._eb_merge_default, _cssvalues,
                ),
            )

        return defer.DeferredList(_dlist, ).addCallbacks(self._cb_merge, self._eb_merge, )

    def _cb_merge_uri (self, response, cssvalues, ) :
        _v = utils_html.generate_data_uri(response.content, response.mimetype, )

        _amount = len(_v) * len(cssvalues)
        if not self._context.throttle.check(_amount) :
            failure.Failure(OverCapacity(), ).raiseException()
            return

        self._context.throttle += _amount

        for i in cssvalues :
            i.setStringValue(
                CSSPrimitiveValue.CSS_URI,
                _v,
            )



