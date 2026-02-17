from abc import ABC, abstractmethod
from datetime import datetime, date, time, timedelta
from fastapi import FastAPI, HTTPException
import uvicorn, textwrap, pprint

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

    def __init__(self, member, schedule, status="Pending"):
        super().__init__()
        self.__member = member
        self.__schedule = schedule
        self.__training_log = ""

    @property
    def member(self):
        return self.__member
    
    @property
    def schedule(self):
        return self.__schedule

    @property
    def info(self):
        if self.status == "Pending":
            status_text = "Pending. Please Pay to Confirm Booking"
        else:
            status_text = self.status
        return {
            "schedule id" : self.__schedule.schedule_id,
            "Class date": self.__schedule.date,
            "Status": status_text
        }
    
    @property
    def notification(self):
        if self.__schedule.status == "Cancelled":
            return f"[schedule id: {self.__schedule.schedule_id}] Has been cancelled"
        elif self.__status == "Pending":
            return "Pending. Please Pay to Confirm Booking"
        elif self.__status == "Waitlist":
            queue_count = self.__schedule.get_queue_count(self)
            if queue_count == 0:
                return f"[schedule id: {self.__schedule.schedule_id}] Currently the next booking in line\n"
            else:
                return f"[schedule id: {self.__schedule.schedule_id}] There's currently {queue_count} queue before this\n"
        else:
            return ""

    def __str__(self):
        # if self.__status == "Pending":
        #     status_text = "Pending. Please Pay to Confirm Booking"
        # else:
        #     status_text = self.__status
        # text = f"Booking id: {self.__booking_id}\nschedule id: {self.__schedule_id}\nCitizen id: {self.__citizen_id}\nClass date: {self.__class_date}\nStatus: {status_text}"
        # return text
        pass

class Schedule:

    def __init__(self, start, end, date, max_participants, room, trainer, gym_class = None):
        if gym_class:
            schedule_len = len(gym_class.schedule_list)
            self.__schedule_id = f"{gym_class.class_id}-{schedule_len+1:03d}"
        else:
            schedule_len = len(trainer.schedule_list)
            self.__schedule_id = f"{trainer.staff_id}-{schedule_len+1:03d}"
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
    def schedule_id(self):
        return self.__schedule_id
    
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
            "schedule id": self.schedule_id,
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
    
    def get_schedule_type(self):
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

        # TODO: booking schedule comes with a free, normal locker
        # but probably should be added when the member "Confirmes" by paying, NOT here right away

        return booking
    
    def is_available(self, new_start, new_end, new_date):
        if self.__date != new_date:
            return True
        
        return self.end <= new_start or self.start >= new_end
    
    def __str__(self):
        text = f"[{self.__schedule_id}]\n"
        text += f"Start: {self.__start} End: {self.__end} Date: {self.__date}\n"
        text += f"With: {self.__trainer.name} At: {self.__room.name} [{self.__room.room_id}]\n"
        if self.__training_plan:
            text += f"Training plan: {self.__training_plan}\n"
        text += f"Enrolled: {self.get_enrolled_num()} Max: {self.__max_participants}"
        return text
    
class ScheduleManager:
    def __init__(self):
        self.__schedule_list = []

    @property
    def schedule_list(self):
        return self.__schedule_list
    
    def create_schedule(self, start, end, date, max_participants, room, trainer = None, gym_class = None):
        if not room.is_available(start, end, date):
            raise Exception("Schedule is overlapping another previous schedule")
        if not trainer and not isinstance(self, Trainer):
            raise Exception("Trainer not provided")
        if not trainer: trainer = self
        if max_participants > room.max_people:
            raise Exception(f"Room can only accommodate {room.max_people} people")
        schedule = Schedule(start, end, date, max_participants, room, trainer, gym_class)
        self.__schedule_list.append(schedule)
        return schedule
    
    def create_repeating_schedule(self, start, end, start_date, days_interval, times, max_participants, room, trainer = None, gym_class = None):
        if not trainer and not isinstance(self, Trainer):
            raise Exception("Trainer not provided")
        if not trainer: trainer = self
        if max_participants > room.max_people:
            raise Exception(f"Room can only accommodate {room.max_people} people")
        for time in range(times):
            date = start_date + timedelta(days=days_interval*time)
            if not room.is_available(start, end, date):
                raise Exception("Schedule is overlapping another previous schedule")
            
            schedule = Schedule(start, end, date, max_participants, room, trainer, gym_class)
            self.__schedule_list.append(schedule)

    def view_schedule(self):
        pass

    def get_schedule_by_id(self, schedule_id):
        for schedule in self.__schedule_list:
            if schedule.schedule_id == schedule_id:
                return schedule
        return False

class GymClass(ScheduleManager):
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
        schedules = []
        for schedule in self.schedule_list:
            schedules.append(schedule.info)

        return {
            "Class id": self.__class_id,
            "Class name": self.__name,
            "Class detail": self.__detail,
            "Class schedule": schedules
        }
    
    def __str__(self):
        text = f"Class name: {self.__name}\nClass id: {self.__class_id}\nSchedule:\n"
        for schedule in self.schedule_list:
            schedule_str = str(schedule)

            indented_schedule = textwrap.indent(schedule_str, '   ')

            text += f" - {indented_schedule.lstrip()}\n"
        return text

