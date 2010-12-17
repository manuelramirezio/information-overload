# -*- coding: utf-8 -*-

from django.conf import settings
from django.contrib.auth import models as models_auth
from django.db.models import ObjectDoesNotExist
from django.utils.safestring import mark_safe
from django.template import TemplateSyntaxError, Variable, Library, Node, NodeList, Template, Context, TemplateDoesNotExist
from django.utils.encoding import StrAndUnicode, force_unicode
from django.utils.html import urlize
from django.core.urlresolvers import reverse

from IO.developer import models as models_developer

register = Library()

def render_developer (request, user, show_me=True, is_full=False, template=None, ) :
    if type(user) in (str, unicode, ) :
        return user

    _is_me = False
    _profile = None
    _show_me = show_me and request.user.is_authenticated()

    if isinstance(user, models_developer.Profile, ) :
        _profile = user
        user = user.user
    else :
        try :
            _profile = user.profile
        except ObjectDoesNotExist :
            if user.profiles.all().count() > 0 :
               _profile = user.profiles.all()[0]

    if _profile and _show_me and _profile.users.filter(pk=request.user.pk, ) :
        _is_me = True
   
    _username= _profile and _profile.user.username or user.first_name
    if not _username.strip() :
        _username = user.email

    _link_name = (is_full and """
<span class="email">%(username)s &lt;%(email)s&gt;</span>""" or "%(username)s") % dict(
        username=_username,
        email=user.email,
    )
    
    if not template :
        template = u"""
<a class="developer %(no_profile)s %(is_me)s" href="%(url)s">%(username)s</a>
        """

    _username_url = _profile and _profile.user.username or user.username
    return template.strip() % dict(
        no_profile=not bool(_profile) and "no_profile" or "",
        is_me=_is_me and "me" or "",
        url=reverse("developer", kwargs=dict(username=_username_url, ), ),
        username=_link_name,
    )

class DeveloperNode (Node, ) :
    def __init__ (self, obj, not_show_me=None, ) :
        self._object = obj
        self._not_show_me = not_show_me

    def render (self, context, ) :
        return render_developer(
            context.get("request"),
            self._object.resolve(context),
            show_me=not self._not_show_me.resolve(context),
            is_full=True,
        )

@register.tag
def developer (parser, token, ) :
    try :
        _object = token.source[0].name
    except :
        return u""

    _bits = list(token.split_contents())
    _not_show_me = ""
    if len(_bits) > 2 :
        _not_show_me =  _bits[2]

    return DeveloperNode(
        parser.compile_filter(_bits[1]),
        parser.compile_filter(_not_show_me),
    )


