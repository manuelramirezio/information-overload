# -*- coding: utf-8 -*-

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.views.generic import View
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth import models as models_auth, views as views_auth
from django.core.urlresolvers import reverse

from IO.developer import models as models_developer

def index (request, ) :
    return HttpResponseRedirect("/", )

def login (request, ) :
    views_auth.logout(request, )
    return views_auth.login(request, template_name="auth/login.html", )

def password_change_done (request, ) :
    messages.info(request, u"Successfully changed password.", )

    return HttpResponseRedirect(reverse("developer", kwargs=dict(username=request.user.username, )))

