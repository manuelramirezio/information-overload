# -*- coding: utf-8 -*-

import sys, os, subprocess, logging

from django.core.management.base import BaseCommand, LabelCommand, CommandError

class DebugCommand (BaseCommand, ) :
    def __init__ (self, *a, **kw) :
        super(DebugCommand, self).__init__(*a, **kw)
        if os.getenv("PYTHONDEBUG") :
            logging.basicConfig(level=logging.DEBUG, )

class PidCommand (BaseCommand, ) :
    def get_pid_filename (self, *a, **kw) :
        return "/tmp/%s-%s.pid" % (
            os.getenv("DJANGO_SETTINGS_MODULE"),
            os.path.splitext(os.path.basename(__file__))[0].lower(),
        )

    def execute (self, *a, **kw) :
        _pidfile = self.get_pid_filename(*a, **kw)
        if _pidfile :
            if os.path.exists(_pidfile) :
                _rcode = subprocess.call(
                    (
                        "ps",
                        "-p",
                        file(_pidfile).read().strip(),
                    ),
                    stdout=file("/dev/null"),
                    stderr=file("/dev/null"),
                    shell=False,
                )
                if _rcode == 0 :
                    sys.exit(1)

            with file(_pidfile, "w") as f :
                f.write(str(os.getpid()))

        return super(PidCommand, self).execute(*a, **kw)


