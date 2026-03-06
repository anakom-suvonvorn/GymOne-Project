from abc import ABC, abstractmethod
from datetime import datetime, date, time, timedelta
from fastapi import FastAPI, HTTPException
import uvicorn, textwrap, pprint
from order_and_payment import MembershipPlan, TrainerTier, LockerType, AbstractOrder, OrderItem, Order, OrderRefund, PaymentGateway
# from order_and_payment import *

# paul has been here

class Booking:
    def __init__(self, status = "Pending"):
        self.__status = status # statuses: Waitlist Confirmed Check-in Completed Cancelled

    @property
    def status(self):
        return self.__status

    def confirm(self):
        self.__status = "Confirmed"

    def cancel(self):
        self.__status = "Cancelled"

class TrainingBooking(Booking):

    def __init__(self, member, session, status="Pending"):
        super().__init__()
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
        elif self.__status == "Waitlist":
            queue_count = self.__session.get_queue_count(self)
            if queue_count == 0:
                return f"[session id: {self.__session.session_id}] Currently the next booking in line\n"
            else:
                return f"[session id: {self.__session.session_id}] There's currently {queue_count} queue before this\n"
        else:
            return ""
        
    @property
    def price(self):
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

    def get_queue_count(self, training_booking):
        queue_count = 0
        for booking in self.__training_booking_list:
            if booking == training_booking:
                return queue_count
            elif booking.status == "Waitlist":
                queue_count+=1

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
            # Waitlist > will update to Pending if next time that check/action/other cancel/etc. and there's free
            booking = TrainingBooking(member, self, "Waitlist")
        else:
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
    
class SessionManager:
    def __init__(self):
        self.__session_list = []

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

class GymClass(SessionManager):
    __next_id = 1

    def __init__(self, name, detail):
        super().__init__()
        self.__class_id = f"CL-{GymClass.__next_id}"
        GymClass.__next_id += 1
        self.__name = name
        self.__detail = detail

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
    
    @property
    def price(self):
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

class ProductAmount:
    def __init__(self, item, amount):
        self.__item = item
        self.__amount = amount
    
    @property
    def item(self):
        return self.__item
    
    @property
    def amount(self):
        return self.__amount
    
    def price(self, member = None):
        price = self.__item.price * self.__amount
        if member:
            membership_type = member.current_membership
            discount = MembershipPlan[membership_type.upper()].product_discount
            return round(price * (1 - discount), 2)
        else:
            return price
        
# class Transaction:
#     __TRAINER_TIER_PRICE = {
#     # private, class
#     "Junior": [800,200],
#     "Senior": [1500,375],
#     "Master": [2500,625]
#     }

#     __LOCKER_HOUR_PRICE = {
#         "Normal": 35,
#         "VIP" : 70
#     }

#     __MEMBER_DISCOUNT = {
#         # booking, item, locker
#         "Monthly" : [0, 0, 0],
#         "Annual" : [0.2, 0.1, 0.15],
#         "Student" : [0.15, 0, 0.10]
#     }

#     __MEMBER_PRICE = {
#         "Monthly" : 1500,
#         "Annual" : 15000,
#         "Student" : 1200
#     }

#     def __init__(self, user = None, new_membership_type = None, daypass_date = None, refund = False):
#         self.__timestamp_payed = None
#         self.__user = user # can just be a default user, or member, or None if stuff like buy item stuff wid nothing else
#         self.__item_amount_list = []
#         self.__training_booking_list = []
#         self.__locker_booking_list = []
#         self.__new_membership_type = new_membership_type
#         self.__daypass_date = daypass_date
#         self.__refund = refund
#         self.__qr_code = None
#         self.__status = "Pending"

#     @property
#     def total_amount(self):
#         total = 0
#         # get item total
#         for item_amount in self.__item_amount_list:
#             total += item_amount.item.price * item_amount.amount

#         # get training booking total
#         if isinstance(self.__user, Member):
#             membership_type = self.__user.current_membership
#         for training_booking in self.__training_booking_list:
#             session = training_booking.session
#             session_type = session.get_session_type()
#             trainer_tier = session.trainer.tier
#             price = Transaction.__TRAINER_TIER_PRICE[trainer_tier][session_type == "Class"]
#             discount = Transaction.__MEMBER_DISCOUNT[membership_type][0]
#             discount_price = round(price * (1-discount), 2)
#             total += discount_price

#         # get locker booking total
#         for locker_booking in self.__locker_booking_list:
#             discount = Transaction.__MEMBER_DISCOUNT[membership_type][2]
#             locker_price = Transaction.__LOCKER_HOUR_PRICE[locker_booking.locker.type]
#             locker_duration = locker_booking.locker.duration_hours
#             total_price = locker_price * locker_duration
#             discount_price = round(total_price * (1-discount), 2)
#             total += discount_price

#         if self.__new_membership_type:
#             membership_price = Transaction.__MEMBER_PRICE[self.__new_membership_type]
#             total += membership_price

#         if self.__daypass_date:
#             total += 500

