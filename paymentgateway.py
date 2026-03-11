class QRCode:
    def __init__(self, transaction_id):
        self.__qr_string = "Dummy QR Image String"
        self.__transaction_id = transaction_id

    @property
    def qr_string(self):
        return self.__qr_string
    
    @property
    def transaction_id(self):
        return self.__transaction_id

class PaymentGateway:
    __next_id = 1

    def __init__(self):
        pass

    def create_qr(self, amount):
        return QRCode(f"GateWayBank-{PaymentGateway.__next_id}")
    
    def validate_qr_payment(self, transaction_id):
        return True

    def pay_card(self, card_num, cvv, expiry, amount):
        return f"GateWayBank-{PaymentGateway.__next_id}"
    
    def refund(self, transaction_id, amount):
        return True
    
payment_gateway = PaymentGateway()