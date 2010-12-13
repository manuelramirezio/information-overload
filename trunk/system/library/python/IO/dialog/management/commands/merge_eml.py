# -*- coding: utf-8 -*-

import time, glob, logging

from django.db import transaction
from django.db.models import ObjectDoesNotExist
from django.core.management.base import BaseCommand, LabelCommand, CommandError

from IO.dialog import models as models_dialog, forms as forms_dialog

class Command (BaseCommand, ) :

    args = "<eml file>"
    requires_model_validation = False

    @transaction.commit_on_success
    def handle (self, *a, **kw) :
        if len(a) < 1 :
            raise CommandError("Enter eml file path.")

        _s = time.time()

        for i in a :
            _post_data = file(i).read()

            logging.info(u"Merging %s." % i, )
            try :
                (_message, _created, ) = forms_dialog.get_model("email", )(_post_data, ).save()
            except Exception, e :
                import traceback
                traceback.print_exc()
                raise CommandError(u"Failed to merge in this file, %s" % i, )

        logging.info(u"Total elapsed time is %f." % (time.time() - _s, ), )

        return
        if _code_name.find(" ") != -1 :
            raise CommandError("Enter the proper code name, don't use the blank space.")

logging.basicConfig(level=logging.INFO, )


