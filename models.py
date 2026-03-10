from abc import ABC, abstractmethod
from datetime import datetime, date, time, timedelta
from enum import Enum
from os import name
import textwrap

class OrderItem(ABC):
    def __init__(self, payment_status = "Pending"):
        self.__price_paid = None
        self.__payment_status = payment_status

    @property
    def price_paid(self):
        return self.__price_paid

    @abstractmethod
    def calculate_price(self, user = None):
        pass

    def set_price_paid(self, amount):
        self.__price_paid = amount
        self.__payment_status = "Paid"

class DayPass(OrderItem):
    def __init__(self, payment_status="Pending"):
        super().__init__(payment_status)
        self.__date = date.today()
    
    def calculate_price(self, user = None):
        return 500
    
class NewMembership(OrderItem):
    def __init__(self, membership, payment_status="Pending"):
        super().__init__(payment_status)
        self.__membership = membership

    @property
    def membership(self):
        return self.__membership

    def calculate_price(self, user = None):
        return MembershipPlan[self.__membership.upper()].price

class Booking(OrderItem):
    def __init__(self, status = "Pending"):
        super().__init__()
        self.__status = status # statuses: Waitlist Confirmed Check-in Completed Cancelled

    @property
    def status(self):
        return self.__status

    def confirm(self):
        self.__status = "Confirmed"

    def cancel(self):
        self.__status = "Cancelled"

    def check_in(self):
        self.__status = "Check-in"

    def late_check_in(self):
        self.__status = "Late Check-in"

class TrainingBooking(Booking):

    def __init__(self, member, session, status="Pending"):
        super().__init__(status)
        self.__member = member
        self.__session = session
        self.__training_log = ""
        self.__locker_booking = None

    @property
    def member(self):
        return self.__member
    
    @property
    def session(self):
        return self.__session
    
    @property
    def locker_booking(self):
        return self.__locker_booking

    @property
    def info(self):
        if self.status == "Pending":
            status_text = "Pending. Please Pay to Confirm Booking"
        else:
            status_text = self.status
        return {
            "session id" : self.__session.session_id,
            "Class date": self.__session.date,
            "Status": status_text
        }
    
    @property
    def notification(self):
        if self.__session.status == "Cancelled":
            return f"[session id: {self.__session.session_id}] Has been cancelled"
        elif self.__status == "Pending":
            return "Pending. Please Pay to Confirm Booking"
        else:
            return ""
        
    def calculate_price(self, user = None):
        membership_type = self.__member.current_membership
        membership_enum = MembershipPlan[membership_type.upper()]
        trainer_tier = self.__session.trainer.tier
        tier_enum = TrainerTier[trainer_tier.upper()]
        session_type = self.__session.get_session_type()

        price = tier_enum.class_price if session_type == "Class" else tier_enum.private_price
        discount = membership_enum.booking_discount
        discount_price = round(price * (1 - discount), 2)
        return discount_price

    def __str__(self):
        if self.__status == "Pending":
            status_text = "Pending. Please Pay to Confirm Booking"
        else:
            status_text = self.__status
        text = f"session id: {self.__session.session_id} Citizen id: {self.__member.citizen_id} Class date: {self.__session.date} Status: {status_text}"
        return text

