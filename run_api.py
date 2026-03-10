from datetime import datetime, date, time, timedelta
import uvicorn, pprint
from fastapi import FastAPI, HTTPException

from models import Gym, Member, Trainer

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


def run_api(gym: Gym, gym_bro: Trainer, manager_tyler, receptionist_alya, bob_membership: Member):
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
    # run_test(gym, gym_bro, manager_tyler, receptionist_alya, bob_membership)
    run_api(gym, gym_bro, manager_tyler, receptionist_alya, bob_membership)