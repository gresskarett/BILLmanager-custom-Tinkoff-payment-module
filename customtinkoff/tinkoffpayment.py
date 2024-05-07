import typing as t

from customtinkoff import MODULE_NAME, logger
from customtinkoff.payment import Payment
from customtinkoff.tinkoffkassa import TinkoffKassa


class TinkoffPayment(Payment):

    def __init__(self, elid: str, cookies: str = "", http_host: str = "",
                 request_method: str = "", https: str = "") -> None:
        super().__init__(elid, cookies, http_host, request_method, https)

        self.int_amount = self.payment_params.get("paymethodamount")\
                              .replace(".", "")
        self.order_id = "billmgr#{0}#{1}".format(
            self.elid, self.payment_params.get("randomnumber"))
        self.success_page + "&elid=" + self.elid + "&module=" + MODULE_NAME
        self.fail_page + "&elid=" + self.elid+"&module=" + MODULE_NAME

        self.kassa: TinkoffKassa = TinkoffKassa(
            terminalkey=self.paymethod_params.get("terminalkey"),
            terminalpsw=self.paymethod_params.get("terminalpsw")
        )

    def make(self) -> str:
        """
        Метод инициализирует платёж и устанавливает статус платежа.\n
        Возвращает URL для дальнейшего перехода в Тинькофф Кассу.
        """

        logger.info("run TinkoffPayment.make")

        response: t.Dict[str, t.Union[str, int]] = self.kassa.init_payment(
            amount=self.int_amount,
            order_id=self.order_id,
            success_url=self.success_page,
            fail_url=self.fail_page
        )
        response_info: str = "{0} {1}".format(response.get("Message"),
                                              response.get("Details")).strip()

        if not response.get("Success"):
            self.set_canceled(payment_id=self.elid,
                              info=response_info,
                              externalid=response.get("PaymentId"))
            raise Exception("Ошибка инициализации платежа. " + response_info)

        self.set_in_pay(payment_id=self.elid,
                        info=response_info,
                        externalid=response.get("PaymentId"))

        payment_url: str = response.get("PaymentURL")
        return payment_url

    # ex Process()
    def get_redirect_request(self, url: str) -> str:
        """
        Метод возвращает полный HTTP запрос с переадресацией в Тинькофф кассу.
        """

        logger.info("run TinkoffPayment.get_redirect_request")
        logger.info(f"paymethod_params = {self.paymethod_params}")
        logger.info(f"payment_params = {self.payment_params}")

        # TODO: загрузить http из templates, заменить "{{ redirect_url }}" и записать в переменную
        return '<html>\n<head>\n<meta http-equiv="refresh" content="0; URL={0}">\n</head>\n<body></body>\n</html>'\
            .format(url)
