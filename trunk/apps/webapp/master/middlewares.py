# -*- coding: utf-8 -*-

import re, traceback

from django.conf import settings
from django.http import HttpResponseRedirect

from django_modules.utils.url import get_path

RE_API = re.compile("\/api\/")

MEANINGLESS_PATH = (
    settings.MEDIA_URL,
    settings.STATICFILES_URL,
    settings.LOGIN_URL,
    "/favicon.ico",
    "/accounts/logout/",
)

class CheckAuthenticated (object, ) :
    def process_request (self, request, ) :
        if RE_API.search(request.path, ) :
            return

        for i in MEANINGLESS_PATH :
            if request.path.startswith(i, ) :
                return

        if not request.user.is_authenticated() :
            return HttpResponseRedirect(settings.LOGIN_URL + "?next=" + request.path_info, )

        return

class ExceptionHandler (object, ) :
    def process_exception (self, request, exception, ) :
        print request
        traceback.print_exc()


