# -*- coding: utf-8 -*-

from django.conf import settings
from django.conf.urls.defaults import *

from master.views import views_developer

urlpatterns = patterns("",
    url(r"^confirm/email/(?P<key>.*)/", views_developer.ConfirmEmail.as_view(),
        name="confirm_email", ),
    url(r"^(?P<username>[\w\-]+)/", views_developer.Profile.as_view(), name="developer", ),
)



