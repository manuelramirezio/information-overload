# -*- coding: utf-8 -*-

import os, locale

from django.conf import settings
from django import forms
from django.forms.util import ErrorDict, ErrorList
from django.utils import simplejson
from django.utils.safestring import mark_safe
from django.template import Variable, Library, Node, NodeList, Template, Context, TemplateDoesNotExist
from django.template.defaultfilters import timesince
from django.utils.encoding import StrAndUnicode, force_unicode
from django.template.loader_tags import IncludeNode

from django_modules.http import get_host as get_host_http, get_current_url as get_current_url_http

register = Library()

@register.filter
def json_loads (s, ) :
    try :
        return simplejson.loads(s)
    except :
        return None

@register.filter
def json_dumps (s, ) :
    try :
        return simplejson.dumps(s)
    except :
        return None

@register.filter
def split (s, d=" ") :
    return s.split(d, )

@register.filter()
def currency(value):
    return locale.currency(value, grouping=True)

INCLUDE_MEDIA_TYPES = (
    (
        ".css",
        "<style type=\"text/css\">",
        "</style>",
    ),
    (
        ".js",
        "<script type=\"text/javascript\">",
        "</script>",
    ),
)

class IncludeMediaNode (Node, ) :
    def __init__(self, source, ) :
        super(IncludeMediaNode, self).__init__()
        self._source = source

    def __repr__ (self, ) :
        return "<IncludeMediaNode>"

    def _get_template_path (self, ) :
        _abs = os.path.abspath
        for i in settings.TEMPLATE_DIRS :
            if _abs(self._source).startswith(_abs(i)) :
                return os.path.relpath(_abs(self._source), _abs(i), )

    def render (self, context, ) :
        _source = self._get_template_path()
        (_fprefix, _ext_orig, ) = os.path.splitext(_source, )
        if not _fprefix :
            return

        _media = list()
        for _ext, _tag_start, _tag_end in INCLUDE_MEDIA_TYPES :
            try :
                _o = IncludeNode(Variable("\"%s%s\"" % (_fprefix, _ext, ), ), ).render(context, )
            except TemplateDoesNotExist :
                pass
            else :
                if not _o :
                    continue

                _media.append(u"\n<!-- include_media: %s -->" % _fprefix, )
                _media.append(_tag_start, )
                _media.append(_o, )
                _media.append(_tag_end, )
                _media.append(u"\n", )

        return u"\n".join(_media)

@register.tag
def include_media (parser, token, ) :
    try :
        _source = token.source[0].name
    except :
        return u""

    return IncludeMediaNode(_source, )

@register.filter
def getitem (d, k, ) :
    return d.get(k)

@register.filter
def normalize_error (e, ) :
    if isinstance(e, ErrorDict, ) :
        return [u"%s%s" % (
            k != "__all__" and ("%s: " % k) or u"",
            v.as_text()[2:],
        ) for k, v in e.items()]
    elif isinstance(e, ErrorList, ) :
        return [v for v in e]
    elif isinstance(e, forms.Form, ) :
        return normalize_error(e.errors, )

    return [e, ]

@register.filter
def get_range (n, ) :
    return range(n)

@register.filter
def subtract (a, b, ) :
    return a - b

@register.filter
def timeago (t, ) :
    return mark_safe(
        """<span class="datetime"
                data-datetime="%(datetime)s"
                data-since="%(since)s ago"
            ><span class="value">%(since)s ago</span></span>""" % dict(
            since=timesince(t, ),
            datetime=t,
        ),
    )

class MessageNode (Node, ) :
    def __init__ (self, msg, mtype=None, ) :
        self._msg = msg
        self._mtype = mtype

    def render (self, context, ) :
        _msgs = self._msg.resolve(context)

        _mtype = "info"
        if self._mtype :
            _mtype = self._mtype.resolve(context)

        if isinstance(_msgs, (ErrorDict, ErrorList, forms.Form, ), ) :
            _mtype = "error"

        if _mtype == "error" :
            _msgs = normalize_error(_msgs, )

        if not _msgs :
            return u""

        if type(_msgs) not in (list, tuple, ) :
            _msgs = (_msgs, )

        return mark_safe(
            u"""<div class="msgs">%s</div>""" % u"".join(
                (self._render_msg(i, _mtype, ) for i in _msgs)
            ),
        )

    def _render_msg (self, i, mtype, ) :
        return u"""
<span class="msg"><span class="%(mtype)s">%(msg)s</span></span>
        """ % dict(
            mtype=mtype,
            msg=i,
        )

@register.tag
def print_message (parser, token, ) :
    _bits = list(token.split_contents())
    _msg = parser.compile_filter(_bits[1])
    _mtype = None
    if len(_bits) > 2 :
        _mtype = parser.compile_filter(_bits[2])
        
    return MessageNode(_msg, _mtype, )

@register.filter
def get_host (request, ) :
    return get_host_http(request, )

