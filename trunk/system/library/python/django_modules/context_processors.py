# -*- coding: utf-8 -*-

from django.conf import settings

def read_settings (request) :
    return dict(settings=settings, )



