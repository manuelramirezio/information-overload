# -*- coding: utf-8 -*-

import os, pprint, urlparse, cgi, StringIO, uuid

from django.conf import settings
from django.contrib.auth import models as models_auth
from django.db import IntegrityError
from django.db.models import Q, ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, Http404
from django.views.generic import View
from django.views.static import serve
from django.core.paginator import Paginator, EmptyPage
from django.test.client import FakePayload

from django_modules.shortcuts import render_to_response
from django_modules.http import HttpResponseJSON
from django.views.decorators.csrf import csrf_exempt

from spikeekips import _email

from IO.common import models as models_common
from IO.developer import models as models_developer
from IO.dialog import models as models_dialog, forms as forms_dialog

from base import BasePaginationView, BaseDialog

def get_payload (request, message_uid, filename, ) :
    _object = get_object_or_404(models_dialog.Message, uid=message_uid, )
    _payload = get_object_or_404(_object.payloads, filename=filename, )

    _response = serve(
        request,
        os.path.join(
            settings.MEDIA_ROOT,
            _payload.file.name,
        ),
    )
    _response["Content-Disposition"] = (u"attachment; filename=\"%s\"" %
        _payload.filename).encode("utf-8")

    return _response

class APILabelSearch (View, ) :
    @csrf_exempt
    def dispatch (self, *a, **kw) :
        return super(APILabelSearch, self).dispatch(*a, **kw)

    def post (self, request, ) :
        _term = request.POST.get("term", "").strip().lower()
        _labels_mine = models_dialog.Label.objects.filter(
            profilemessage__profile=request.user.profile,
            name__contains=_term,
        ).distinct().values("pk", "name")

        _labels = [i.get("name") for i in _labels_mine]
        if len(_labels_mine) < 5 :
            _labels_etc = models_dialog.Label.objects.filter(
                name__contains=_term,
            ).exclude(pk__in=[i.get("pk") for i in _labels_mine]).distinct().values("name")

            _labels.extend([i.get("name") for i in _labels_etc])

        return HttpResponseJSON(_labels, )

class APIMessage (View, ) :
    @csrf_exempt
    def dispatch (self, *a, **kw) :
        return super(APIMessage, self).dispatch(*a, **kw)

    def post (self, request, message_type, ) :
        _raw_post_data = request._stream.read()
        (_key, _pdict, )  = cgi.parse_header(request.META.get("CONTENT_TYPE"), )
        if not _key.startswith("multipart") :
            _post_data = dict(urlparse.parse_qsl(_raw_post_data, )).get("message", "", )
        else :
            _post_data = cgi.parse_multipart(
                StringIO.StringIO(_raw_post_data, ),
                _pdict,
            ).get("message", list(), )[0]

        try :
            (_message, _created, ) = forms_dialog.get_model(message_type, )(
                _post_data, ).save()
        except Exception, e :
            import traceback
            traceback.print_exc()

            f = file("/tmp/%s.eml" % str(uuid.uuid1(), ), "w")
            f.write(_post_data, )
            traceback.print_exc(file=f, )
            f.close()

            return HttpResponseBadRequest(e, )

        return HttpResponse(status=_created and 200 or 202, )

class Dialog (BaseDialog, ) :
    def get (self, request, username=None, ) :
        if not username :
            _qs = models_dialog.Message.objects.all()
        else :
            _user = get_object_or_404(models_auth.User, username=username, )

            _profile = None
            if _user.profile :
                _profile = _user.profile
            else :
                _profile = models_developer.Profile.objects.get_by_user(_user, )

            if _profile :
                _qs = models_dialog.Message.objects.filter_by_profile(_user.profile, )
            else :
                _qs = models_dialog.Message.objects.filter_by_users(_user, )

        _qs = _qs.filter(parent__isnull=True, )

        _page = Paginator(
            _qs.distinct().order_by("-time_sent"),
            18,
        ).page(self._page_number, )

        return render_to_response(
            request,
            "dialog/dialogs.html",
            {
                "page": _page,
            }
        )

class DialogWithProfile (BaseDialog, ) :
    def get (self, request, labels=None, username=None, starred=None, ) :
        _q = Q(profile=request.user.profile, )

        _label_names = list()

        if labels and labels.strip() :
            _label_names = [i for i in labels.split(",") if i.strip()]
            if _label_names :
                _q = _q & Q(labels__name__in=_label_names, )

        if type(starred) in (bool, ) :
            _q = _q & Q(is_starred=starred, )

        _page = Paginator(
            models_dialog.ProfileMessageTop.objects.filter(
                _q,
            ).distinct().order_by("-time_updated"),
            18,
        ).page(self._page_number, )

        return render_to_response(
            request,
            "dialog/dialogs_with_profile_message.html",
            {
                "page": _page,
                "labels": [i for i in models_dialog.Label.objects.filter(
                    name__in=_label_names)],
            }
        )

class BaseMessage (View, ) :
    def __init__ (self, *a, **kw) :
        super(BaseMessage, self).__init__(*a, **kw)
        self._object = None

    def dispatch (self, *a, **kw) :
        self._object = get_object_or_404(models_dialog.Message, uid=kw.get("message_uid"), )
        del kw["message_uid"]

        return super(BaseMessage, self).dispatch(*a, **kw)

class Message (BaseMessage, ) :
    @csrf_exempt
    def dispatch (self, *a, **kw) :
        return super(Message, self).dispatch(*a, **kw)

    def get (self, request, ) :
        for i in self._object.dialog.all() :
            (_um, _created, ) = models_dialog.ProfileMessage.objects.get_or_create(
                profile=request.user.profile,
                message=i,
            )
            if not _um.parent_top.is_read :
                _parent_top = _um.parent_top
                _parent_top.is_read = True
                _parent_top.save()

        return render_to_response(
            request,
            "dialog/dialog.html",
            {
                "object": self._object,
                "user_message": None,
            }
        )

class Action (BaseMessage, ) :
    def dispatch (self, *a, **kw) :
        return super(Action, self).dispatch(*a, **kw)

    def post (self, request, ) :
        action = request.REQUEST.get("action", "").strip()
        if not action :
            raise Http404

        (_profile_message, _created, ) = models_dialog.ProfileMessage.objects.get_or_create(
            profile=request.user.profile,
            message=self._object,
        )

        if action == "archive" :
            _profile_message.archive()
        elif action == "unarchive" :
            _profile_message.unarchive()
        elif action in ("star", "unstar", ) :
            _profile_message.is_starred = action == "star"
            _profile_message.save()
        elif action == "set_labels" :
            _l = [i.strip() for i in request.REQUEST.get("labels").split(",") if i.strip()]

            _labels = list()
            for i in _l :
                _labels.append(models_dialog.Label.objects.get_or_create(name=i, )[0], )

            _profile_message.labels = _labels
        elif action == "archive_all" :
            for i in models_dialog.ProfileMessageTop.objects.filter(profile=request.user.profile, ) :
                i.archive()
        else :
            raise Http404

        return HttpResponse()


