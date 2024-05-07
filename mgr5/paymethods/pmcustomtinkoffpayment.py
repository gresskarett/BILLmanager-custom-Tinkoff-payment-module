#!/usr/bin/python3

"""
Основной обработчик платёжной системы.
"""

import os
import sys
os.chdir("/usr/local/mgr5")
sys.path.append("/root/practice/paymethod")

from billmgr import logger as logging
from customtinkoff import MODULE_NAME
from customtinkoff.paymentmodule import PaymentModule
from customtinkoff.tinkoffpaymentmodule import TinkoffPaymentModule


logging.init_logging(MODULE_NAME)
logger = logging.get_logger(MODULE_NAME)

logger.info("run paymethods/pmcustomtinkoffpayment")

payment_module: PaymentModule = TinkoffPaymentModule()
payment_module.process()
