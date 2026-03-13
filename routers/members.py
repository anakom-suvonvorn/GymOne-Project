from fastapi import  APIRouter, Depends, HTTPException
from database import get_gym
from pydantic import BaseModel
from typing import Literal, Optional

router = APIRouter(
    prefix="/member",
    tags=["Member"],
)

@router.get("/showclass", description="Show all available classes and their sessions that is not full and has not passed yet") ########
def show_available_classes(gym = Depends(get_gym)):
    classes = gym.get_available_classes()
    return {
        "classes": classes,
    }

@router.get("/showprivate", description="Show all available trainers and their sessions that is not full and has not passed yet") #########
def show_available_private_sessions(gym = Depends(get_gym)):
    private_sessions = gym.get_available_private_sessions()
    return {
        "private_sessions": private_sessions,
    }

@router.get("/notifications/{member_id}", description="Show notifications for a specific member") #########
def show_notifications(member_id: str, gym = Depends(get_gym)):
    try:
        member = gym.get_member_by_id(member_id)
        notifications = member.show_notifications()
        return {
            "notifications": notifications,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.get("/showbooking/{member_id}", description="Show current bookings for a specific member") ###########
def show_current_bookings(member_id: str, gym = Depends(get_gym)):
    try:
        member = gym.get_member_by_id(member_id)
        bookings = member.get_current_bookings()
        return {
            "bookings": bookings,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.get("/showorder/{member_id}", description="Show current orders for a specific member") ##########
def show_current_orders(member_id: str, gym = Depends(get_gym)):
    try:
        member = gym.get_member_by_id(member_id)
        return {
            "orders": member.order_info
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/checkselfinfo/{member_id}", description="Show information about the specific member") ##########
def check_self_info(member_id: str, gym = Depends(get_gym)):
    try:
        member = gym.get_member_by_id(member_id)
        result = member.check_self_info()
        return result
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
    
class EnrollSessionRequest(BaseModel):
    member_id: str
    session_id: str

@router.post("/enrollsession", description="Enroll member into a session") ############
def enroll_session(request: EnrollSessionRequest, gym = Depends(get_gym)) -> dict:
    try:
        gym.enroll_member_by_id(request.member_id, request.session_id)
        return {"success": f"{request.member_id} has been succesfully enrolled into session with session_id: {request.session_id}. please confirm booking by paying"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
class CancelBookingRequest(BaseModel):
    booking_id: str
    
@router.post("/cancelbooking", description="Cancels a TrainingBooking") ############
def cancel_booking(request: CancelBookingRequest, gym = Depends(get_gym)) -> dict:
    try:
        result = gym.cancel_booking(request.booking_id)
        return {
            "success": f"succesfully cancelled booking with booking_id: {request.booking_id} with result",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class PayOrderCreditCardRequest(BaseModel):
    order_id: str
    card_num: int
    cvv: int
    expiry: str

@router.post("/pay_order/creditcard", description="Pay for an order using a credit card [ONLINE ACTION]") ############
def pay_order_credit_card(request: PayOrderCreditCardRequest, gym = Depends(get_gym)) -> dict:
    try:
        result = gym.pay_order_credit_card(request.card_num, request.cvv, request.expiry, request.order_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
class PayOrderQR(BaseModel):
    order_id: str

@router.post("/pay_order/qr", description="Create a qr code to pay [ONLINE ACTION]") ############
def pay_order_qr(request: PayOrderQR, gym = Depends(get_gym)) -> dict:
    try:
        result = gym.pay_order_qr(request.order_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/pay_order/qr/validate", description="Check payment state of qr code [ONLINE ACTION]") ############
def pay_order_qr(request: PayOrderQR, gym = Depends(get_gym)) -> dict:
    try:
        result = gym.validate_pay_order_qr(request.order_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
