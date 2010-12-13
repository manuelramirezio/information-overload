# -*- coding: utf-8 -*-

import uuid

from django import forms
from django.conf import settings
from django.db.models import Q
from django.core.mail import EmailMessage

from django_modules.shortcuts import render_to_string

import models as models_developer

class ChangeProfilePicture (forms.ModelForm, ) :
    class Meta :
        model = models_developer.Profile
        fields = ("picture", )

    message_success = u"Successfully changed your profile picture."
    message_error = u"Failed to change your profile picture."

    form_name = forms.CharField(initial="ChangeProfilePicture", widget=forms.HiddenInput, )
    my_picture = forms.ImageField()

    def __init__ (self, request, *a, **kw) :
        super(ChangeProfilePicture, self).__init__(*a, **kw)

    def clean_my_picture (self, ) :
        self.cleaned_data["picture"] = self.cleaned_data["my_picture"]
        return self.cleaned_data["my_picture"]

class ConfirmNewEmail (forms.Form, ) :
    message_success = u"We sent confirmation email to your address, check it."
    message_error = u"Failed to sent confirmation email."

    form_name = forms.CharField(initial="ConfirmNewEmail", widget=forms.HiddenInput, )
    email = forms.EmailField(
            widget=forms.TextInput(attrs=dict(
                placeholder=u"Add your new email address",
                size=30,
            ), ),
        )

    def __init__ (self, request, *a, **kw) :
        self._request = request
        self._instance = kw.get("instance")
        del kw["instance"]

        super(ConfirmNewEmail, self).__init__(*a, **kw)

    def clean_email (self, ) :
        _v = self.cleaned_data.get("email")

        # check whether email was already registered to other profiled user.
        _q = Q(
            user__email=_v,
        ) | Q(
            users__email=_v,
        )
        if models_developer.Profile.objects.filter(_q, ).count() > 0 :
            raise forms.ValidationError(u"'%s' is already registered." % _v, )

        return _v

    def save (self, *a, **kw) : # send confirmation email
        _email = self.cleaned_data.get("email")
        _key = str(uuid.uuid1(), )

        _message_body = render_to_string(
            self._request,
            "developer/confirm_email.html",
            {
                "key": _key,
                "email": _email,
            },
        )

        _msg = EmailMessage(
            u"[I.O] '%s' requests developer email confirmation." % _email,
            _message_body,
            u"%s <%s>" % (u"I.O Service", settings.EMAIL_IO_SERVICE, ),
            [_email, ],
        )
        _msg.content_subtype = "html"
        if not _msg.send() :
            return False

        models_developer.ConfirmEmail.objects.filter(
            profile=self._instance,
            email=_email,
        ).delete()

        models_developer.ConfirmEmail.objects.create(
            key=_key,
            profile=self._instance,
            email=_email,
        )

        return True




