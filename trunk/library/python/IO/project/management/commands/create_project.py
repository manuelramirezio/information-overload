# -*- coding: utf-8 -*-

from django.db import transaction
from django.db.models import ObjectDoesNotExist
from django.core.management.base import BaseCommand, LabelCommand, CommandError

from IO.developer import models as models_developer
from IO.project import models as models_project
from IO.version_control import models as models_version_control

class Command (BaseCommand, ) :

    args = "<project name> <code name>"
    requires_model_validation = False

    @transaction.commit_on_success
    def handle (self, *a, **kw) :
        if len(a) < 2 :
            raise CommandError("Enter project name and code name.")

        (_project_name, _code_name, ) = a[0], a[1]
        if _code_name.find(" ") != -1 :
            raise CommandError("Enter the proper code name, don't use the blank space.")

        (_project, _created, ) = models_project.Item.objects.get_or_create(
            name=_project_name,
            code=_code_name,
            author=models_developer.Profile.objects.all()[0].user,
        )
        if not _created :
            raise CommandError("This project, '%s' was already created." % _project_name, )

        print "Successfully project, '%s' was created" % _project

        return


