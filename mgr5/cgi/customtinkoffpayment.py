#!/usr/bin/python3

"""
CGI скрипт для перехода в платёжную систему для оплаты.
"""

import sys

from customtinkoffpayment.tinkoffpayment import TinkoffPayment


payment: TinkoffPayment = TinkoffPayment()
payment_request: str = payment.get_redirect_request()
sys.stdout.write(payment_request)
