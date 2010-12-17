# -*- coding: utf-8 -*-

import os

from django.db import transaction
from django.db.models import ObjectDoesNotExist
from django.core.management.base import BaseCommand, LabelCommand, CommandError

from IO.project import models as models_project
from IO.version_control import models as models_version_control

class Command (BaseCommand, ) :

    args = "<project code> <name> <revision number>"

    requires_model_validation = False

    @transaction.commit_on_success
    def handle (self, *a, **kw) :
        if len(a) < 2 :
            raise CommandError("Enter project code, version_control name and revision number.")

        (_project_code, _name, _revision_number, ) = a[0], a[1], None
        if len(a) > 2 :
            _revision_number = int(a[2])

        try :
            _info = models_version_control.Info.objects.get(project__code=_project_code, name=_name, )
        except ObjectDoesNotExist :
            raise CommandError("Create project first, using `create_project` command.")

        try :
            _info.revision_update(_revision_number, )
        except Exception, e :
            import traceback
            traceback.print_exc()
            raise CommandError(e, )

        print "Successfully updated from repository, '%s'" % (
            os.path.relpath(_info.repository_path), )

        return


import logging
logging.basicConfig(level=logging.INFO, )



