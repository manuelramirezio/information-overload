# -*- coding: utf-8 -*-

from django.shortcuts import get_object_or_404
from django.views.generic import View
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, Http404
from django.core.paginator import Paginator, EmptyPage

from django_modules.utils.url import get_path

from IO.project import models as models_project

class InvalidRequest (Exception, ) : pass

class BaseProjectView (View, ) :
    def __init__ (self, *a, **kw) :
        super(BaseProjectView, self).__init__(*a, **kw)

        self._project = None

    def _dispatch (self, request, *a, **kw) :
        if not kw.has_key("project") :
            raise InvalidRequest

        self._project = get_object_or_404(models_project.Item, code=kw.get("project", ))
        del kw["project"]

        return (request, a, kw, )

    def dispatch (self, request, *a, **kw) :
        try :
            (request, a, kw, ) = self._dispatch(request, *a, **kw)
        except InvalidRequest :
            return self.http_method_not_allowed(request, *a, **kw)

        return super(BaseProjectView, self).dispatch(request, *a, **kw)

class BasePaginationView (View, ) :
    def __init__ (self, *a, **kw) :
        super(BasePaginationView, self).__init__(*a, **kw)
        self._page_number = 1

    def dispatch (self, request, *a, **kw) :
        try :
            self._page_number = int(request.REQUEST.get("p", 1, ), )
        except (TypeError, ValueError, ) :
            self._page_number = 1

        return super(BasePaginationView, self).dispatch(request, *a, **kw)

class BaseDialog (BasePaginationView) :
    def _remember_path (self, request, ) :
        request.session["dialogs.path.latest"] = get_path(request)

    def dispatch (self, request, *a, **kw) :
        if request.method == "GET" :
            self._remember_path(request, )

        try :
            return super(BaseDialog, self).dispatch(request, *a, **kw)
        except EmptyPage :
            return HttpResponseRedirect(request.path + "?p=1", )