class Session:

    def __init__(self, start, end, date, max_participants, room, trainer, gym_class = None):
        if gym_class:
            session_len = len(gym_class.session_list)
            self.__session_id = f"{gym_class.class_id}-{session_len+1:03d}"
        else:
            session_len = len(trainer.session_list)
            self.__session_id = f"{trainer.staff_id}-{session_len+1:03d}"
        self.__start = start
        self.__end = end
        self.__date = date
        self.__max_participants = max_participants
        self.__room = room
        self.__trainer = trainer
        self.__gym_class = gym_class
        self.__status = "Normal" # normal, cancelled, startlate?
        self.__training_plan = ""
        self.__training_log = ""
        self.__training_booking_list = []

    @property
    def start(self):
        return datetime.combine(self.__date, self.__start)
    
    @property
    def end(self):
        return datetime.combine(self.__date, self.__end)

    @property
    def session_id(self):
        return self.__session_id
    
    @property
    def date(self):
        return self.__date
    
    @property
    def room(self):
        return self.__room
    
    @property
    def trainer(self):
        return self.__trainer
    
    @property
    def status(self):
        return self.__status
    
    @property
    def info(self):
        return {
            "session id": self.session_id,
            "datetime": f"Start: {self.__start} End: {self.__end} Date: {self.__date}",
            "enrolled": self.get_enrolled_num(),
            "max participants": self.__max_participants
        }
    
    def set_training_plan(self, text):
        self.__training_plan = text

    def get_enrolled_num(self):
        participants = 0
        for training_booking in self.__training_booking_list:
            if training_booking.status == "Confirmed":
                participants += 1
        return participants
    
    def get_session_type(self):
        return "Class" if self.__gym_class else "Private"

    def enroll_member(self, member):
        participants = self.get_enrolled_num()
        if participants >= self.__max_participants:
            raise Exception("Session is full. Please wait until someone cancels.")
        
        booking = TrainingBooking(member, self)
        self.__training_booking_list.append(booking)
        member.add_booking(booking)
        return booking
    
    def is_available(self, new_start, new_end, new_date):
        if self.__date != new_date:
            return True
        
        return self.end <= new_start or self.start >= new_end
    
    def __str__(self):
        text = f"[{self.__session_id}]\n"
        text += f"Start: {self.__start} End: {self.__end} Date: {self.__date}\n"
        text += f"With: {self.__trainer.name} At: {self.__room.name} [{self.__room.room_id}]\n"
        if self.__training_plan:
            text += f"Training plan: {self.__training_plan}\n"
        text += f"Enrolled: {self.get_enrolled_num()} Max: {self.__max_participants}"
        return text

class GymClass:
    __next_id = 1

    def __init__(self, name, detail):
        self.__class_id = f"CL-{GymClass.__next_id}"
        GymClass.__next_id += 1
        self.__name = name
        self.__detail = detail
        self.__session_list = []

    @property
    def class_id(self):
        return self.__class_id
    
    @property
    def info(self):
        sessions = []
        for session in self.session_list:
            sessions.append(session.info)

        return {
            "Class id": self.__class_id,
            "Class name": self.__name,
            "Class detail": self.__detail,
            "Class session": sessions
        }
    
    @property
    def session_list(self):
        return self.__session_list
    
    def create_session(self, start, end, date, max_participants, room, trainer = None, gym_class = None):
        if not room.is_available(start, end, date):
            raise Exception("Session is overlapping another previous session")
        if not trainer and not isinstance(self, Trainer):
            raise Exception("Trainer not provided")
        if not trainer: trainer = self
        if max_participants > room.max_people:
            raise Exception(f"Room can only accommodate {room.max_people} people")
        session = Session(start, end, date, max_participants, room, trainer, gym_class)
        self.__session_list.append(session)
        return session
    
    def create_repeating_session(self, start, end, start_date, days_interval, times, max_participants, room, trainer = None, gym_class = None):
        if not trainer and not isinstance(self, Trainer):
            raise Exception("Trainer not provided")
        if not trainer: trainer = self
        if max_participants > room.max_people:
            raise Exception(f"Room can only accommodate {room.max_people} people")
        for time in range(times):
            date = start_date + timedelta(days=days_interval*time)
            if not room.is_available(start, end, date):
                raise Exception("Session is overlapping another previous session")
            
            session = Session(start, end, date, max_participants, room, trainer, gym_class)
            self.__session_list.append(session)

    def view_session(self):
        pass

    def get_session_by_id(self, session_id):
        for session in self.__session_list:
            if session.session_id == session_id:
                return session
        return False
    
    def __str__(self):
        text = f"Class name: {self.__name}\nClass id: {self.__class_id}\nSession:\n"
        for session in self.session_list:
            session_str = str(session)

            indented_session = textwrap.indent(session_str, '   ')

            text += f" - {indented_session.lstrip()}\n"
        return text