class Payment:
    __TRAINER_TIER_PRICE = {
        # private, class
        "Junior": [800,200],
        "Senior": [1500,375],
        "Master": [2500,625]
    }

    __LOCKER_HOUR_PRICE = {
        "Normal": 35,
        "VIP" : 70
    }

    __MEMBER_DISCOUNT = {
        # booking, item, locker
        "Monthly" : [0, 0, 0],
        "Annual" : [20, 10, 15],
        "Student" : [15, 0, 10]
    }
    
    def __init__(self, gym):
        self.__gym = gym

    def pay_all(self, member):
        pass

    def pay_booking(self, member):
        pending_bookings = member.get_pending_bookings() # need to change to NOT get locker booking since it is all already paid
        membership_type = member.current_membership
        for pending_booking in pending_bookings:
            if isinstance(pending_booking, TrainingBooking):
                schedule = pending_booking.schedule
                schedule_type = schedule.get_schedule_type()
                trainer_tier = schedule.trainer.tier
                price = Payment.__TRAINER_TIER_PRICE[trainer_tier][schedule_type == "Class"]
                discount = Payment.__MEMBER_DISCOUNT[membership_type][0]
                discount_price = round(price * (1-discount), 2)
                self.__gym.create_transaction("CLS" if "Class" else "PVT", discount_price, datetime.now(), member)

                # also comes with a free normal locker
                new_locker_booking = schedule.room.reserve_locker("Normal", member, schedule.start, schedule.end, "Confirmed")
                print(f"Reserved a free included normal locker during the same time starting {new_locker_booking.start} and ending {new_locker_booking.end} for {new_locker_booking.member.name} at locker {new_locker_booking.locker.locker_id}")

            elif isinstance(pending_booking, LockerBooking): # need to change to NOT locker booking since it is all already paid
                discount = Payment.__MEMBER_DISCOUNT[membership_type][2]
                locker_price = Payment.__LOCKER_HOUR_PRICE[pending_booking.locker.type]
                locker_duration = pending_booking.locker.duration_hours
                total_price = locker_price * locker_duration
                discount_price = round(total_price * (1-discount), 2)
                self.__gym.create_transaction("LKR" if "Normal" else "LKR-VIP", discount_price, datetime.now(), member)
            pending_booking.confirm()

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

    def is_time_conflict(self, start, end): # 7-10 9-12 > 7<12 true, 9<10 true
        return self.__start < end and start < self.__end

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
        self.__schedule_list = []
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
        for schedule in self.__schedule_list:
            if not schedule.is_available(start, end, date):
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
    
class Transaction:
    def __init__(self, type, amount, timestamp, member):
        self.__type = type
        self.__amount = amount
        self.__timestamp = timestamp
        self.__member = member

    def __str__(self):
        return f"[{self.__type}] {self.__amount}_{self.__timestamp.date()}_{self.__timestamp.replace(microsecond=0).time()}_{self.__member.member_id}"

class Gym:
    def __init__(self, name, location):
        self.__name = name
        self.__location = location
        self.__payment = Payment(self)
        self.__user_list = []
        self.__room_list = []
        self.__item_list = []
        self.__gym_class_list = []
        self.__transaction_list = []

    @property
    def payment(self):
        return self.__payment

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
    
    def create_transaction(self, type, amount, timestamp, member):
        transaction = Transaction(type, amount, timestamp, member)
        self.__transaction_list.append(transaction)
        member.add_transaction(transaction)
    
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
    
    def get_schedule_by_id(self, schedule_id):
        for gym_class in self.__gym_class_list:
            schedule = gym_class.get_schedule_by_id(schedule_id)
            if schedule:
                return schedule
        for user in self.__user_list:
            if isinstance(user, Trainer):
                schedule = user.get_schedule_by_id(schedule_id)
                if schedule:
                    return schedule
        raise Exception("schedule not found")
    
    def get_user_by_citizen_id(self, citizen_id):
        for user in self.__user_list:
            if user.citizen_id == citizen_id:
                return user
        raise Exception("user not found")
    
    def enroll_member(self, member, schedule_id):
        schedule = self.get_schedule_by_id(schedule_id)
        schedule.enroll_member(member)

class User(ABC):
    def __init__(self, citizen_id, name, age):
        self.__citizen_id = citizen_id
        self.__name = name
        self.__age = age
        self.__guest_date_list = []

    @property
    def citizen_id(self):
        return self.__citizen_id
    
    @property
    def name(self):
        return self.__name
    
    @abstractmethod
    def check_current_notifications(self):
        pass

