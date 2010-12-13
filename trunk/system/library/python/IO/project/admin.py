# -*- coding: utf-8 -*-

from IO.admin import admin, admin_site, admin_site_raw

import models as models_project

admin_site.register(models_project.Item, )
admin_site_raw.register(models_project.Item, )