class LockerBooking(Booking):
    def __init__(self, member, locker, start, end, status):
        super().__init__(status)
        self.__member = member
        self.__locker = locker
        self.__start = start
        self.__end = end

    @property
    def member(self):
        return self.__member

    @property
    def locker(self):
        return self.__locker
    
    @property
    def start(self):
        return self.__start
    
    @property
    def end(self):
        return self.__end
    
    @property
    def duration_hours(self):
        duration = self.__end - self.__start
        return duration.total_seconds() / 3600
        # total_seconds = duration.total_seconds()

        # hours = int(total_seconds // 3600)
        # minutes = int((total_seconds % 3600) // 60)

        # if hours == 0:
        #     return 1
        # elif minutes > 15:
        #     return hours + 1
        # else:
        #     return hours

    @property
    def info(self):
        if self.status == "Pending":
            status_text = "Pending. Please Pay to Confirm Booking"
        else:
            status_text = self.status
        return {
            "Date" : self.start.date(),
            "Start time": self.start.time(),
            "End time": self.end.time(),
            "Status": status_text
        }
    
    def calculate_price(self, user = None):
        membership_type = self.__member.current_membership
        membership_enum = MembershipPlan[membership_type.upper()]
        locker_enum = LockerType[self.__locker.type.upper()]
    
        discount = membership_enum.locker_discount
        locker_price = locker_enum.value
        locker_duration = self.duration_hours
        
        total_price = locker_price * locker_duration
        discount_price = round(total_price * (1 - discount), 2)
        return discount_price

    def is_time_conflict(self, start, end): # 7-10 9-12 > 7<12 true, 9<10 true
        return self.__start < end and start < self.__end
    
    def __str__(self):
        if self.status == "Pending":
            status_text = "Pending. Please Pay to Confirm Booking"
        else:
            status_text = self.status
        return f"Lockertype: {self.__locker.type} Date: {self.start.date()} Start Time: {self.start.time()} End Time: {self.end.time()} Status: {status_text}"

class Locker:
    def __init__(self, room, type = "Normal"):
        locker_len = len(room.locker_list)
        self.__locker_id = f"{room.room_id}-{locker_len+1:03d}"
        self.__status = "Available"
        self.__room = room
        self.__type = type
        self.__locker_booking_list = []
    
    @property
    def type(self):
        return self.__type
    
    @property
    def locker_id(self):
        return self.__locker_id
    
    def is_available(self, start, end):
        if self.__status != "Available":
            return False
        
        # check time conflict
        for locker_booking in self.__locker_booking_list:
            if locker_booking.is_time_conflict(start, end):
                return False
        return True
        
    def reserve_locker(self, member, start, end, status):
        if not self.is_available(start, end):
            return False
        
        new_locker_booking = LockerBooking(member, self, start, end, status)

        self.__locker_booking_list.append(new_locker_booking)
        member.add_booking(new_locker_booking)
        
        return new_locker_booking

class Room:
    __next_id = 1

    def __init__(self, gym, name, max_people):
        self.__gym = gym
        self.__room_id = f"R-{Room.__next_id:03d}" # needs to make it id accorrding to type like main M, storage S, locker L, class C, etc.
        Room.__next_id += 1
        self.__name = name
        self.__status = "Operating"
        self.__max_people = max_people
        self.__equipment_list = []
        self.__session_list = []
        self.__locker_list = []

    @property
    def locker_list(self):
        return tuple(self.__locker_list)

    @property
    def room_id(self):
        return self.__room_id
    
    @property
    def name(self):
        return self.__name

    @property
    def max_people(self):
        return self.__max_people
    
    def create_lockers(self, amount_normal, amount_vip):
        for i in range(amount_normal):
            self.__locker_list.append(Locker(self))
        for i in range(amount_vip):
            self.__locker_list.append(Locker(self, "VIP"))

    def is_available(self, start, end, date):
        for session in self.__session_list:
            if not session.is_available(start, end, date):
                return False
        return True
    
    def reserve_locker(self, type, member, start, end, status):
        for locker in self.__locker_list:
            if locker.type != type:
                continue
            new_locker_booking = locker.reserve_locker(member, start, end, status)
            if new_locker_booking: return new_locker_booking
        raise Exception("No lockers available for the specified duration")
    
    # def create_equipments(self, data):
    #     for equipment in data:
    #         self.__equipment_list.append()