class Member(User):
    __next_id = 1

    def __init__(self, citizen_id, name, age, current_membership = "Monthly", medical_history = "", goal = ""): #MEM-2023-001
        super().__init__(citizen_id, name, age)
        self.__member_id = f"MEM-{Member.__next_id:03d}"
        Member.__next_id += 1
        self.__current_membership = current_membership
        self.__medical_history = medical_history
        self.__goal = goal
        self.__training_plan = ""
        self.__status = "Pending"
        self.__membership_log_list = []
        self.__transaction_list = []
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
                pending_bookings.append(training_booking)
        return pending_bookings

    def set_training_plan(self, text):
        self.__training_plan = text

    def add_booking(self, booking):
        if isinstance(booking, TrainingBooking):
            self.__training_booking_list.append(booking)
        elif isinstance(booking, LockerBooking):
            self.__locker_booking_list.append(booking)

    def add_transaction(self, transaction):
        self.__transaction_list.append(transaction)

    def print_transactions(self):
        for transaction in self.__transaction_list:
            print(transaction)

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
    
    def enroll_schedule(self, gym, schedule_id):
        gym.enroll_member(self,schedule_id)

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

class Trainer(Staff, ScheduleManager):
    def __init__(self, citizen_id, name, age, tier, specialization): #MEM-2023-001
        Staff.__init__(self, citizen_id, name, age)
        ScheduleManager.__init__(self)
        self.__tier = tier
        self.__specialization = specialization
        self.__schedule_list = []

    @property
    def tier(self):
        return self.__tier

    def write_training_plan(self, sched_or_mem: Schedule | Member, text):
        sched_or_mem.set_training_plan(text)

    def check_current_notifications(self):
        return super().check_current_notifications()

def create_stuff():
    gym = Gym("my gym", "1/45 bangkok thailand")

    private_room = gym.create_room("a private room", 2)
    private_room.create_lockers(2,1)

    gym_bro = gym.create_trainer("987654321", "Yabro Muscal", 25, "Junior", "muscle making")
    gym_bro.create_repeating_schedule(time(8,0,0),time(10,30,0),date(2026,4,15),7,3,1,private_room)

    manager_tyler = None

    receptionist_alya = None

    bob_membership = gym.create_member("123456789", "Bobda builder", 19)

    yoga_studio = gym.create_room("yoga studio", 10)
    yoga_studio.create_lockers(10,4)
    multi_studio = gym.create_room("multi studio", 5)
    yoga_studio.create_lockers(5,2)
    
    yoga_class = gym.create_class("yoga", "stretchin dat bodae")
    yoga_class.create_repeating_schedule(time(10,0,0),time(11,30,0),date(2026,2,7),7,5,10,yoga_studio,gym_bro,yoga_class)

    bike_class = gym.create_class("bike", "workin on our leggies")
    eve_bike_sched = bike_class.create_schedule(time(15,30,0),time(16,30,0),date.today(),3,multi_studio,gym_bro,bike_class)
    night_bike_sched = bike_class.create_schedule(time(18,0,0),time(19,30,0),date.today(),5,multi_studio,gym_bro,bike_class)

    gym_bro.write_training_plan(night_bike_sched, "we'll be biking for 30 km")
    gym_bro.write_training_plan(bob_membership, "focus on training the lower leg area")

    return gym, gym_bro, manager_tyler, receptionist_alya, bob_membership

def run_test(gym: Gym, gym_bro: Trainer, manager_tyler, receptionist_alya, bob_membership: Member):
    gym.print_available_classes() # to see and choose what to enroll in

    schedule_id = input("Enter schedule id to enroll into: ")
    # citizen_id = input("Enter citizen_id: ")
    # user = gym.get_user_by_citizen_id(citizen_id)

    # both works
    # gym.enroll_member(user, schedule_id)
    bob_membership.enroll_schedule(gym, schedule_id)

    pprint.pprint(bob_membership.get_current_bookings(), indent=4)
    bob_membership.print_transactions()
    # print(bob_membership.get_pending_bookings())

    gym.payment.pay_booking(bob_membership)

    pprint.pprint(bob_membership.get_current_bookings(), indent=4)
    bob_membership.print_transactions()


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
            "tip": "To enroll in class go to /enrollclass/{schedule_id} with the content {date: 'yyyy-mm-dd'}"
        }
    
    @app.get("/showbooking")
    def show_current_bookings():
        bookings = bob_membership.get_current_bookings()
        return {
            "bookings": bookings,
        }
    
    @app.post("/enrollclass/{schedule_id}")
    def enroll_class(schedule_id: str, body: dict) -> dict:
        try:
            citizen_id = body["citizen_id"]
            user = gym.get_user_by_citizen_id(citizen_id)
            print("user is good")
            gym.enroll_member(user, schedule_id)
            print("enroll is good")
            return {"success": f"{user.name} has been succesfully enrolled into class with schedule_id: {schedule_id}"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

if __name__ == "__main__":
    gym, gym_bro, manager_tyler, receptionist_alya, bob_membership = create_stuff()
    run_test(gym, gym_bro, manager_tyler, receptionist_alya, bob_membership)
    # run_api_test(gym, gym_bro, manager_tyler, receptionist_alya, bob_membership)


