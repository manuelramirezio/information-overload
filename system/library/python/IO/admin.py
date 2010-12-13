# -*- coding: utf-8 -*-

from django.contrib import admin

class AdminSite (admin.AdminSite, ) :
    pass

admin_site = AdminSite()
admin_site_raw = admin.site





