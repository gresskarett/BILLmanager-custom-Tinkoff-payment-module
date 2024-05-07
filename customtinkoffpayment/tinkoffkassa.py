import typing as t
from hashlib import sha256

import requests


class TinkoffKassa:
    """
    Тинькофф Касса - сервис, помогающий проводить выплату клиенту-физлицу.\n
    см. https://www.tinkoff.ru/kassa/dev/payments/
    """

    def __init__(self, terminalkey: str, terminalpsw: str) -> None:
        self.terminalkey: str = terminalkey
        self.terminalpsw: str = terminalpsw

    def generate_token(self, request_body: t.Dict[str, t.Union[str, int]]
                       ) -> str:
        """
        Формирование токена для запросов по API Тинькофф согласно инструкции:
        https://www.tinkoff.ru/kassa/dev/payments/#section/Podpis-zaprosa
        """
        # нужна копия словаря, так как он далее преобразуется
        request: t.Dict[str, t.Union[str, int]] = dict(request_body)
        request.update({"Password": self.terminalpsw})
        request_sorted_by_key: t.Dict[str, t.Union[str, int]] = dict(
            sorted(request.items(), key=lambda item: str(item[0])))
        concatenated_values: str = "".join(request_sorted_by_key.values())
        token: str = sha256(concatenated_values.encode("utf-8")).hexdigest()

        return token

    def init_payment(self, amount: int, order_id: str,
                     customer_key: str = "", recurrent: str = "",
                     language: str = "", notification_url: str = "",
                     success_url: str = "", fail_url: str = ""
                     ) -> t.Dict[t.Union[str, int]]:
        "Метод инициирует платежную сессию."

        url: str = "https://securepay.tinkoff.ru/v2/Init"

        request_body: t.Dict[t.Union[str, int]] = {
            "TerminalKey": self.terminalkey,
            "Amount": amount,
            "OrderId": order_id,
            "SuccessURL": success_url,
            "FailURL": fail_url
        }
        request_body.update({"Token": self.generate_token(request_body)})

        response: t.Dict[t.Union[str, int]] = requests\
            .post(url=url, json=request_body)\
            .json()

        return response

    def get_state(self, payment_id: str) -> t.Dict[t.Union[str, int]]:
        "Метод возвращает статус платежа."

        url: str = "https://securepay.tinkoff.ru/v2/GetState"

        request_body: dict[t.Union[str, int]] = {
            "TerminalKey": self.terminalkey,
            # "PaymentId": pt.get("externalid"),
            "PaymentId": payment_id
        }
        request_body.update({"Token": self.generate_token(
            request_body=request_body, password=self.terminalpsw)})

        response: dict[t.Union[str, int]] = requests\
            .post(url=url, json=request_body)\
            .json()

        return response

    def cancel(self, payment_id: str) -> t.Dict[t.Union[str, int]]:
        """
        Отменяет платежную сессию. В зависимости от статуса платежа переводит его в следующие состояния:\n
        NEW - CANCELED\n
        AUTHORIZED - PARTIAL_REVERSED – если отмена не на полную сумму\n
        AUTHORIZED - REVERSED - если отмена на полную сумму\n
        CONFIRMED - PARTIAL_REFUNDED – если отмена не на полную сумму\n
        CONFIRMED - REFUNDED – если отмена на полную сумму.\n
        Если платеж находился в статусе AUTHORIZED производится отмена холдирования средств на карте клиента. \n
        При переходе из статуса CONFIRMED – возврат денежных средств на карту клиента.\n
        """

        url: str = "https://securepay.tinkoff.ru/v2/Cancel"

        request_body: dict[t.Union[str, int]] = {
            "TerminalKey": self.terminalkey,
            "PaymentId": payment_id
        }
        request_body.update({"Token": self.generate_token(
            request_body=request_body, password=self.terminalpsw)})

        response: dict[t.Union[str, int]] = requests\
            .post(url=url, json=request_body)\
            .json()

        return response