#     @property
#     def user(self):
#         return self.__user
    
#     @property
#     def status(self):
#         return self.__status
    
#     def update_all_related_info_payed(self):
#         self.__status = "Payed"
#         self.__timestamp_payed = datetime.now()

#         # update stock of all items in the list
#         for item_amount in self.__item_amount_list:
#             item_amount.item.sell_stock(item_amount.amount)

#         # update training booking status
#         for training_booking in self.__training_booking_list:
#             training_booking.status = "Confirmed"

#         # update locker booking status
#         for locker_booking in self.__locker_booking_list:
#             locker_booking.status = "Confirmed"

#         # update guest date list if daypass
#         if self.__daypass_date:
#             self.__user.add_guest_date(self.__daypass_date)

#         # update membership type
#         if self.__new_membership_type:
#             if isinstance(self.__user, Member):
#                 self.__user.set_membership(self.__new_membership_type)
#             elif isinstance(self.__user, User):
#                 new_member = Member(self.__user.citizen_id, self.__user.name, self.__user.age, self.__new_membership_type, guest_date_list=self.__user.guest_date_list)
#                 return new_member
#             else:
#                 raise Exception("I dont know who this annonymus is")
#         return None

#     def book_locker_if_training_booking(self):
#         for training_booking in self.__training_booking_list:
#             session = training_booking.session
#             new_locker_booking = session.room.reserve_locker("Normal", self.__user, session.start, session.end, "Confirmed")
#             print(f"Reserved a free included normal locker during the same time starting {new_locker_booking.start} and ending {new_locker_booking.end} for {new_locker_booking.member.name} at locker {new_locker_booking.locker.locker_id}")

#     def pay_cash(self):        
#         self.book_locker_if_training_booking()
#         new_member = self.update_all_related_info_payed()
#         if new_member:
#             return new_member

#     def create_qr(self):
#         qrcode = PaymentGateway.create_qr(self.total_amount)
#         self.__qr_code = qrcode
#         return qrcode

#     def validate_qr_payment(self):
#         if PaymentGateway.validate_qr_payment(self.__qr_code):
#             self.book_locker_if_training_booking()
#             new_member = self.update_all_related_info_payed()
#             if new_member:
#                 return new_member
#             print("Payment Successful")
#             return True
#         print("QR has not been paid yet")
#         return False

#     def pay_card(self):
#         if not PaymentGateway.pay_card(self.total_amount):
#             raise Exception("Payment Failed")
#         self.book_locker_if_training_booking()
#         new_member = self.update_all_related_info_payed()
#         if new_member:
#             return new_member

#     def add_item_amount(self, item, amount):
#         self.__item_amount_list.append(ProductAmount(item, amount))

#     def add_training_booking(self, training_booking):
#         self.__training_booking_list.append(training_booking)

#     def add_locker_booking(self, locker_booking):
#         self.__locker_booking_list.append(locker_booking)

#     def __str__(self):
#         text = f"User: {self.__user.name}\n PaymentTimeStamp: {self.__timestamp_payed}\n"
#         text = f"Type: {"Refund" if self.__refund else "Payment"}\n Status: {self.__status}\n"
#         text += f"TotalAmount: {self.total_amount}\n"

#         if self.__item_amount_list: text += "ProductBuyingList:\n"
#         for item_amount in self.__item_amount_list:
#             text += f" - Name: {item_amount.item.name} Amount: {item_amount.amount} Total: {item_amount.amount * item_amount.item.price}\n"

#         if self.__training_booking_list: text += "TrainingBookingList:\n"
#         for training_booking in self.__training_booking_list:
#             text += f" - {training_booking}\n"

#         if self.__locker_booking_list: text += "LockerBookingList:\n"
#         for locker_booking in self.__locker_booking_list:
#             text += f" - {locker_booking}\n"

#         if self.__daypass_date:
#             text += f"DayPass for date: {self.__daypass_date}\n"

#         if self.__new_membership_type:
#             text += f"New Membership: {self.__new_membership_type}\n"

class Gym:
    def __init__(self, name, location):
        self.__name = name
        self.__location = location
        self.__user_list = []
        self.__room_list = []
        self.__item_list = []
        self.__gym_class_list = []
        self.__order_list = []
        self.__payment_gateway = PaymentGateway()

    @property
    def payment(self):
        return self.__payment_gateway

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
            pass
            # if order.

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

    def replace_user_with_member(self, member):
        citizen_id = member.citizen_id
        for idx, user in enumerate(self.__user_list):
            if user.citizen_id == citizen_id:
                self.__user_list[idx] = member
                print(f"User with citizen_id: {user.citizen_id} has been replaced by Member with {member.current_membership} membership")

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

    def check_current_notifications(self):
        for training_booking in self.__training_booking_list:
            print(training_booking.notification, end="")
        # return super().check_current_notifications()
    
class Staff(User):
    __next_id = 1

    def __init__(self, citizen_id, name, age): #MEM-2023-001
        super().__init__(citizen_id, name, age)
        self.__staff_id = f"STF-{Staff.__next_id:03d}"
        Staff.__next_id += 1

    @property
    def staff_id(self):
        return self.__staff_id