class Product:
    def __init__(self, name, amount, price):
        self.__item_id = "todo"
        self.__name = name
        self.__amount = amount
        self.__price = price

    @property
    def name(self):
        return self.__name

    @property
    def price(self):
        return self.__price

    def add_stock(self, amount):
        self.__amount += amount

    def sell_stock(self, amount):
        if self.__amount < amount:
            raise Exception("Not enough stock available")
        self.__amount -= amount

class ProductAmount(OrderItem):
    def __init__(self, item, amount):
        super().__init__()
        self.__item = item
        self.__amount = amount
    
    @property
    def item(self):
        return self.__item
    
    @property
    def amount(self):
        return self.__amount
    
    def calculate_price(self, user = None):
        price = self.__item.price * self.__amount
        if isinstance(user, Member):
            membership_type = user.current_membership
            discount = MembershipPlan[membership_type.upper()].product_discount
            return round(price * (1 - discount), 2)
        else:
            return price
        
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
    
class Gym:
    def __init__(self, name, location):
        self.__name = name
        self.__location = location
        self.__user_list = []
        self.__room_list = []
        self.__item_list = []
        self.__gym_class_list = []
        self.__order_list = []
        self.__payment_list = []
        self.__payment_gateway = PaymentGateway()

    @property
    def payment(self):
        return self.__payment_gateway
    
    def create_payment_list(self):
        self.__payment_list = []

        for order in self.__order_list:
            if order.payment:
                self.__payment_list.append(order.payment)

    def create_room(self, name, max_people):
        room = Room(self, name, max_people)
        self.__room_list.append(room)
        return room

    def create_class(self, name, detail):
        gym_class = GymClass(name, detail)
        self.__gym_class_list.append(gym_class)
        return gym_class

    def create_member(self, citizen_id, name, age):
        member = Member(citizen_id, name, age)
        self.__user_list.append(member)
        return member
    
    def create_trainer(self, citizen_id, name, age, tier, specialization):
        trainer = Trainer(citizen_id, name, age, tier, specialization)
        self.__user_list.append(trainer)
        return trainer
    
    def approve_daypass(self, citizen_id, name, age, target_date):
        try:
            user = self.get_user_by_citizen_id(citizen_id)
        except Exception:
            user = Guest(citizen_id, name, age)
            self.__user_list.append(user)

        if target_date in user.guest_date_list:
            raise Exception(f"Daypass for {target_date} already purchased.")

        order = self.create_order(user)
        order.create_order_item(target_date, type="DaypassDate")
        return order

    def create_item(self, name, amount, price):
        item = Product(name, amount, price)
        self.__item_list.append(item)
    
    # def create_manager(self, citizen_id, name, age, tier, specialization):
    #     manager = Manager(citizen_id, name, age, tier, specialization)
    #     self.__user_list.append(manager)
    #     return manager
    
    def get_available_classes(self):
        class_list = []
        for gym_class in self.__gym_class_list:
            class_list.append(gym_class.info)
        return class_list
    
    def get_available_private_sessions(self):
        trainer_session_list = []
        for user in self.__user_list:
            if isinstance(user, Trainer) : trainer_session_list.append(user.session_info)
        return trainer_session_list

    def print_available_classes(self):
        for gym_class in self.__gym_class_list:
            print(gym_class)

    def get_class_by_id(self, class_id):
        for gym_class in self.__gym_class_list:
            if gym_class.class_id == class_id:
                return gym_class
        raise Exception("gym class not found")
    
    def get_session_by_id(self, session_id):
        for gym_class in self.__gym_class_list:
            session = gym_class.get_session_by_id(session_id)
            if session:
                return session
        for user in self.__user_list:
            if isinstance(user, Trainer):
                session = user.get_session_by_id(session_id)
                if session:
                    return session
        raise Exception("session not found")
    
    def get_member_by_id(self, member_id):
        for user in self.__user_list:
            if hasattr(user, "member_id") and user.member_id == member_id:
                return user
        raise Exception("member not found")
    
    def get_order_by_id(self, order_id):
        for order in self.__order_list:
            if order.order_id == order_id:
                return order
        raise Exception("order not found")

    def get_user_by_citizen_id(self, citizen_id):
        for user in self.__user_list:
            if user.citizen_id == citizen_id:
                return user
        raise Exception("user not found")
    
    def create_order(self, user = None, new_membership_type = None, daypass_date = None, refund = False):
        if refund:
            order = OrderRefund(user)
        else:
            order = Order(user)
        self.__order_list.append(order)
        if isinstance(user, Member):
            user.add_order(order)
        return order
    
    # def create_transaction(self, user = None, new_membership_type = None, daypass_date = None, refund = False):
    #     transaction = Transaction(user = user, daypass_date=daypass_date, refund=refund)
    #     self.__transaction_list.append(transaction)
    #     if isinstance(user, Member):
    #         user.add_transaction(transaction)
    #     return transaction
    
    # def create_or_add_to_transaction(self, user):
    #     for transaction in self.__transaction_list:
    #         if transaction.user == user and transaction.status == "Pending":
    #             transaction
    
    def enroll_member(self, member, session_id):
        session = self.get_session_by_id(session_id)
        session.enroll_member(member)

    def enroll_member_by_id(self, member_id, session_id):
        member = self.get_member_by_id(member_id)
        session = self.get_session_by_id(session_id)
        booking = session.enroll_member(member)

    def refund(self, member, refund_amount: float):
        refund_order = self.create_order(member, refund=True)
        payment = CashPayment()
        payment.set_amount(refund_amount)
        refund_order.set_payment(payment)
        refund_order.process()
        return refund_order

    def cancel_booking(self, member_id: str, session_id: str):
        member = self.get_member_by_id(member_id)
        session = self.get_session_by_id(session_id)
        booking = member.find_booking_by_session_id(session_id)

        if booking is None:
            raise Exception("Booking not found for session" + session_id)
        
        status = booking.status

        if status in ("Cancelled", "Completed"):
            raise Exception(f"Cannot cancel — current status: {status}")
        
        if status == "Pending":
            booking.cancel()
            return {
                "cancelled": True,
                "refund": 0.0,
                "message": "Cancelled (Pending) — no refund, not yet paid"
            }
        
        hours_until = (session.start - datetime.now()).total_seconds() / 3600

        if hours_until <= 0:
            raise Exception("Cannot cancel — session has already started")

        if hours_until < 4:
            booking.cancel()
            return {
            "cancelled": True,
            "refund": 0.0,
            "message": f"Cancelled — no refund ({hours_until:.1f} hrs notice, need >= 4)"
            }
        
        refund_amount = booking.price
        booking.cancel()
        self.refund(member, refund_amount)
        return {
            "cancelled": True,
            "refund": refund_amount,
            "message": (
                f"Cancelled — Refund {refund_amount:.2f} THB"
                f" [{session.get_session_type()} |"
                f" Trainer: {session.trainer.tier} |"
                f" Membership: {member.current_membership}]"
                )
            }

    def replace_user_with_member(self, member):
        citizen_id = member.citizen_id
        for idx, user in enumerate(self.__user_list):
            if user.citizen_id == citizen_id:
                self.__user_list[idx] = member
                print(f"User with citizen_id: {user.citizen_id} has been replaced by Member with {member.current_membership} membership")

    def check_in_member(self, member_id):
        member = self.get_member_by_id(member_id)

        if member.member_status != "Active":
            raise Exception(f"Cannot check-in — member status is '{member.member_status}'")

        booking = member.get_confirmed_booking_today()
        if booking is None:
            raise Exception("No confirmed booking found for today")

        now = datetime.now()
        minutes_late = (now - booking.session.start).total_seconds() / 60

        if minutes_late > 15:
            booking.late_check_in()
            return {
                "status": "Late Check-in",
                "session_id": booking.session.session_id,
                "minutes_late": round(minutes_late)
            }
        else:
            booking.check_in()
            return {
                "status": "Check-in",
                "session_id": booking.session.session_id
            }

    def process_order(self, order_id): 
        self.get_order_by_id(order_id)

    # def pay_cash(self, user):
    #     for transaction in self.__transaction_list:
    #         if transaction.user == user and transaction.status == "Pending":
    #             new_member = transaction.pay_cash()
    #             if isinstance(new_member, Member):
    #                 self.replace_user_with_member(new_member)
    #             return
    #     raise Exception("Transaction of user not found")
    
    # def create_qr_to_pay(self, user):
    #     for transaction in self.__transaction_list:
    #         if transaction.user == user and transaction.status == "Pending":
    #             qr_code = transaction.create_qr()
    #             return qr_code
                
    # def validate_qr_payment(self, user):
    #     for transaction in self.__transaction_list:
    #         if transaction.user == user and transaction.status == "Pending":
    #             result = transaction.validate_qr_payment()
    #             if isinstance(result, Member):
    #                 self.replace_user_with_member(result)
    #                 return True
    #             return result
            
    # def pay_card(self, user):
    #     for transaction in self.__transaction_list:
    #         if transaction.user == user and transaction.status == "Pending":
    #             new_member = transaction.pay_card()
    #             if isinstance(new_member, Member):
    #                 self.replace_user_with_member(new_member)
    #             return
    #     raise Exception("Transaction of user not found")

    def gather_report(self, month, year):
        month_now = datetime.now().month
        year_now = datetime.now().year

        if year > year_now or (year == year_now and month > month_now):
            raise Exception("Report for future month/year cannot be generated")

        revenue_data = {
            "Membership": 0.0,
            "Daypass": 0.0,
            "Product": 0.0,
            "Locker": 0.0,
            "Training": 0.0
        }

        membership_type_count = {
            "Monthly": 0,
            "Annual": 0,
            "Student": 0
        }

        total_revenue = 0.0
        matched_orders = []

        for order in self.__order_list:
            payment = order.payment
            if not payment:
                continue

            if payment.status not in ["Paid", "Refunded"]:
                continue

            if payment.timestamp is None:
                continue

            pay_date = payment.timestamp
            if pay_date.month != month or pay_date.year != year:
                continue

            matched_orders.append(order)

            if payment.status == "Paid":
                multiplier = 1
            else: multiplier = -1

            for order_item in order.order_items:
                price = order_item.calculate_price(order.user) * multiplier
                if isinstance(order_item, NewMembership):
                    revenue_data["Membership"] += price
                    if multiplier > 0:
                        membership_type_count[order_item.membership] += 1
                elif isinstance(order_item, DayPass):
                    revenue_data["Daypass"] += price
                elif isinstance(order_item, ProductAmount):
                    revenue_data["Product"] += price
                elif isinstance(order_item, LockerBooking):
                    revenue_data["Locker"] += price
                elif isinstance(order_item, TrainingBooking):
                    revenue_data["Training"] += price

                total_revenue += price

        return {
            "month": month,
            "year": year,
            "matched_orders_count": len(matched_orders),
            "revenue": revenue_data,
            "total_revenue": round(total_revenue, 2),
            "membership_distribution": membership_type_count
        }


