# -*- coding: utf-8 -*-

from IO.admin import admin, admin_site, admin_site_raw
from django.core.urlresolvers import reverse

import models as models_version_control

class AuthorModelAdmin (admin.ModelAdmin, ) :
    list_display = ("name", "link_info", "link_profile", )
    list_display_links = ("name", )

    def link_info (self, obj, ) :
        return u"""
<a href="%s">%s</a>
        """ % (
            reverse("admin:version_control_info_change", args=(obj.info.pk, ), ),
            obj.info,
        )

    link_info.allow_tags = True
    link_info.short_description = u"Version Control"

    def link_profile (self, obj, ) :
        if not obj.profile :
            return u""

        return u"""
<a href="%s">%s</a>
        """ % (
            reverse("admin:developer_profile_change", args=(obj.profile.pk, ), ),
            obj.info,
        )

    link_profile.allow_tags = True
    link_profile.short_description = u"Profile"

admin_site_raw.register(models_version_control.Info, )
admin_site_raw.register(models_version_control.File, )
admin_site_raw.register(models_version_control.Revision, )
admin_site_raw.register(models_version_control.RevisionFile, )
admin_site_raw.register(models_version_control.Author, )
admin_site_raw.register(models_version_control.Message, )
admin_site_raw.register(models_version_control.Ignore, )

admin_site.register(models_version_control.Info, )
admin_site.register(models_version_control.Author, AuthorModelAdmin, )



