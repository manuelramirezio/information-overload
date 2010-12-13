# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *
from django.core.urlresolvers import reverse
from django.contrib.auth import urls as urls_auth

urlpatterns = patterns("",
    (r"^login/$", "master.views.views_auth.login", ),

    url(r"^password_change/done/$", "master.views.views_auth.password_change_done",
        name="password_change_done",
    ),
    url(r"^password_change/$", "django.contrib.auth.views.password_change",
        name="password_change",
        kwargs=dict(
            template_name="auth/password_change_form.html",
            post_change_redirect="/accounts/password_change/done/",
        ),
    ),

    (r"^", include(urls_auth, ), ),
)


