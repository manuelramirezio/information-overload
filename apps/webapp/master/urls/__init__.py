# -*- coding: utf-8 -*-

import os

import django
from django.conf import settings
from django.conf.urls.defaults import *

from IO.admin import admin_site, admin_site_raw

from django.contrib import admin
admin.autodiscover()

import urls_auth, urls_developer, urls_project, urls_dialog

from django.contrib.staticfiles.urls import staticfiles_urlpatterns
urlpatterns = staticfiles_urlpatterns()

urlpatterns += patterns("",
    url(r"^_media/(?P<path>.*)$", "django.views.static.serve",
            {"document_root": settings.MEDIA_ROOT, }, name="media", ),

    url(r"^_m/(?P<path>.*)$", "django.views.static.serve",
            {"document_root": settings.STATICFILES_DIRS[0]}, name="static_media", ),

    (r"^static/admin/img/(?P<path>.*)", "django.views.static.serve", {
            "document_root": os.path.join(settings.MASTER_PATH, "media", "admin", "img", ),
        }, ),
    (r"^static/admin/(?P<path>.*)", "django.views.static.serve", {
        "document_root": os.path.join(django.__path__[0], "contrib", "admin", "media", ),
        }, ),

    # Uncomment the next line to enable the admin:
    (r"^.*/login/", "master.views.views_auth.login", ),
    (r"^.*/logout/", "django.contrib.auth.views.logout_then_login", ),

    (r"^admin/raw/", include(admin_site_raw.urls), ),
    (r"^admin/", include(admin_site.urls), ),

    (r"^accounts/", include(urls_auth), ),

    (r"^developer/(?P<username>.*)/dialog/", include(urls_dialog.Developer(), ), ),
    (r"^developer/", include(urls_developer, )),
    (r"^dialog/", include(urls_dialog.Global(), ), ),

    (r"^(?P<project>[\w_\.\-]+)/", include(urls_project, )),

    (r"", "master.views.views_project.index", ),
)

