from datetime import datetime, date, time, timedelta
from fastapi import FastAPI, HTTPException
import uvicorn

class TimeSlot:
    def __init__(self, start, end, date, days_between=7, times=1): #-1>forever, other>number of times
        self.__start = start
        self.__end = end
        self.__date = date
        self.__days_between = days_between
        self.__times = times

    @property
    def date(self):
        return self.__date
    
    @property
    def days_between(self):
        return self.__days_between
    
    @property
    def times(self):
        return self.__times
    
    def __str__(self):
        # should change this to day by day so that we can change to show participants in each day too
        if self.__times == 1:
            times_repeat_date_text = f"on {self.__date}"
        elif self.__times == -1:
            times_repeat_date_text = f"every {self.__days_between} days starting {self.__date}"
        else:
            times_repeat_date_text = f"every {self.__days_between} days starting {self.__date} until {self.__date + timedelta(days=self.__times*self.__days_between)}"
        return f"start: {self.__start} end: {self.__end} {times_repeat_date_text}"

class Schedule:
    __next_id = 1

    def __init__(self, name, timeslot):
        self.__schedule_id = Schedule.__next_id
        Schedule.__next_id += 1
        self.__name = name
        self.__timeslot = timeslot

    @property
    def timeslot(self):
        return self.__timeslot
    
    @property
    def name(self):
        return self.__name
    
    @property
    def schedule_id(self):
        return self.__schedule_id
    
class DateBookings:
    def __init__(self, date):
        self.__date = date
        self.__booking_list = []

    @property
    def date(self):
        return self.__date
    
    @property
    def booking_list(self):
        return self.__booking_list
    
    def add_booking(self, booking):
        self.__booking_list.append(booking)

class ClassSchedule(Schedule):
    def __init__(self, name, max_participants, timeslot):
        super().__init__(name, timeslot)
        self.__max_participants = max_participants
        self.__date_booking_list = []

    def is_occuring(self, check_date):
        if self.timeslot.times == 1:
            return check_date == self.timeslot.date

        if check_date < self.timeslot.date:
            return False
        
        delta = check_date - self.timeslot.date

        if delta.days % self.timeslot.days_between != 0:
            return False
        
        if self.timeslot.times != -1:
            occurrence_index = delta.days // self.timeslot.days_between
            
            if occurrence_index > self.timeslot.times:
                return False

        return True

    def enroll_member(self, member, enroll_date):
        if not self.is_occuring(enroll_date):
            raise Exception("Class not scheduled for this date")

        date_booking_obj = self.get_or_create_date_booking(enroll_date)
        current_count = 0
        for booking in date_booking_obj.booking_list:
            if booking.status == "Confirmed":
                current_count += 1
        
        if current_count >= self.__max_participants:
            raise Exception("Class is full")
        
        new_booking = Booking(member.citizen_id, self.schedule_id, enroll_date)

        date_booking_obj.add_booking(new_booking) 
        member.add_booking(new_booking)

        print(f"Booking successful:\n{new_booking}")

    def get_or_create_date_booking(self, date):
        for db in self.__date_booking_list:
            if db.date == date:
                return db
        
        new_db = DateBookings(date)
        self.__date_booking_list.append(new_db)
        return new_db

    # needs to display to current enrolled / available participants slot

    @property
    def info(self):
        return {
            "name": self.name,
            "schedule id": self.schedule_id,
            "timeslot": f"{self.timeslot}",
            "max participants": self.__max_participants
        }

    def __str__(self):
        return f"[{self.name} | schedule id: {self.schedule_id}] {self.timeslot} | Max participants: {self.__max_participants}"

class GymClass:
    __next_id = 1

    def __init__(self, name):
        self.__class_id = GymClass.__next_id
        GymClass.__next_id += 1
        self.__name = name
        self.__class_schedule_list = []

    @property
    def class_id(self):
        return self.__class_id
    
    @property
    def class_schedule_list(self):
        return self.__class_schedule_list
    
    def create_class_schedule(self, name, max_participants, timeslot):
        class_schedule = ClassSchedule(name, max_participants, timeslot)
        self.__class_schedule_list.append(class_schedule)
        return class_schedule
    
    @property
    def info(self):
        schedules = []
        for class_schedule in self.__class_schedule_list:
            schedules.append(class_schedule.info)

        return {
            "Class name": self.__name,
            "Class id": self.__class_id,
            "Class schedule": schedules
        }
    
    def __str__(self):
        text = f"Class name: {self.__name}\nClass id: {self.__class_id}\nClass schedule:\n"
        for class_schedule in self.__class_schedule_list:
            text += f" - {class_schedule}\n"
        return text

class Payment:
    pass

