#!/usr/bin/python3

"""
CGI скрипт для перехода в платёжную систему для оплаты.
"""

import sys

from customtinkoffpayment.tinkoffpayment import TinkoffPayment


# TODO: get elid, передать аргументом в класс. Сейчас класс сам почему-то получает свой elid
payment: TinkoffPayment = TinkoffPayment()
redirect_url: str = payment.make()

sys.stdout.write(payment.get_redirect_request(redirect_url))
