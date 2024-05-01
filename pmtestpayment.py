#!/usr/bin/python3

"""
Основной обработчик платёжной системы.
"""

from xml.etree import ElementTree as ET
import typing as t

import requests

from billmgr import db
from billmgr.misc import MgrctlXml
from payment import generate_token, PaymentStatus, PaymentModule
import billmgr.exception
import billmgr.logger as logging
import payment


MODULE = 'payment'

logging.init_logging('pmtestpayment')
logger = logging.get_logger('pmtestpayment')


class TestPaymentModule(PaymentModule):

    def __init__(self):
        super().__init__()

        self.features[payment.FEATURE_CHECKPAY] = True
        self.features[payment.FEATURE_REDIRECT] = True
        self.features[payment.FEATURE_NOT_PROFILE] = True
        self.features[payment.FEATURE_PMVALIDATE] = True

        self.params[payment.PAYMENT_PARAM_PAYMENT_SCRIPT] = "/mancgi/testpayment"

    # в тестовом примере валидация проходит успешно, если
    # Идентификатор терминала = rick, пароль терминала = morty
    # TODO
    def PM_Validate(self, xml: ET.ElementTree):
        logger.info("run pmvalidate")

        # мы всегда можем вывести xml в лог, чтобы изучить, что приходит :)
        logger.info(f"xml input: {ET.tostring(xml.getroot(), encoding='unicode')}")

        terminalkey_node = xml.find('./terminalkey')
        terminalpsw_node = xml.find('./terminalpsw')
        terminalkey = terminalkey_node.text if terminalkey_node is not None else ''
        terminalpsw = terminalpsw_node.text if terminalpsw_node is not None else ''

        if terminalkey != 'rick' or terminalpsw != 'morty':
            raise billmgr.exception.XmlException('wrong_terminal_info')

    # в тестовом примере получаем необходимые платежи
    # и переводим их все в статус 'оплачен'
    def CheckPay(self):
        # проверить оплаченные платежи
        # реализация --command checkpay
        # здесь делаем запрос в БД, получаем список платежей в статусе "оплачивается"
        # идем в платежку и проверяем прошли ли платежи
        # если платеж оплачен, выставляем соответствующий статус c помощью функции set_paid

        # получаем список платежей в статусе оплачивается
        # и которые используют обработчик pmtestpayment
        # TODO: pmtestpayment поменять
        #
        query: str = f"""
            SELECT pt.id, pt.externalid FROM payment AS pt
            JOIN paymethod AS pmd
            ON pt.paymethod = pmd.id
            WHERE module = '{'pmtestpayment'}' AND pt.status = {PaymentStatus.INPAY.value}
        """
        # testovy
        query = f"""
            SELECT pt.id, pt.externalid FROM payment AS pt
            JOIN paymethod AS pmd ON pt.paymethod = pmd.id
            WHERE module = '{'pmtestpayment'}' AND pt.status = {4}
            ORDER BY pt.id DESC LIMIT 3;
        """
        db_in_pay_payments: t.List[t.Dict[str, t.Union[str, int]]] \
            = db.db_query(query)

        for pt in db_in_pay_payments:
            logger.info("Payment in pay = " + str(pt))

            payment_info_xml = MgrctlXml("payment.info", elid=pt.get("id"), lang="ru")
            terminalkey = payment_info_xml.find("./payment/paymethod/terminalkey").text
            terminalpsw = payment_info_xml.find("./payment/paymethod/terminalpsw").text

            request_body: dict[t.Union[str, int]] = {
                # "TerminalKey": "TinkoffBankTest",
                "TerminalKey": terminalkey,
                "PaymentId": pt.get("externalid"),
            }
            request_body.update({"Token": generate_token(
                request_body=request_body, password=terminalpsw)})
            logger.info(f"request_body = {request_body}")

            kassa_url: str = "https://securepay.tinkoff.ru/v2/GetState"
            kassa_response: dict[t.Union[str, int]] = requests\
                .post(url=kassa_url, json=request_body)\
                .json()
            logger.info("kassa_response = " + str(kassa_response))

            if not kassa_response.get("Success"):
                raise Exception("Ошибка получения статуса платежа")

            # TODO: убрать тестовые данные
            # if kassa_response.get("TerminalKey") == "TinkoffBankTest":
            #     payment.set_fraud(payment_id=pt.get("id"),
            #                       info="Платёж выполнен через тестовые данные.",
            #                       externalid=pt.get("externalid"))
            if kassa_response.get("Status") in ["NEW", "CONFIRMED"]:
                payment.set_paid(payment_id=pt.get("id"),
                                 info="",
                                 externalid=pt.get("externalid"))
            elif kassa_response.get("Status") == "CANCELED":
                payment.set_canceled(payment_id=pt.get("id"),
                                     info="",
                                     externalid=pt.get("externalid"))

            logger.info(f'Status for payment({pt.get("id")}) = {kassa_response.get("Status")}.')


TestPaymentModule().Process()
