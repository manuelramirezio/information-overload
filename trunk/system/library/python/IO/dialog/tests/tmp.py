# -*- coding: utf-8 -*-


import sys
from spikeekips import _email

from IO.dialog import utils  as utils_dialog

from email import utils as utils_email

_msg = _email.Message.from_string(file(sys.argv[1]).read(), )
print _msg.get_header("from", raw=True, )
for a, b in _msg.get_header("from", ) :
    print a.encode("utf-8"), b

#for i in _msg.get_attachments() :
#    print i.get("mimetype")
#    print len(i.get("mimetype"), )
#    #print i.get("filename")
#    #print utils_dialog.normalize_filename(i.get("filename"), )
#
#
#
