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
        "Инициализация платежа. Метод инициирует платежную сессию."

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