class User(ABC):
    def __init__(self, citizen_id, name, age, guest_date_list = []):
        self.__citizen_id = citizen_id
        self.__name = name
        self.__age = age
        self.__guest_date_list = guest_date_list

    @property
    def citizen_id(self):
        return self.__citizen_id
    
    @property
    def name(self):
        return self.__name
    
    @property
    def age(self):
        return self.__age
    
    @property
    def guest_date_list(self):
        return tuple(self.__guest_date_list)
    
    def add_guest_date(self, date):
        self.__guest_date_list.append(date)
    
    @abstractmethod
    def check_current_notifications(self):
        pass

class Member(User):
    __next_id = 1

    def __init__(self, citizen_id, name, age, current_membership = "Monthly", medical_history = "", goal = "", guest_date_list = []): #MEM-2023-001
        super().__init__(citizen_id, name, age, guest_date_list=guest_date_list)
        self.__member_id = f"MEM-{Member.__next_id:03d}"
        Member.__next_id += 1
        self.__current_membership = current_membership
        self.__medical_history = medical_history
        self.__goal = goal
        self.__training_plan = ""
        self.__status = "Pending"
        self.__membership_log_list = []
        self.__order_list = []
        self.__training_booking_list = []
        self.__locker_booking_list = []

    @property
    def member_id(self):
        return self.__member_id

    @property
    def current_membership(self):
        return self.__current_membership
    
    @property
    def member_status(self):
        return self.__status

    def activate(self):
        self.__status = "Active"

    def get_pending_bookings(self):
        pending_bookings = []
        for training_booking in self.__training_booking_list:
            if training_booking.status == "Pending":
                pending_bookings.append(training_booking)
        for locker_booking in self.__locker_booking_list:
            if locker_booking.status == "Pending":
                pending_bookings.append(locker_booking)
        return pending_bookings

    def set_training_plan(self, text):
        self.__training_plan = text

    def add_booking(self, booking):
        if isinstance(booking, TrainingBooking):
            self.__training_booking_list.append(booking)
        elif isinstance(booking, LockerBooking):
            self.__locker_booking_list.append(booking)

    def add_order(self, order):
        self.__order_list.append(order)

    def print_orders(self):
        for order in self.__order_list:
            print(order)

    def get_current_bookings(self):
        training_bookings = []
        locker_bookings = []
        for training_booking in self.__training_booking_list:
            training_bookings.append(training_booking.info)
        for locker_booking in self.__locker_booking_list:
            locker_bookings.append(locker_booking.info)
        return {
            "training_booking" : training_bookings,
            "locker_booking" : locker_bookings
        }
    
    def enroll_session(self, gym, session_id):
        gym.enroll_member(self,session_id)

    def find_booking_by_session_id(self, session_id: str):
        for booking in self.__training_booking_list:
            if booking.session.session_id == session_id:
                return booking
        return None
    
    def get_confirmed_booking_today(self):
        today = date.today()
        for booking in self.__training_booking_list:
            if booking.status == "Confirmed" and booking.session.date == today:
                return booking
        return None

    def check_current_notifications(self):
        for training_booking in self.__training_booking_list:
            print(training_booking.notification, end="")
        # return super().check_current_notifications()

