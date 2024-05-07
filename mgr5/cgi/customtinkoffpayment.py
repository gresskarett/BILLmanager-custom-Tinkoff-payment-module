#!/usr/bin/python3

"""
CGI скрипт для перехода в платёжную систему для оплаты.
"""

import os
import sys
os.chdir("/usr/local/mgr5")
sys.path.append("/root/practice/paymethod")

import typing as t

from billmgr import logger as logging
from customtinkoff import MODULE_NAME
from customtinkoff.tinkoffpayment import TinkoffPayment


logging.init_logging(MODULE_NAME)
logger = logging.get_logger(MODULE_NAME)

logger.info("run cgi/customtinkoffpayment")


def get_elid():
    input_str = os.environ['QUERY_STRING']
    for key, val in [param.split('=') for param in input_str.split('&')]:
        if key == "elid":
            return val


payment_environ: t.Dict[str, str] = {
    "elid": get_elid(),
    "cookies": os.environ["HTTP_COOKIE"],
    "http_host": os.environ.get("HTTP_HOST"),
    "request_method": os.environ.get("REQUEST_METHOD"),
    "https": os.environ.get("HTTPS")
}
logger.info("payment environment variables = " + str(payment_environ))

payment: TinkoffPayment = TinkoffPayment(**payment_environ)
redirect_url: str = payment.make()

sys.stdout.write(payment.get_redirect_request(redirect_url))