class Gym:
    def __init__(self, name, location):
        self.__name = name
        self.__location = location
        self.__gym_class_list = []
        self.__user_list = []
        self.__payment = Payment() #(self)

    def create_class(self, name):
        gym_class = GymClass(name)
        self.__gym_class_list.append(gym_class)
        return gym_class

    def create_member(self, citizen_id, name, age):
        member = Member(citizen_id, name, age)
        self.__user_list.append(member)
        return member
    
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
            for class_schedule in gym_class.class_schedule_list:
                if class_schedule.schedule_id == schedule_id:
                    return class_schedule
        raise Exception("class schedule not found")
    
    def enroll_member(self, member, schedule_id, enroll_date):
        class_schedule = self.get_schedule_by_id(schedule_id)
        class_schedule.enroll_member(member, enroll_date)

class User:
    def __init__(self, citizen_id, name, age):
        self.__citizen_id = citizen_id
        self.__name = name
        self.__age = age

    @property
    def citizen_id(self):
        return self.__citizen_id

class Member(User):
    def __init__(self, citizen_id, name, age): #MEM-2023-001
        super().__init__(citizen_id, name, age)
        self.__booking_list = []

    def add_booking(self, booking):
        self.__booking_list.append(booking)

    def get_current_bookings(self):
        bookings = []
        for booking in self.__booking_list:
            bookings.append(booking.info)
        return bookings

class Booking:
    __next_id = 1

    def __init__(self, citizen_id, schedule_id, class_date):
        self.__booking_id = Booking.__next_id
        Booking.__next_id += 1
        self.__citizen_id = citizen_id
        self.__schedule_id = schedule_id
        self.__class_date = class_date
        self.__status = "Pending" # statuses: Waitlist Confirmed Check-in Completed Cancelled

    @property
    def info(self):
        if self.__status == "Pending":
            status_text = "Pending. Please Pay to Confirm Booking"
        else:
            status_text = self.__status
        return {
            "Booking id" : self.__booking_id,
            "schedule id" : self.__schedule_id,
            "Citizen id" : self.__citizen_id,
            "Class date": self.__class_date,
            "Status": status_text
        }

    def __str__(self):
        if self.__status == "Pending":
            status_text = "Pending. Please Pay to Confirm Booking"
        else:
            status_text = self.__status
        text = f"Booking id: {self.__booking_id}\nschedule id: {self.__schedule_id}\nCitizen id: {self.__citizen_id}\nClass date: {self.__class_date}\nStatus: {status_text}"
        return text
    
def create_stuff():
    gym = Gym("my gym", "1/45 bangkok thailand")
    
    yoga_class = gym.create_class("yoga")

    saturday_morning_timeslot = TimeSlot(time(10,0,0),time(11,30,0),date(2026,2,7),times=-1)
    yoga_saturday_morning_class = yoga_class.create_class_schedule("Saturday morning class",10,saturday_morning_timeslot)
    
    special_sunday_timeslot = TimeSlot(time(14,0,0),time(16,00,0),date(2026,2,8))
    special_sunday_class = yoga_class.create_class_schedule("Special sunday class",7,special_sunday_timeslot)

    bike_class = gym.create_class("bike")
    every4days_night_x5_timeslot = TimeSlot(time(18,0,0),time(20,00,0),date(2026,2,14),4,5)
    every4days_night_x5_bike_class = bike_class.create_class_schedule("every4days night x5",15,every4days_night_x5_timeslot)

    bob_membership = gym.create_member("123456789", "Bobda builder", 19)

    return gym, bob_membership

def run_test(gym, bob_membership):
    gym.print_available_classes() # to see and choose what to enroll in

    schedule_id = int(input("Enter schedule id to enroll bob into: "))
    date_string = input("Enter date that bob will be participating in [yyyy-mm-dd]: ")
    enroll_date = datetime.strptime(date_string, '%Y-%m-%d').date()

    gym.enroll_member(bob_membership, schedule_id, enroll_date)

    def minimize_to_cleaner():
        # testing if check date logic is correct
        # schedule = gym.get_schedule_by_id(2)
        # for i in range(1,29):
        #     print(f"{i} : {schedule.is_occuring(date(2026,2,i))}")
        # for i in range(1,20):
        #     print(f"{i} : {schedule.is_occuring(date(2026,3,i))}")
        # print(schedule)

        # after enrolling need to confirm by paying
        # can cancel
        pass

def run_api_test(gym: Gym, bob_membership: Member):
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
    def enroll_class(schedule_id: int, body: dict) -> dict:
        try:
            date_string = body["date"]
            enroll_date = datetime.strptime(date_string, '%Y-%m-%d').date()
            gym.enroll_member(bob_membership, schedule_id, enroll_date)
            return {"success": f"bob has been succesfully enrolled into class with schedule_id: {schedule_id} on {enroll_date}"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

if __name__ == "__main__":
    gym, bob_membership = create_stuff()
    # run_test(gym, bob_membership)
    run_api_test(gym, bob_membership)