class Guest(User):
    __next_id = 1

    def __init__(self, citizen_id, name, age):
        super().__init__(citizen_id, name, age)
        self.__guest_id = f"GST-{Guest.__next_id:03d}"
        Guest.__next_id += 1

    @property
    def guest_id(self):
        return self.__guest_id

    def check_current_notifications(self):
        return

class Staff(User):
    __next_id = 1

    def __init__(self, citizen_id, name, age): #MEM-2023-001
        super().__init__(citizen_id, name, age)
        self.__staff_id = f"STF-{Staff.__next_id:03d}"
        Staff.__next_id += 1

    @property
    def staff_id(self):
        return self.__staff_id

class Trainer(Staff):
    def __init__(self, citizen_id, name, age, tier, specialization): #MEM-2023-001
        super().__init__(citizen_id, name, age)
        self.__tier = tier
        self.__specialization = specialization
        self.__session_list = []

    @property
    def tier(self):
        return self.__tier
    
    @property
    def session_list(self):
        return self.__session_list
    
    @property
    def session_info(self):
        sessions = []
        for session in self.session_list:
            sessions.append(session.info)

        return {
            "Staff id": self.staff_id,
            "Name": self.name,
            "Tier": self.__tier,
            "Specialization": self.__specialization,
            "Sessions": sessions
        }
    
    def create_session(self, start, end, date, max_participants, room, trainer = None, gym_class = None):
        if not room.is_available(start, end, date):
            raise Exception("Session is overlapping another previous session")
        if not trainer and not isinstance(self, Trainer):
            raise Exception("Trainer not provided")
        if not trainer: trainer = self
        if max_participants > room.max_people:
            raise Exception(f"Room can only accommodate {room.max_people} people")
        session = Session(start, end, date, max_participants, room, trainer, gym_class)
        self.__session_list.append(session)
        return session
    
    def create_repeating_session(self, start, end, start_date, days_interval, times, max_participants, room, trainer = None, gym_class = None):
        if not trainer and not isinstance(self, Trainer):
            raise Exception("Trainer not provided")
        if not trainer: trainer = self
        if max_participants > room.max_people:
            raise Exception(f"Room can only accommodate {room.max_people} people")
        for time in range(times):
            date = start_date + timedelta(days=days_interval*time)
            if not room.is_available(start, end, date):
                raise Exception("Session is overlapping another previous session")
            
            session = Session(start, end, date, max_participants, room, trainer, gym_class)
            self.__session_list.append(session)

    def view_session(self):
        pass

    def get_session_by_id(self, session_id):
        for session in self.__session_list:
            if session.session_id == session_id:
                return session
        return False

    def write_training_plan(self, sched_or_mem: Session | Member, text):
        sched_or_mem.set_training_plan(text)

    def check_current_notifications(self):
        return super().check_current_notifications()

