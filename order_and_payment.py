from abc import ABC, abstractmethod
from datetime import datetime, date, time, timedelta
from new_main import ProductAmount, TrainingBooking, LockerBooking, Locker, Member
# from new_main import *
from enum import Enum

class MembershipPlan(Enum):
    # Tuple format: (price, booking_discount, product_discount, locker_discount)
    MONTHLY = (1500, 0.0, 0.0, 0.0)
    ANNUAL = (15000, 0.2, 0.1, 0.15)
    STUDENT = (1200, 0.15, 0.0, 0.10)

    def __init__(self, price, booking_discount, product_discount, locker_discount):
        self.price = price
        self.booking_discount = booking_discount
        self.product_discount = product_discount
        self.locker_discount = locker_discount

class TrainerTier(Enum):
    # Tuple format: (private_price, class_price)
    JUNIOR = (800, 200)
    SENIOR = (1500, 375)
    MASTER = (2500, 625)

    def __init__(self, private_price, class_price):
        self.private_price = private_price
        self.class_price = class_price

class LockerType(Enum):
    NORMAL = 35
    VIP = 70

class OrderItem:
    def __init__(self, item, type="Auto"):
        if type == "Auto":
            if isinstance(item, ProductAmount):
                type = "ProductAmount"
            elif isinstance(item, TrainingBooking):
                type = "TrainingBooking"
            elif isinstance(item, LockerBooking):
                type = "LockerBooking"
            elif isinstance(item, date):
                type = "DaypassDate"
            elif item in ["Monthly", "Annual", "Student"]:
                type = "NewMembershipType"
        elif type not in ["ProductAmount", "TrainingBooking", "LockerBooking", "DaypassDate", "NewMembershipType"]:
            raise Exception("type is not 'ProductAmount'|'TrainingBooking'|'LockerBooking'|'DaypassDate'|'NewMembershipType'")
        self.__type = type
        self.__item = item
        self.__price_paid = None

    @property
    def price_paid(self):
        return self.__price_paid

    def price(self, user):
        if self.__type == "DaypassDate":
            return 500
        elif self.__type == "NewMembershipType":
            return MembershipPlan[self.__item.upper()].price
        elif self.__type == "ProductAmount":
            if isinstance(user, Member):
                return self.__item.price(user)
            else:
                return self.__item.price()
        else:
            return self.__item.price

    def set_price_paid(self, user):
        self.__price_paid = self.price(user)

class AbstractOrder:
    __next_id = 1

    def __init__(self, user = None):
        self.__order_id = AbstractOrder.__next_id
        AbstractOrder.__next_id += 1
        self.__user = user
        self.__payment = None
        self.__order_item_list = []
        self.__status = "Pending"

    @property
    def payment(self):
        return self.__payment

    @property
    def total_price(self):
        total = 0
        for order_item in self.__order_item_list:
            total += order_item.price(self.__user)
        return total
    
    def set_payment(self, payment):
        if not isinstance(CashPayment|CreditCardPayment|QRPayment):
            raise Exception("Not a valid payment type")
        self.__payment = payment 
    
    @abstractmethod
    def process(self):
        pass

    @abstractmethod
    def verify_and_update_all_info(self):
        pass

    @abstractmethod
    def create_order_item(self):
        pass

class Order(AbstractOrder):
    def process(self):
        self.payment.set_amount(self.total_price)
        self.payment.process()
    
    def verify_and_update_all_info(self):
        return
    
    def create_order_item(self, item, type="auto"):
        self.__order_item_list.append(OrderItem(item, type))

class OrderRefund(AbstractOrder):
    def process(self):
        self.payment.refund()
    
    def verify_and_update_all_info(self):
        return
    
    def create_order_item(self, item, type="auto"):
        self.__order_item_list.append(OrderItem(item, type))

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

    def create_qr(amount):
        return QRCode(f"GateWayBank-{PaymentGateway.__next_id}")
    
    def validate_qr_payment(transaction_id):
        return True

    def pay_card(card_num, cvv, expiry, amount):
        return f"GateWayBank-{PaymentGateway.__next_id}"
    
    def refund(transaction_id, amount):
        return True

class Payment(ABC):
    __next_id = 1

    def __init__(self):
        self.__transaction_id = Payment.__next_id
        Payment.__next_id += 1
        self.__payment_gateway_transaction_id = None
        self.__timestamp_payed = None
        self.__amount = None
        self.__status = "NoAmountSet"

    @property
    def payment_gateway_transaction_id(self):
        return self.__payment_gateway_transaction_id

    @property
    def amount(self):
        return self.__amount

    @property
    def status(self):
        return self.__status
    
    def set_payment_gateway_transaction_id(self, id):
        self.__payment_gateway_transaction_id = id

    def set_status(self, status):
        self.__status = status

    def set_amount(self, amount):
        self.__amount = amount
        self.__status = "Pending"

    @abstractmethod
    def process(self):
        pass

    @abstractmethod
    def validate(self):
        pass

    @abstractmethod
    def refund(self):
        pass

class CashPayment(Payment):
    def process(self):
        self.set_status("Paid")

    def validate(self):
        if self.status == "Paid":
            return True
        return False

    def refund(self):
        pass

class CreditCardPayment(Payment):
    def __init__(self, card_num, cvv, expiry):
        super().__init__()
        self.__card_num = card_num
        self.__cvv = cvv
        self.__expiry = expiry
        
    def process(self):
        result = PaymentGateway.pay_card(self.__card_num, self.__cvv, self.__expiry, self.amount)
        if result:
            self.set_status("Paid")
            self.set_payment_gateway_transaction_id(result)
        else:
            raise Exception("Error")

    def validate(self):
        if self.status == "Paid":
            return True
        return False

    def refund(self):
        pass

class QRPayment(Payment):
    def __init__(self):
        super().__init__()
        self.__qr_string = ""

    def process(self):
        result = PaymentGateway.create_qr(self.amount)
        if isinstance(result, QRCode):
            self.__qr_string = result.qr_string
            self.set_payment_gateway_transaction_id(result.transaction_id)
        else:
            raise Exception("Error")

    def validate(self):
        result = PaymentGateway.validate_qr_payment(self.payment_gateway_transaction_id)
        if result:
            self.set_status("Paid")
        else:
            raise Exception("Error")

    def refund(self):
        pass