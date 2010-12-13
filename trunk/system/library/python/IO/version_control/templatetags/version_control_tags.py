# -*- coding: utf-8 -*-

import os, locale

from django.utils import simplejson
from django.utils.safestring import mark_safe
from django.template import Variable, Library, Node, NodeList, Template, Context, TemplateDoesNotExist
from django.template.defaulttags import kwarg_re
from django.core.urlresolvers import reverse

from IO.version_control import models as models_version_control
from IO.developer.templatetags.developer_tags import render_developer

register = Library()

@register.filter
def version_control_diff (diff, ) :
    _temp = dict(
        tag=None,
        content=None,
    )

    _n = 1
    _line = list()

    for i in diff :
        if i[:2] == u"- " :
           _tag = u"deleted"
        elif i[:2] == u"+ " :
           _tag = u"added"
        elif i[:2] == u"? " :
           _tag = u"modified"
        else :
            _tag = "none"

        if not _line :
            _o = dict(_temp.items(), )
            _o.update(dict(
                tag=_tag,
                content=i[2:],
            ))
            _line.append(_o)
            continue

        _last = _line[-1]
        if _last.get("tag") == "deleted" and _tag == "added" :
            _o = dict(_temp.items(), )
            _o.update(dict(
                tag=_tag,
                content=i[2:],
            ))
            _line.append(_o, )
        elif _tag == "modified" :
            _o = dict(_temp.items(), )
            _o.update(dict(
                tag=_tag,
                content=i[2:].replace("\n", ""),
            ))
            _line.append(_o, )
        else :
            yield _line

            _line = list()

            _o = dict(_temp.items(), )
            _o.update(dict(
                tag=_tag,
                content=i[2:],
            ))
            _line.append(_o, )

    if _line :
        yield _line

@register.filter
def get_revision_file_by_number (f, number, ) :
    return models_version_control.RevisionFile.objects.get_by_number(f, number, )


class RevisionNode (Node, ) :
    def __init__ (self, **kw) :
        self._kw = kw

    def render (self, context, ) :
        _kw = dict()
        for k, v in self._kw.items() :
            _kw[k] = v.resolve(context)

        if not _kw.get("from_revision") and not _kw.get("to_revision") :
            return u"None"

        _kw_new = dict()

        _info = _kw.get("info")
        _kw_new["name"] = _info.name
        _kw_new["project"] = _info.project.code

        _path = _kw.get("path")
        if not _kw.get("path") :
            _path = _info.root

        if isinstance(_path, models_version_control.File, ) :
            _path = _path.abspath_verbose
        elif isinstance(_path, models_version_control.RevisionFile, ) :
            _path = _path.file.abspath_verbose

        _kw_new["path"] = _path

        if _kw.get("to_revision") :
            _kw_new["to_revision"] = _kw.get("to_revision")
        if _kw.get("from_revision") :
            _kw_new["from_revision"] = _kw.get("from_revision")

        if _kw_new.get("to_revision") == _kw_new.get("from_revision") and _kw_new.has_key("from_revision"):
            del _kw_new["from_revision"]

        if not _kw_new.get("from_revision") :
            _viewname = "version_control_revision0"
        else :
            _viewname = "version_control_revision"

        _link = _kw.get("link")

        if not _link :
            _has_to = _kw_new.get("to_revision")
            _has_from = _kw_new.get("from_revision")

            if _has_to and _has_from :
                _fmt = u"r%(from_revision)d &gt; r%(to_revision)d"
            elif _has_to :
                _fmt = u"r%(to_revision)d"
            elif _has_from :
                _fmt = u"r%(from_revision)d"
            else :
                _fmt = u""

            _link = _fmt % _kw_new

        return u"""<a class="revision" href="%s">%s</a>""" % (
            reverse(_viewname, kwargs=_kw_new, ),
            _link,
        )

@register.tag
def revision (parser, token, ) :
    """
{% url version_control_revision project=object.code path=None to_revision=object.version_control.latest_revision.number %}
    """

    _kw = dict()
    _bits = list(token.split_contents())
    for _b in _bits:
        _match = kwarg_re.match(_b)
        if not _match:
            raise TemplateSyntaxError("Malformed arguments to url tag")

        _n, _v = _match.groups()
        if _n:
            _kw[_n] = parser.compile_filter(_v)

    return RevisionNode(**_kw)

class AuthorNode (Node, ) :
    def __init__ (self, obj, not_show_me=None, ) :
        self._object = obj
        self._not_show_me = not_show_me

    def render (self, context, ) :
        _author = self._object.resolve(context)
        if not _author :
            return u"no author"

        elif _author.profile :
            _user = _author.profile
        else :
            _user = _author.name

        return render_developer(
            context.get("request"),
            _user,
            show_me=not self._not_show_me.resolve(context),
            is_full=True,
        )

@register.tag
def author (parser, token, ) :
    try :
        _object = token.source[0].name
    except :
        return u""

    _bits = list(token.split_contents())
    _not_show_me = ""
    if len(_bits) > 2 :
        _not_show_me =  _bits[2]

    return AuthorNode(
        parser.compile_filter(_bits[1]),
        parser.compile_filter(_not_show_me),
    )