class Manager(Staff):
    def __init__(self, citizen_id, name, age): #MEM-2023-001
        super().__init__(citizen_id, name, age)
        self.__gym = Gym

    def add_stock(self, name, amount, price):
        self.__gym.create_item(name, amount, price)

    def get_reports(self, month, year):
        return self.__gym.gather_report(month, year)

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

class AbstractOrder(ABC):
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
            total += order_item.calculate_price(self.__user)
        return total
    
    @property
    def order_id(self):
        return self.__order_id

    @property
    def user(self):
        return self.__user

    @property
    def order_items(self):
        return tuple(self.__order_item_list)

    @property
    def status(self):
        return self.__status
    
    def set_payment(self, payment):
        if not isinstance(payment, (CashPayment, CreditCardPayment, QRPayment)):
            raise Exception("Not a valid payment type")
        self.__payment = payment 
    
    @abstractmethod
    def process(self):
        pass

    @abstractmethod
    def verify_and_update_all_info(self):
        pass

    def add_order_item(self, order_item):
        self.__order_item_list.append(order_item)

class Order(AbstractOrder):
    def process(self):
        self.payment.set_amount(self.total_price)
        self.payment.process()
    
    def verify_and_update_all_info(self):
        if self.payment.validate():
            for order_item in self.__order_item_list:
                order_item.set_price_paid(order_item.calculate_price(self.__user))

class OrderRefund(AbstractOrder):
    def process(self):
        self.payment.set_amount(self.total_price)
        self.payment.refund()

    def verify_and_update_all_info(self):
        self.payment.validate()

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
    
    @property
    def timestamp(self):
        return self.__timestamp_payed
    
    def set_payment_gateway_transaction_id(self, id):
        self.__payment_gateway_transaction_id = id

    def set_status(self, status):
        self.__status = status
        if status in ["Paid", "Refunded"]:
            self.__timestamp_payed = datetime.now()

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
        self.set_status("Refunded")

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
        result = PaymentGateway.refund(self.__payment_gateway_transaction_id, self.amount)
        if result:
            self.set_status("Refunded")
        else:
            raise Exception("Error")

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
            return True
        return False

    def refund(self):
        result = PaymentGateway.refund(self.__payment_gateway_transaction_id, self.amount)
        if result:
            self.set_status("Refunded")
        else:
            raise Exception("Error")
