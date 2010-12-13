# -*- coding: utf-8 -*-

from django.conf import settings
from django.db.models import ObjectDoesNotExist
from django.utils.safestring import mark_safe
from django.template import TemplateSyntaxError, Variable, Library, Node, NodeList, Template, Context, TemplateDoesNotExist
from django.utils.encoding import StrAndUnicode, force_unicode
from django.core.urlresolvers import reverse

from IO.developer.templatetags.developer_tags import render_developer
from IO.developer import models as models_developer
from IO.dialog import models as models_dialog

register = Library()

class ProfileNode (Node, ) :
    def __init__ (self, obj, not_show_me=None, is_full=None, ) :
        self._object = obj
        self._not_show_me = not_show_me
        self._is_full = is_full

    def render (self, context, ) :
        _v = self._object.resolve(context)
        _not_show_me = self._not_show_me.resolve(context)
        _is_full = self._is_full.resolve(context)

        return render_developer(
            context.get("request"),
            self._object.resolve(context),
            show_me=not self._not_show_me.resolve(context),
            is_full=self._is_full.resolve(context),
        )

@register.tag
def message_profile (parser, token, ) :
    try :
        _object = token.source[0].name
    except :
        return u""

    _bits = list(token.split_contents())
    _not_show_me = u""
    _is_full = u""
    if len(_bits) > 2 :
        _not_show_me =  _bits[2]
    if len(_bits) > 3 :
        _is_full =  _bits[3]

    return ProfileNode(
        parser.compile_filter(_bits[1]),
        parser.compile_filter(_not_show_me),
        parser.compile_filter(_is_full),
    )

@register.filter
def get_profile_message (user, message, ) :
    if isinstance(user, models_developer.Profile, ) :
        _profile = user
    else :
        _profile = models_developer.Profile.objects.get_by_user(user, )

    if not _profile :
        return

    if isinstance(message, models_dialog.Message, ) :
        try :
            return models_dialog.ProfileMessage.objects.get(profile=_profile, message=message, )
        except ObjectDoesNotExist :
            return None
    elif isinstance(message, models_dialog.ProfileMessageTop, ) :
        try :
            return models_dialog.ProfileMessage.objects.get(profile=_profile, message=message, )
        except ObjectDoesNotExist :
            return None

@register.filter
def get_message (message, ) :
    if isinstance(message, models_dialog.Message, ) :
        return message

    if isinstance(message, (models_dialog.ProfileMessageTop, models_dialog.ProfileMessage, ), ) :
        return message.message

