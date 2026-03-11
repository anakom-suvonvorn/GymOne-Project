from fastapi import  APIRouter, Depends, HTTPException
from database import get_gym
from pydantic import BaseModel
from typing import Literal, Optional

router = APIRouter(
    prefix="/member",
    tags=["Member"],
)

# NOTE: this whole file is just mainly for structure and knowing what to do
# We can change the function call name or how it works inside or however we like it to be

@router.get("/showclass") ########
def show_available_classes(gym = Depends(get_gym)):
    classes = gym.get_available_classes()
    return {
        "classes": classes,
    }

@router.get("/showprivate") #########
def show_available_private_sessions(gym = Depends(get_gym)):
    private_sessions = gym.get_available_private_sessions()
    return {
        "private_sessions": private_sessions,
    }

@router.get("/notifications/{member_id}") #########
def show_notifications(member_id: str, gym = Depends(get_gym)):
    try:
        member = gym.get_member_by_id(member_id)
        notifications = member.show_notifications()
        return {
            "notifications": notifications,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.get("/showbooking/{member_id}") ###########
def show_current_bookings(member_id: str, gym = Depends(get_gym)):
    try:
        member = gym.get_member_by_id(member_id)
        bookings = member.get_current_bookings()
        return {
            "bookings": bookings,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.get("/showorder/{member_id}") ##########
def show_current_orders(member_id: str, gym = Depends(get_gym)):
    try:
        member = gym.get_member_by_id(member_id)
        return {
            "orders": member.order_info
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/checkselfinfo/{member_id}") ##########
def check_self_info(member_id: str, gym = Depends(get_gym)):
    try:
        member = gym.get_member_by_id(member_id)
        training_plan, training_history = member.check_self_info()
        return {
            "training_plan": training_plan,
            "training_history": training_history
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
class ChangeMembershipRequest(BaseModel):
    member_id: str
    new_membership_type: Literal["Monthly", "Annual", "Student"]

@router.post("/changemembership", description="Change the membership type of a member, adds to order, needs to pay order to confirm") ###########
def change_membership(request: ChangeMembershipRequest, gym = Depends(get_gym)) -> dict:
    try:
        gym.change_membership(request.member_id, request.new_membership_type)
        return {
            "success": f"Success. Please pay order to confirm application",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/enrollsession") ############
def enroll_session(body: dict, gym = Depends(get_gym)) -> dict:
    try:
        member_id = body["member_id"]
        session_id = body["session_id"]
        gym.enroll_member_by_id(member_id, session_id)
        return {"success": f"{member_id} has been succesfully enrolled into session with session_id: {session_id}. please confirm booking by paying"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/cancelbooking")
def cancel_booking(body: dict, gym = Depends(get_gym)) -> dict:
    try:
        booking_id = body["booking_id"]
        result = gym.cancel_booking(booking_id)
        return {
            "success": f"succesfully cancelled booking with booking_id: {booking_id} with result",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
# NOTE: a lot of the above function will result in something that is pending > can be paid/confirmed by paying
# online payments (creditcard, qr)

@router.post("/pay_order/creditcard")
def pay_order_credit_card(body: dict, gym = Depends(get_gym)) -> dict:
    try:
        member_id = body.get("member_id") # use this
        order_id = body.get("order_id") # or this
        card_num = body["card_num"]
        cvv = body["cvv"]
        expiry = body["expiry"]
        transaction_id, total, items = gym.pay_order_credit_card(card_num, cvv, expiry, member_id, order_id) # NOTE: might be member_id or guest_id or order_id to reference the order instead, needs looking into
        return {
            "success": f"{member_id} has succesfully payed a total of {total} with these items",
            "items": [f"{item}" for item in items],
            "transaction_id": transaction_id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/pay_order/qr")
def pay_order_qr(body: dict, gym = Depends(get_gym)) -> dict:
    try:
        member_id = body["member_id"]
        member = gym.get_member_by_id(member_id)
        transaction_id, total, items = gym.pay_order_qr(member) # NOTE: might be member_id or guest_id or order_id to reference the order instead, needs looking into
        return {
            "success": f"{member.name} has succesfully payed a total of {total} with these items",
            "items": [f"{item}" for item in items],
            "transaction_id": transaction_id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
