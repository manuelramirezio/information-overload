# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *

from master.views import views_dialog

class Global (object, ) :
    urlpatterns = patterns("",
        url(r"^api/message/(?P<message_type>.*)/$", views_dialog.APIMessage.as_view(),
            name="dialog_api_message", ),

        url(r"^(?P<message_uid>.*)/action/$", views_dialog.Action.as_view(),
            name="dialog_message_action", ),
        url(r"^(?P<message_uid>.*)/payload/(?P<filename>.*)/$",
            "master.views.views_dialog.get_payload", name="dialog_message_payload", ),
        url(r"^(?P<message_uid>.*)/$", views_dialog.Message.as_view(), name="dialog_message", ),

        url(r"^$", views_dialog.Dialog.as_view(), name="dialog_index", ),
    )

class Developer (object, ) :
    urlpatterns = patterns("",
        url(r"^^(?P<labels>.*)/starred/$", views_dialog.DialogWithProfile.as_view(),
            kwargs=dict(
                starred=True,
            ),
        ),
        url(r"^starred/$", views_dialog.DialogWithProfile.as_view(),
            name="dialog_developer_by_starred",
            kwargs=dict(
                starred=True,
            ),
        ),
        url(r"^(?P<labels>.*)/$", views_dialog.DialogWithProfile.as_view(),
            name="dialog_developer_by_labels", ),
        url(r"^$", views_dialog.Dialog.as_view(), name="dialog_developer", ),
    )


