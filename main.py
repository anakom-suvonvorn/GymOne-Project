from datetime import datetime, date, time, timedelta
import uvicorn, pprint
from fastapi import FastAPI, HTTPException, APIRouter
from fastapi_mcp import FastApiMCP

from models import Gym, Member, Trainer
from routers.members import router as member_router
from routers.trainers import router as trainer_router
from routers.receptionists import router as receptionist_router
from routers.managers import router as manager_router
from database import gym

def create_stuff():
    # create products
    gym.create_product("Energy drink", 50, 40)
    gym.create_product("Water", 100, 15)
    gym.create_product("Whey protein", 20, 1500)

    # create rooms and their lockers
    locker_room = gym.create_room("main locker room", 0)
    locker_room.create_lockers(20,5)

    private_room = gym.create_room("a private room", 2)
    private_room.create_lockers(2,1)

    yoga_studio = gym.create_room("yoga studio", 10)
    yoga_studio.create_lockers(10,4)

    multi_studio = gym.create_room("multi studio", 5)
    multi_studio.create_lockers(5,2)

    # create managers
    manager_tyler = gym.create_manager("111111111", "Tyler", date(1990, 1, 1))

    # create receptionists
    receptionist_alya = gym.create_receptionist("135792468", "Alya receptionist", date(1995, 1, 1))

    # create trainers and their sessions
    gym_bro = gym.create_trainer("987654321", "Yabro Muscal", date(2000, 1, 1), "Junior", "muscle making")
    gym_bro.create_repeating_session(time(8,0,0),time(10,30,0),date(2026,4,15),7,3,1,private_room)

    # create classes and their sessions
    gaming_class = gym.create_class("gaming", "play e sport")
    gaming_class.create_repeating_session(time(10,0,0),time(22,30,0),date(2026,11,3),7,10,5,multi_studio,gym_bro)

    yoga_class = gym.create_class("yoga", "stretchin dat bodae")
    yoga_class.create_repeating_session(time(10,0,0),time(11,30,0),date(2026,2,7),7,5,10,yoga_studio,gym_bro)

    bike_class = gym.create_class("bike", "workin on our leggies")
    eve_bike_sched = bike_class.create_session(time(15,30,0),time(16,30,0),date.today()+timedelta(days=1),3,multi_studio,gym_bro)
    night_bike_sched = bike_class.create_session(time(18,0,0),time(19,30,0),date.today(),5,multi_studio,gym_bro)

    # create memberships
    bob_membership = gym.create_member("123456789", "Bobda builder", date(2007, 8, 8), status="Active")
    studa_membership = gym.create_member("498453155", "Studa Hardent", date(1998, 3, 28), membership="Student", status="Active")
    richie_membership = gym.create_member("987456154", "Richie Guyant", date(2006, 10, 2), membership="Annual", status="Active")

    # simulate some transactions and stuff so have stuff to show in report

    # 1. Enroll members in sessions (using the session ids from the classes you made)
    gym.enroll_member_by_id(bob_membership.member_id, eve_bike_sched.session_id)
    gym.enroll_member_by_id(studa_membership.member_id, night_bike_sched.session_id)
    gym.enroll_member_by_id(richie_membership.member_id, eve_bike_sched.session_id)

    # 2. Sell some products to members
    # PRD-001 = Energy drink, PRD-002 = Water, PRD-003 = Whey protein
    gym.sell_product("PRD-001", 2, bob_membership.member_id)
    gym.sell_product("PRD-002", 1, studa_membership.member_id)
    gym.sell_product("PRD-003", 1, richie_membership.member_id)
    
    # Sell product to a walk-in guest (no member_id)
    guest_product_order = gym.sell_product("PRD-001", 3)

    # 3. Approve a Daypass for a random guest
    daypass_order_id = gym.approve_daypass("1100229933", "Randy Guestman", date(2003, 5, 12))

    # 4. Reserve some lockers for members (e.g., Bob reserves a locker for 3 hours before his bike class)
    gym.reserve_locker(bob_membership.member_id, is_vip=False, start=datetime.combine(date.today(), time(14,0,0)), hours=3)
    gym.reserve_locker(richie_membership.member_id, is_vip=True, start=datetime.combine(date.today(), time(14,0,0)), hours=3)

    # 5. Pay for all pending orders using Credit Card so they show up as revenue in reports
    # We can iterate through the users/members to pay their pending orders
    for user in [bob_membership, studa_membership, richie_membership]:
        # Fetch the pending order for the member (assuming `get_pending_order` or similar exists, 
        # or we just grab their current active order. In your models, Members usually have a current order)
        try:
            # We fetch the current active/pending order ID for the member via the gym's method
            order = gym.get_order_by_member_id(user.member_id)
            if order and order.status == "Pending":
                gym.pay_order_credit_card(1234567890123456, 123, "12/26", order.order_id)
        except Exception:
            pass # Order might already be paid or not exist

    # Pay for the guest's product order and daypass
    try:
        gym.pay_order_credit_card(9876543210987654, 321, "11/27", guest_product_order.order_id)
        gym.pay_order_credit_card(1111222233334444, 999, "01/25", daypass_order_id)
    except Exception:
        pass

    # 6. Simulate the trainer recording a training log for an enrolled session
    # We'll write a log for Bob in the evening bike schedule
    gym.record_session(
        session_id=eve_bike_sched.session_id, 
        training_log="Class completed successfully. High energy.", 
        member_training_log={bob_membership.member_id: "Bob did great, pedaled 25km."}
    )

    # 7. Testing Apply New Member (Correctly creates NewMembership Order items)
    new_monthly_id = gym.apply_new_member("Molly Monthly", "777777777", date(2002, 1, 1), "Monthly")
    new_annual_id = gym.apply_new_member("Annie Annual", "888888888", date(1999, 5, 5), "Annual")
    new_student_id = gym.apply_new_member("Stu Student", "999999999", date(2005, 9, 9), "Student")

    # 8. Testing Change Membership
    # Bob (who was directly created above without an order) now upgrades to Annual
    gym.change_membership(bob_membership.member_id, "Annual")

    # 9. Process Payments for Memberships
    # Pay for the three brand new members
    for new_id in [new_monthly_id, new_annual_id, new_student_id]:
        # get_order_by_member_id will fetch the Pending order created by apply_new_member
        order = gym.get_order_by_member_id(new_id)
        if order and order.status == "Pending":
            gym.pay_order_credit_card(1234567890123456, 123, "12/26", order.order_id)

    # Pay Bob's new order for upgrading to Annual
    bob_upgrade_order = gym.get_order_by_member_id(bob_membership.member_id)
    if bob_upgrade_order and bob_upgrade_order.status == "Pending":
        gym.pay_order_credit_card(1234567890123456, 123, "12/26", bob_upgrade_order.order_id)

    gym_bro.write_training_plan(night_bike_sched, "we'll be biking for 30 km")
    gym_bro.write_training_plan(bob_membership, "focus on training the lower leg area")

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


def run_api():
    app = FastAPI()

    @app.get("/")
    def home():
        return {"status": "Server is up!"}

    app.include_router(member_router)
    app.include_router(trainer_router)
    app.include_router(receptionist_router)
    app.include_router(manager_router)

    mcp = FastApiMCP(app)
    mcp.mount()

    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

if __name__ == "__main__":
    create_stuff()
    # run_test()
    run_api()