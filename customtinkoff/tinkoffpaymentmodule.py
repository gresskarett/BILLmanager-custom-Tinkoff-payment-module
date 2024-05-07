from xml.etree import ElementTree as ET
import typing as t

from billmgr import db
from billmgr import logger as logging
from billmgr.exception import XmlException
from billmgr.misc import MgrctlXml
from customtinkoff import MODULE_NAME
from customtinkoff.payment import Payment
from customtinkoff.paymentmodule import PaymentModule
from customtinkoff.tinkoffkassa import TinkoffKassa


logging.init_logging(MODULE_NAME)
logger = logging.get_logger(MODULE_NAME)


class TinkoffPaymentModule(PaymentModule):

    def __init__(self) -> None:
        super().__init__()

        self.features[self.Feature.CHECK_PAY.value] = True
        self.features[self.Feature.REDIRECT.value] = True
        self.features[self.Feature.NO_NEED_PROFILE.value] = True
        self.features[self.Feature.PM_VALIDATE.value] = True

        self.params[self.Param.PAYMENT_SCRIPT.value] = "/mancgi/customtinkoffpayment"

    # в тестовом примере валидация проходит успешно, если
    # Идентификатор терминала = rick, пароль терминала = morty
    #
    # принимается xml с веденными на форме значениями
    # если есть некорректные значения, то бросаем исключение billmgr.exception.XmlException
    # если все значение валидны, то ничего не возвращаем, исключений не бросаем
    # TODO
    def pm_validate(self, xml: ET.ElementTree):
        logger.info("run pm_validate")

        # мы всегда можем вывести xml в лог, чтобы изучить, что приходит :)
        logger.info(f"xml input: {ET.tostring(xml.getroot(), encoding='unicode')}")

        terminalkey_node = xml.find('./terminalkey')
        terminalpsw_node = xml.find('./terminalpsw')
        terminalkey = terminalkey_node.text if terminalkey_node is not None else ''
        terminalpsw = terminalpsw_node.text if terminalpsw_node is not None else ''

        if terminalkey not in ['rick', "TinkoffBankTest"] or terminalpsw not in ['morty', "TinkoffBankTest"]:
            raise XmlException('wrong_terminal_info')

    # в тестовом примере получаем необходимые платежи
    # и переводим их все в статус 'оплачен'
    def check_pay(self):
        # здесь делаем запрос в БД, получаем список платежей в статусе "оплачивается"
        # идем в платежку и проверяем прошли ли платежи
        # если платеж оплачен, выставляем соответствующий статус c помощью функции set_paid

        logger.info("run check_pay")

        # получаем список платежей в статусе оплачивается
        # и которые используют обработчик pmtestpayment
        #
        query: str = f"""
            SELECT pt.id, pt.externalid FROM payment AS pt
            JOIN paymethod AS pmd
            ON pt.paymethod = pmd.id
            WHERE pmd.module = '{"pm" + MODULE_NAME}' AND pt.status = {Payment.Status.IN_PAY.value}
        """
        # testovy
        # query = f"""
        #     SELECT pt.id, pt.externalid FROM payment AS pt
        #     JOIN paymethod AS pmd ON pt.paymethod = pmd.id
        #     WHERE module = '{'pmtestpayment'}' AND pt.status = {4}
        #     ORDER BY pt.id DESC LIMIT 3;
        # """
        db_in_pay_payments: t.List[t.Dict[str, t.Union[str, int]]]\
            = db.db_query(query)

        for pt in db_in_pay_payments:
            logger.info("Payment in pay = " + str(pt))

            payment_info_xml = MgrctlXml("payment.info", elid=pt.get("id"), lang="ru")
            logger.info(f"payment_info_xml = {ET.tostring(payment_info_xml, encoding='unicode')}")
            kassa: TinkoffKassa = TinkoffKassa(
                terminalkey=payment_info_xml.find("./payment/paymethod/terminalkey").text,
                terminalpsw=payment_info_xml.find("./payment/paymethod/terminalpsw").text
            )
            kassa_response = kassa.get_state(payment_id=pt.get("externalid"))
            logger.info("kassa_response = " + str(kassa_response))

            if not kassa_response.get("Success"):
                raise Exception("Ошибка получения статуса платежа")

            response_info: str = "{0} {1}".format(
                kassa_response.get("Message"),
                kassa_response.get("Details")
            ).strip()

            # TODO: убрать тестовые данные
            if kassa_response.get("TerminalKey") == "TinkoffBankTest":
                MgrctlXml('payment.setfraud', elid=pt.get("id"), info=response_info, externalid=pt.get("externalid"))
                # payment.set_fraud(payment_id=pt.get("id"),
                #                   info="Платёж выполнен через тестовые данные.",
                #                   externalid=pt.get("externalid"))
            if kassa_response.get("Status") in ["NEW", "CONFIRMED"]:
                MgrctlXml('payment.setpaid', elid=pt.get("id"), info="", externalid=pt.get("externalid"))
                # Payment.set_paid(payment_id=pt.get("id"),
                #                  info="",
                #                  externalid=pt.get("externalid"))
            elif kassa_response.get("Status") == "CANCELED":
                MgrctlXml('payment.setcanceled', elid=pt.get("id"), info=response_info, externalid=pt.get("externalid"))
                # Payment.set_canceled(payment_id=pt.get("id"),
                #                      info="",
                #                      externalid=pt.get("externalid"))

            logger.info(f'Status for payment({pt.get("id")}) = {kassa_response.get("Status")}.')
