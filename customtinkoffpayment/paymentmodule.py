from abc import ABC, abstractmethod
import sys
import typing as t
import xml.etree.ElementTree as ET
from enum import Enum

from billmgr.exception import XmlException


class PaymentModule(ABC):
    # Абстрактные методы CheckPay и PM_Validate необходимо переопределить в своей реализации
    # см пример реализации в pmtestpayment.py

    # проверить оплаченные платежи
    # реализация --command checkpay
    # здесь делаем запрос в БД, получаем список платежей в статусе "оплачивается"
    # идем в платежку и проверяем прошли ли платежи
    # если платеж оплачен, выставляем соответствующий статус c помощью функции set_paid

    class Feature(Enum):
        """
        Фичи платежного модуля.\n
        Полный список можно посмотреть в документации:
        https://docs.ispsystem.ru/bc/razrabotchiku/sozdanie-modulej/sozdanie-modulej-plateyonyh-sistem#id-Созданиемодулейплатежныхсистем-Основнойскриптмодуля
        """
        REDIRECT = "redirect"
        "Нужен ли переход в платёжку для оплаты."
        CHECK_PAY = "checkpay"
        "Проверка статуса платежа по крону."
        NO_NEED_PROFILE = "notneedprofile"
        "Оплата без плательщика (позволит зачислить платеж без создания плательщика)."
        PM_VALIDATE = "pmvalidate"
        "Проверка введённых данных на форме создания платежной системы."
        PM_USER_CREATE = "pmusercreate"
        "Для ссылки на регистрацию в платежке."

    class Param(Enum):
        """
        Параметры платежного модуля.\n
        Полный список можно посмотреть в документации:
        https://docs.ispsystem.ru/bc/razrabotchiku/sozdanie-modulej/sozdanie-modulej-plateyonyh-sistem#id-Созданиемодулейплатежныхсистем-Основнойскриптмодуля
        """
        PAYMENT_SCRIPT = "payment_script"
        "Путь к скрипту переадресации на оплату:\n\n`/mancgi/<наименование cgi скрипта>`."
        RECURRING_SCRIPT = "recurring_script"
        "Путь к скрипту на подтверждение активации рекуррентных платежей:\n\n`/mancgi/<наименование cgi скрипта>`."

    @abstractmethod
    def check_pay(self):
        """
        Проверить оплаченные платежи.
        Реализация `--command checkpay`.
        """
        pass

    @abstractmethod
    def pm_validate(self, xml):
        """
        Вызывается для проверки введенных в настройках метода оплаты значений.
        Реализация `--command pmvalidate`.
        """
        pass

    def __init__(self):
        self.features = {}
        self.params = {}

    def config(self):
        """
        Возращает xml с кофигурацией метода оплаты.\n
        Реализация `--command config`.
        """
        config_xml = ET.Element('doc')
        feature_node = ET.SubElement(config_xml, 'feature')
        for key, val in self.features.items():
            ET.SubElement(feature_node, key).text = "on" if val else "off"

        param_node = ET.SubElement(config_xml, 'param')
        for key, val in self.params.items():
            ET.SubElement(param_node, key).text = val

        return config_xml

    def process(self):
        """
        Лайтовый парсинг аргументов командной строки.\n
        Ожидаем `--command <наименование команды>`.
        """
        try:
            if len(sys.argv) < 3:
                raise XmlException("invalid_arguments")

            if sys.argv[1] != "--command":
                raise Exception("invalid_arguments")

            command = sys.argv[2]

            if command == "config":
                xml = self.config()
                if xml is not None:
                    ET.dump(xml)
            elif command == self.Feature.PM_VALIDATE:
                self.pm_validate(ET.parse(sys.stdin))
            elif command == self.Feature.CHECK_PAY:
                self.check_pay()

        except XmlException as exception:
            sys.stdout.write(exception.as_xml())
