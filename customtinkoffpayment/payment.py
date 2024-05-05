from abc import ABC, abstractmethod
from enum import Enum

from billmgr.misc import MgrctlXml


class Payment(ABC):

    class Status(Enum):
        """
        Статусы платежей в виде, в котором они хранятся в БД.\n
        см. https://docs.ispsystem.ru/bc/razrabotchiku/struktura-bazy-dannyh#id-Структурабазыданных-payment
        """
        NEW = 1
        IN_PAY = 2
        PAID = 4
        FRAUD = 7
        CANCELED = 9

    def __init__(self) -> None:
        pass

    # перевести платеж в статус "оплачивается"
    def set_in_pay(payment_id: str, info: str, externalid: str):
        '''
        payment_id - id платежа в BILLmanager
        info       - доп. информация о платеже от платежной системы
        externalid - внешний id на стороне платежной системы
        '''
        MgrctlXml('payment.setinpay', elid=payment_id, info=info, externalid=externalid)

    # перевести платеж в статус "мошеннический"
    def set_fraud(payment_id: str, info: str, externalid: str):
        MgrctlXml('payment.setfraud', elid=payment_id, info=info, externalid=externalid)

    # перевести платеж в статус "оплачен"
    def set_paid(payment_id: str, info: str, externalid: str):
        MgrctlXml('payment.setpaid', elid=payment_id, info=info, externalid=externalid)

    # перевести платеж в статус "отменен"
    def set_canceled(payment_id: str, info: str, externalid: str):
        MgrctlXml('payment.setcanceled', elid=payment_id, info=info, externalid=externalid)
