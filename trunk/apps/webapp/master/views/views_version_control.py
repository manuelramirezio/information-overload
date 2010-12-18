# -*- coding: utf-8 -*-

import os, pysvn, logging, datetime

from django.db.models import Max, ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt

from django_modules.shortcuts import render_to_response

from IO.dialog import models as models_dialog
from IO.developer import models as models_developer
from IO.version_control import models as models_version_control

from base import BaseProjectView, InvalidRequest, BasePaginationView, BaseDialog

class BaseVersionControlView (BaseProjectView, ) :
    def __init__ (self, *a, **kw) :
        super(BaseVersionControlView, self).__init__(*a, **kw)
        self._info = None

    def _dispatch (self, request, *a, **kw) :
        (request, a, kw, ) = super(BaseVersionControlView, self)._dispatch(request, *a, **kw)

        if not kw.has_key("name") :
            raise InvalidRequest

        self._info = get_object_or_404(
            models_version_control.Info, project=self._project, name=kw.get("name", ))
        del kw["name"]

        return (request, a, kw, )

class APIRevision (BaseVersionControlView, ) :
    @csrf_exempt
    def dispatch (self, *a, **kw) :
        return super(APIRevision, self).dispatch(*a, **kw)

    def get (self, request, number=None, ) : # get revision info
        if number :
            _revision = get_object_or_404(self._info.revision, number=int(number, ), )
        else :
            _revision = self._info.latest_revision

        return HttpResponse(str(_revision.number, ), )

    def post (self, request, number=None, ) : # update
        (_latest_number, _updated_number, ) = self._info.revision_update(number, )
        if not _updated_number :
            return HttpResponse(u"Not modified: latest revision is %s" %
                _latest_number, status=304, )

        return HttpResponse(u"Updated: latest revision is %s" % _updated_number, )

class ShowFile (BaseVersionControlView, ) :
    def get (self, request, path, ) :
        try :
            _root = models_version_control.File.objects.get(
                info=self._info,
                abspath=models_version_control.File.normalize_path(path, ),
            )
        except ObjectDoesNotExist :
            return HttpResponseBadRequest(u"Invalid `path`, '%s'." % path, )

        return render_to_response(
            request,
            "version_control/revisions_file.html",
            {
                "project": self._project,
                "info": self._info,
                "root": _root,
                "revisions": _root.revision_file.all().order_by(
                    "-revision__number"),
            }
        )

class ShowRevision (BaseVersionControlView, BaseDialog, ) :
    def get (self, request, to_revision, path=None, from_revision=None, ) :
        if from_revision :
            try :
                from_revision = int(from_revision, )
            except (ValueError, TypeError, ) :
                return HttpResponseBadRequest(u"Invalid `from_revision`, it must be integer.")
            else :
                if from_revision > to_revision :
                    return HttpResponseBadRequest(
                        u"`from_revision` can not exceeed `to_revision`.")

        if to_revision is None :
            _to_revision = self._info.latest_revision
            if _to_revision is None :
                raise Http404
        else :
            _to_revision = get_object_or_404(self._info.revision, number=to_revision, )

        if from_revision is None :
            from_revision = _to_revision.number - 1

        if from_revision < 1 :
            from_revision = 1

        _root = self._info.root
        if path and path.strip() :
            try :
                _root = models_version_control.File.objects.get(
                    info=self._info,
                    abspath=models_version_control.File.normalize_path(path, ),
                )
            except ObjectDoesNotExist :
                return HttpResponseBadRequest(u"Invalid `path`, '%s'." % path, )

        _context = dict(
            project=self._project,
            info=self._info,
        )

        return getattr(self, "_get_%s" % _root.filetype)(
            request, _context, from_revision, _to_revision, _root, )

    def _get_directory (self, request, context, from_revision_number, to_revision, root) :
        context.update({
            "root": root,
            "to_revision": to_revision,
            "from_revision_number": from_revision_number,
            "revision_files": to_revision.diff_by_number(from_revision_number, root=root, ),
        }, )

        _page = Paginator(
            models_dialog.ConnectedMessage.objects.filter(
                to_revision,
            ).order_by("-time_sent"),
            self._page_number < 2 and 5 or 18,
        ).page(self._page_number, )

        context.update(dict(page=_page, ), )

        return render_to_response(
            request,
            "version_control/revision_directory.html",
            context,
        )

    def _get_regular (self, request, context, from_revision_number, to_revision, fileobj, ) :
        _revision_file = get_object_or_404(to_revision.files, file=fileobj, )

        context.update({
            "root": fileobj,
            "to_revision": to_revision,
            "from_revision_number": from_revision_number,
            "revision": _revision_file.diff_by_number(from_revision_number, ),
        }, )

        return render_to_response(
            request,
            "version_control/revision_regular.html",
            context,
        )




