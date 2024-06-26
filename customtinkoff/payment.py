from abc import ABC, abstractmethod
from enum import Enum
from http.cookies import SimpleCookie
import typing as t

from billmgr import db
from billmgr.exception import XmlException
from billmgr.misc import MgrctlXml
from customtinkoff import logger


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

    def __init__(self, elid: str, cookies: str = "", http_host: str = "",
                 request_method: str = "", https: str = "") -> None:
        logger.info("run Payment.__init__")

        self.elid = elid
        "ID платежа."
        self.cookies: t.Dict[str, str] = self._parse_cookies(cookies)
        self.request_method: str = request_method
        self.https: str = https
        self.auth = self.cookies.get("billmgrses5")
        "Токен авторизации."

        self.mgrurl = "https://" + http_host + "/billmgr"
        "URL биллинга."
        self.pending_page = f'{self.mgrurl}?func=payment.pending'
        "URL страницы биллинга с информацией об ожидании зачисления платежа."
        self.fail_page = f'{self.mgrurl}?func=payment.fail'
        "URL страницы биллинга с информацией о неуспешной оплате."
        self.success_page = f'{self.mgrurl}?func=payment.success'
        "URL страницы биллинга с информацией об успешной оплате."

        self.payment_params = {}
        "Параметры платежа."
        self.paymethod_params = {}
        "Параметры метода оплаты."
        self.user_params = {}
        "Параметры пользователя."

        self.lang = self.cookies["billmgrlang5"].split(':')[1]
        "Язык, используемый у клиента."

        if request_method and https:
            self.validate()

        # получить параметры платежа и метода оплаты
        # см. https://docs.ispsystem.ru/bc/razrabotchiku/sozdanie-modulej/sozdanie-modulej-plateyonyh-sistem#id-Созданиемодулейплатежныхсистем-CGIскриптымодуля

        payment_info_xml = MgrctlXml("payment.info", elid=self.elid, lang=self.lang)
        for elem in payment_info_xml.findall("./payment/"):
            self.payment_params[elem.tag] = elem.text
        for elem in payment_info_xml.findall("./payment/paymethod/"):
            self.paymethod_params[elem.tag] = elem.text

        # получаем параметры пользователя
        # получаем с помощью функции whoami информацию об авторизованном пользователе
        # в качестве параметра передаем auth - токен сессии
        user_node = MgrctlXml("whoami", auth=self.auth).find('./user')
        if user_node is None:
            raise XmlException("invalid_whoami_result")
        # получаем из бд данные о пользователях
        user_query = db.get_first_record(
            f"""SELECT u.*, IFNULL(c.iso2, 'EN') AS country, a.registration_date
            FROM user u
            LEFT JOIN account a ON a.id=u.account
            LEFT JOIN country c ON c.id=a.country
            WHERE u.id = '{user_node.attrib['id']}' """
        )
        if user_query:
            self.user_params["user_id"] = user_query["id"]
            self.user_params["phone"] = user_query["phone"]
            self.user_params["email"] = user_query["email"]
            self.user_params["realname"] = user_query["realname"]
            self.user_params["language"] = user_query["language"]
            self.user_params["country"] = user_query["country"]
            self.user_params["account_id"] = user_query["account"]
            self.user_params["account_registration_date"] = user_query["registration_date"]

    @staticmethod
    def _parse_cookies(rawdata) -> t.Dict[str, str]:
        cookie = SimpleCookie()
        cookie.load(rawdata)
        return {k: v.value for k, v in cookie.items()}

    @abstractmethod
    def get_redirect_request(self, url: str) -> str:
        "Основной метод работы CGI, возвращающий HTTP запрос для перехода в платёжную систему для оплаты."
        pass

    def validate(self) -> None:
        # пока поддерживаем только http метод GET
        if self.request_method != 'GET':
            raise NotImplementedError

        # по-умолчанию используется https
        if self.https != 'on':
            raise NotImplementedError

    # перевести платеж в статус "оплачивается"

    def set_in_pay(self, payment_id: str, info: str, externalid: str):
        '''
        payment_id - id платежа в BILLmanager
        info       - доп. информация о платеже от платежной системы
        externalid - внешний id на стороне платежной системы
        '''
        MgrctlXml('payment.setinpay', elid=payment_id, info=info, externalid=externalid)

    # перевести платеж в статус "мошеннический"
    def set_fraud(self, payment_id: str, info: str, externalid: str):
        MgrctlXml('payment.setfraud', elid=payment_id, info=info, externalid=externalid)

    # перевести платеж в статус "оплачен"
    def set_paid(self, payment_id: str, info: str, externalid: str):
        MgrctlXml('payment.setpaid', elid=payment_id, info=info, externalid=externalid)

    # перевести платеж в статус "отменен"
    def set_canceled(self, payment_id: str, info: str, externalid: str):
        MgrctlXml('payment.setcanceled', elid=payment_id, info=info, externalid=externalid)
