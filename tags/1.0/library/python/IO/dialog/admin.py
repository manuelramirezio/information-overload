# -*- coding: utf-8 -*-

from IO.admin import admin, admin_site, admin_site_raw
from django.core.urlresolvers import reverse

from IO.developer import models as models_developer
import models as models_dialog

class MessageModelAdmin (admin.ModelAdmin, ) :
    list_display = ("link_subject", "link_sender", )
    #list_display_links = ("link_subject", )

    def link_subject (self, obj, ) :
        return obj.subject.strip() and obj.subject or u"<No Subject>"

    def link_sender (self, obj, ) :
        _profile = models_developer.Profile.objects.get_by_user(obj.sender, )
        return u"""
<a href="%s">%s</a>
        """ % (
            reverse("admin:auth_user_change", args=(obj.sender.pk, ), ),
            _profile and _profile or (obj.sender.first_name and obj.sender.first_name or obj.sender.email),
        )

    link_sender.allow_tags = True


admin_site_raw.register(models_dialog.Label, )
admin_site_raw.register(models_dialog.Message, MessageModelAdmin, )
admin_site_raw.register(models_dialog.Payload, )
admin_site_raw.register(models_dialog.ProfileMessageTop, )
admin_site_raw.register(models_dialog.ProfileMessage, )
admin_site_raw.register(models_dialog.ConnectedMessage, )





