# -*- coding: utf-8 -*-

CREDENTIAL = (
    "", # user id
    "", # password
)

MAIL_SERVER_IMAP = ("imap.gmail.com", 993, )
MAIL_SERVER_SMTP = ("smtp.gmail.com", 587, )

MAILBOX = ""

MAIL_ADDRESS = ""

INTERVAL = 20
NUMBER_OF_EMAIL_PER_SESSION = 100
NUMBER_OF_EMAIL_ASYNC = 30

API_URL = "http://127.0.0.1:9000/dialog/api/message/email/"

import os, sys

STORAGE_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "../../",
        "storage",
        "dialog_messages",
    ),
)

try :
    from config_local import *
except ImportError :
    pass

if not os.path.exists(STORAGE_PATH) :
    raise RuntimeError(u"`STORAGE_PATH` does not exists.", )


