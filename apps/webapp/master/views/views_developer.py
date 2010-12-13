# -*- coding: utf-8 -*-

import os, pysvn, logging, datetime

from django.contrib import messages
from django.contrib.auth import models as models_auth
from django.db.models import Q, ObjectDoesNotExist
from django.http import HttpResponse
from django.views.generic import View
from django.shortcuts import get_object_or_404

from django_modules.shortcuts import render_to_response

from IO.developer import models as models_developer, forms as forms_developer
from IO.project import models as models_project
from IO.version_control import models as models_version_control

class BaseUserView (View, ) :
    def __init__ (self, *a, **kw) :
        super(BaseUserView, self).__init__(*a, **kw)

        self._profile = None
        self._user_unknown = None

    def dispatch (self, request, *a, **kw) :
        if not kw.has_key("username") :
            return self.http_method_not_allowed(request, *a, **kw)

        _username = kw.get("username", )
        _qs = models_developer.Profile.objects.filter(
            Q(
                user__username=_username,
            ) | Q(
                users__username=_username,
            )
        ).distinct()
        if _qs.count() > 0 :
            self._profile = _qs[0]
        else :
            self._user_unknown = get_object_or_404(
                models_auth.User,
                username=_username,
            )

        del kw["username"]

        return super(BaseUserView, self).dispatch(request, *a, **kw)

FORMS_PROFILE = (
    "ChangeProfilePicture",
    "ConfirmNewEmail",
)

class Profile (BaseUserView, ) :
    def get (self, request, forms=dict(), ) :
        if not self._profile and self._user_unknown :
            return render_to_response(
                request,
                "developer/profile_unknown.html",
                {
                    "object": self._user_unknown,
                    #"dialogs": _page,
                }
            )

        if request.user.profile == self._profile :
            for i in FORMS_PROFILE :
                if not forms.has_key(i) :
                    forms[i] = getattr(forms_developer, i, )(
                        request, instance=self._profile, )

        return render_to_response(
            request,
            "developer/profile.html",
            {
                "object": self._profile.user,
                "forms": forms,
                "my_projects": models_project.Item.objects.filter(
                        version_control__revision__author__profile__users=self._profile,
                    ).distinct(),
                #"dialogs": _page,
            }
        )

    def post (self, request, ) :
        _form_name = request.POST.get("form_name", "none", )
        if not hasattr(forms_developer, _form_name, ) :
            messages.error(request, u"Bad Request", )
            return self.get(request, )

        _form = getattr(forms_developer, _form_name, )(
            request, request.POST, request.FILES, instance=self._profile, )

        if not _form.is_valid() :
            print _form.errors
            return self.get(request, forms={_form_name: _form, }, )

        messages.info(
            request,
            _form.save() and _form.message_success or _form.message_error,
        )
        return self.get(request, )


class ConfirmEmail (View, ) :
    def get (self, request, key, ) :
        _object = get_object_or_404(models_developer.ConfirmEmail,
            profile=request.user.profile,
            key=key,
        )

        _email = _object.email
        _is_valid = _object.is_valid()

        _user = None
        if _object.is_valid() :
            (_user, _created, ) = models_developer.Profile.objects.get_or_create_user(
                request.user.username,
                _object.email,
                password=None,
            )
            _profile = request.user.profile
            _profile.users.add(_user, )

        _object.delete()

        return render_to_response(
            request,
            "developer/confirmed_email.html",
            {
                "email": _email,
                "is_valid": _is_valid,
                "created_user": _user,
            }
        )


