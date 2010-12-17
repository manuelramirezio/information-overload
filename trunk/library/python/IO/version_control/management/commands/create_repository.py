# -*- coding: utf-8 -*-

import os, re

from django.db import transaction
from django.db import IntegrityError
from django.db.models import ObjectDoesNotExist
from django.core.management.base import BaseCommand, LabelCommand, CommandError

from IO.project import models as models_project
from IO.version_control import models as models_version_control

RE_INFO_NAME = re.compile("^[\w\-\.][\w\-\.]*$", re.I, )

class Command (BaseCommand, ) :

    args = "<project code> <name> <repository url>"

    requires_model_validation = False

    @transaction.commit_on_success
    def handle (self, *a, **kw) :
        if len(a) < 2 :
            raise CommandError("Enter project code and repository url.")

        (_project_code, _name, _repository_url, ) = a[0], a[1], a[2]

        _repository_path = models_version_control.get_repository_path(_project_code, _name, )
        if os.path.exists(_repository_path) :
            raise CommandError("Repository, '%s' is already created, clean it up first." %
                    os.path.relpath(_repository_path), )

        if not RE_INFO_NAME.match(_name) :
            raise CommandError("Enter proper name.")

        try :
            _project = models_project.Item.objects.get(code=_project_code, )
            _info = models_version_control.Info.objects.create(
                project=_project,
                name=_name,
                repository_url=_repository_url,
            )
        except ObjectDoesNotExist :
            raise CommandError("Create project first, using `create_project` command.")
        except IntegrityError :
            raise CommandError("'%s' for '%s' was already exists." % (_name, _project, ), )

        logging.info("Successfully created version_control.")
        try :
            _info.checkout()
        except Exception, e :
            import traceback
            traceback.print_exc()
            raise CommandError(e, )

        logging.info("Successfully checked out from repository, '%s' to '%s'" % (
            _repository_url, os.path.relpath(_info.repository_path), ),
        )

        return

import logging
logging.basicConfig(level=logging.INFO, )

