#!/usr/bin/python3

"""
CGI скрипт для перехода в платёжную систему для оплаты.
"""

from customtinkoffpayment.tinkoffpaymentcgi import TinkoffPaymentCgi


TinkoffPaymentCgi().process()
