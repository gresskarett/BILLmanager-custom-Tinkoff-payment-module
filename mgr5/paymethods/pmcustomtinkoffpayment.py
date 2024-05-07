#!/usr/bin/python3

"""
Основной обработчик платёжной системы.
"""

import os
import sys
os.chdir("/usr/local/mgr5")
sys.path.append("/root/practice/paymethod")

from customtinkoff import logger
from customtinkoff.paymentmodule import PaymentModule
from customtinkoff.tinkoffpaymentmodule import TinkoffPaymentModule


logger.info("run paymethods/pmcustomtinkoffpayment")

payment_module: PaymentModule = TinkoffPaymentModule()
payment_module.process()
