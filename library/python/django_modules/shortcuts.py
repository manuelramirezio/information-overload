# -*- coding: utf-8 -*-

from django.http import Http404
from django.shortcuts import render_to_response as render_to_response_django, get_object_or_404 as get_object_or_404_django, _get_queryset
from django.template import loader, RequestContext, Context, Template

def render_to_response (request, *a, **kw) :
    kw.update(
        {
            "context_instance": RequestContext(request),
        }
    )
    return render_to_response_django(*a, **kw)

def render_to_string (request, *a, **kw) :
    if request :
        kw.update(
            {
                "context_instance": RequestContext(request),
            }
        )

    return loader.render_to_string(*a, **kw)

def render_string (s, kw=None, ctx=None) :
    kw = kw or dict()
    if ctx :
        ctx.update(kw)
    else:
        ctx = Context(kw)

    return Template(s).render(ctx)

def get_object_or_none (cls, *a, **kw) :
    queryset = _get_queryset(cls, )
    try:
        return queryset.get(*a, **kw)
    except queryset.model.DoesNotExist :
        return None



__author__ =  "Spike^ekipS <spikeekips@gmail.com>"




