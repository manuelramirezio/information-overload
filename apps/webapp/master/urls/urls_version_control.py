# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *

from master.views import views_version_control

urlpatterns = patterns("",
    url(r"^api/revision/",
        views_version_control.APIRevision.as_view(), name="version_control_api_revision", ),

    url(r"^(?P<path>.*)/r(?P<to_revision>\d+)/r(?P<from_revision>\d+)/$",
        views_version_control.ShowRevision.as_view(),
        name="version_control_revision",
    ),

    url(r"^(?P<path>.*)/r(?P<to_revision>\d+)/$",
        views_version_control.ShowRevision.as_view(),
        name="version_control_revision0",
    ),

    url(r"^(?P<path>.*)/$",
        views_version_control.ShowFile.as_view(),
        name="version_control_file",
    ),

    url(r"^$",
        views_version_control.ShowRevision.as_view(),
        name="version_control_revision_index",
        kwargs=dict(
            to_revision=None,
        ),
    ),
)


