import typing as t
from hashlib import sha256


class TinkoffKassa:
    """
    Тинькофф Касса - сервис, помогающий проводить выплату клиенту-физлицу.
    """

    def __init__(self) -> None:
        pass

    def generate_token(request_body: t.Dict[str, t.Union[str, int]],
                       password: str) -> str:
        """
        Формирование токена для запросов по API Тинькофф согласно инструкции:
        https://www.tinkoff.ru/kassa/dev/payments/#section/Podpis-zaprosa
        """
        # нужна копия словаря, так как он далее преобразуется
        request: t.Dict[str, t.Union[str, int]] = dict(request_body)
        request.update({"Password": password})
        request_sorted_by_key: t.Dict[str, t.Union[str, int]] = dict(
            sorted(request.items(), key=lambda item: str(item[0])))
        concatenated_values: str = "".join(request_sorted_by_key.values())
        token: str = sha256(concatenated_values.encode("utf-8")).hexdigest()

        return token
