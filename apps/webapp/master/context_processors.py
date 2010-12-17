# -*- coding: utf-8 -*-

from IO.project import models as models_project
from IO.dialog import models as models_dialog

def projects (request, ) :
    if not request.user.is_authenticated() :
        return dict()

    return dict(
        projects=models_project.Item.objects.all(),
    )

def profile_labels (request, ) :
    if not request.user.is_authenticated() :
        return dict()

    return dict(
        profile_labels=models_dialog.Label.objects.filter(
                profilemessage__profile=request.user.profile,
            ).distinct(),
    )


