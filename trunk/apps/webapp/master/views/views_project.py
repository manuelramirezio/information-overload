# -*- coding: utf-8 -*-

import os, pysvn, logging, datetime

from django.db.models import ObjectDoesNotExist
from django.http import HttpResponse
from django.views.generic import View
from django.shortcuts import get_object_or_404

from django_modules.shortcuts import render_to_response

from IO.developer import models as models_developer
from IO.project import models as models_project
from IO.version_control import models as models_version_control

from base import BaseProjectView

class Item (BaseProjectView, ) :
    def get (self, request, ) :
        return render_to_response(
            request,
            "project/item.html",
            {
                "project": self._project,
            }
        )


def index (request, ) :
    return render_to_response(
        request,
        "project/index.html",
        {
        }
    )


