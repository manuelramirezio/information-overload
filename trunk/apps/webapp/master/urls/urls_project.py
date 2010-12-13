# -*- coding: utf-8 -*-

from django.conf import settings
from django.conf.urls.defaults import *

from master.views import views_project
from master.urls import urls_version_control

urlpatterns = patterns("",
    (r"^vc/(?P<name>[\w\.\-][\w\.\-]*)/", include(urls_version_control, )),

    url(r"^", views_project.Item.as_view(), name="project", ),
)