class Trainer(Staff, SessionManager):
    def __init__(self, citizen_id, name, age, tier, specialization): #MEM-2023-001
        Staff.__init__(self, citizen_id, name, age)
        SessionManager.__init__(self)
        self.__tier = tier
        self.__specialization = specialization
        self.__session_list = []

    @property
    def tier(self):
        return self.__tier

    def write_training_plan(self, sched_or_mem: Session | Member, text):
        sched_or_mem.set_training_plan(text)

    def check_current_notifications(self):
        return super().check_current_notifications()

def create_stuff():
    gym = Gym("my gym", "1/45 bangkok thailand")

    # item stuff
    gym.create_item("Energy drink", 50, 40)
    gym.create_item("Water", 100, 15)
    gym.create_item("Whey protein", 20, 1500)

    private_room = gym.create_room("a private room", 2)
    private_room.create_lockers(2,1)

    gym_bro = gym.create_trainer("987654321", "Yabro Muscal", 25, "Junior", "muscle making")
    gym_bro.create_repeating_session(time(8,0,0),time(10,30,0),date(2026,4,15),7,3,1,private_room)

    manager_tyler = None

    receptionist_alya = None

    bob_membership = gym.create_member("123456789", "Bobda builder", 19)

    yoga_studio = gym.create_room("yoga studio", 10)
    yoga_studio.create_lockers(10,4)
    multi_studio = gym.create_room("multi studio", 5)
    multi_studio.create_lockers(5,2)
    
    yoga_class = gym.create_class("yoga", "stretchin dat bodae")
    yoga_class.create_repeating_session(time(10,0,0),time(11,30,0),date(2026,2,7),7,5,10,yoga_studio,gym_bro,yoga_class)

    bike_class = gym.create_class("bike", "workin on our leggies")
    eve_bike_sched = bike_class.create_session(time(15,30,0),time(16,30,0),date.today(),3,multi_studio,gym_bro,bike_class)
    night_bike_sched = bike_class.create_session(time(18,0,0),time(19,30,0),date.today(),5,multi_studio,gym_bro,bike_class)

    gym_bro.write_training_plan(night_bike_sched, "we'll be biking for 30 km")
    gym_bro.write_training_plan(bob_membership, "focus on training the lower leg area")

    return gym, gym_bro, manager_tyler, receptionist_alya, bob_membership

def run_test(gym: Gym, gym_bro: Trainer, manager_tyler, receptionist_alya, bob_membership: Member):
    gym.print_available_classes() # to see and choose what to enroll in

    session_id = input("Enter session id to enroll into: ")
    member_id = input("Enter member_id: ")

    # citizen_id = input("Enter citizen_id: ")
    # user = gym.get_user_by_citizen_id(citizen_id)

    # both works
    gym.enroll_member_by_id(member_id, session_id)
    # gym.enroll_member(user, session_id)
    # bob_membership.enroll_session(gym, session_id)

    pprint.pprint(bob_membership.get_current_bookings(), indent=4)
    bob_membership.print_orders()
    # print(bob_membership.get_pending_bookings())

    gym.pay_card(bob_membership)
    # gym.payment.pay_booking(bob_membership)

    pprint.pprint(bob_membership.get_current_bookings(), indent=4)
    bob_membership.print_orders()


def run_api_test(gym: Gym, gym_bro: Trainer, manager_tyler, receptionist_alya, bob_membership: Member):
    app = FastAPI()

    @app.get("/")
    def home():
        return {"status": "Server is up!"}
    
    @app.get("/showclass")
    def show_available_classes():
        classes = gym.get_available_classes()
        return {
            "classes": classes,
            "tip": "To enroll in class go to /enrollclass/{session_id} with the content {'citizen_id': 'xxxxxxxxx'}"
        }
    
    @app.get("/showbooking")
    def show_current_bookings():
        bookings = bob_membership.get_current_bookings()
        return {
            "bookings": bookings,
        }
    
    @app.post("/enrollclass/{session_id}")
    def enroll_class(session_id: str, body: dict) -> dict:
        try:
            member_id = body["member_id"]
            gym.enroll_member_by_id(member_id, session_id)
            return {"success": f"{member_id} has been succesfully enrolled into class with session_id: {session_id}"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
        
    @app.post("/pay_bookings")
    def pay_bookings(body: dict) -> dict:
        try:
            member_id = body["member_id"]
            member = gym.get_member_by_id(member_id)
            total, payments = gym.payment.pay_booking(member)
            return {
                "success": f"{member.name} has succesfully payed a total of {total} with these payments",
                "payments": [f"{payment}" for payment in payments]
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

if __name__ == "__main__":
    gym, gym_bro, manager_tyler, receptionist_alya, bob_membership = create_stuff()
    run_test(gym, gym_bro, manager_tyler, receptionist_alya, bob_membership)
    # run_api_test(gym, gym_bro, manager_tyler, receptionist_alya, bob_membership)


