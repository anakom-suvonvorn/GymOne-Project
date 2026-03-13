from fastapi import  APIRouter, Depends, HTTPException
from database import get_gym
from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime, date, time, timedelta

router = APIRouter(
    prefix="/receptionist",
    tags=["Receptionist"]
)

class ApproveDayPassRequest(BaseModel):
    name: str
    citizen_id: str
    birth_date: date

@router.post("/approvedaypass", description="Approve a daypass application for member [ONSITE ACTION by receptionist: in person at reception]") ############
def approve_daypass(request: ApproveDayPassRequest, gym = Depends(get_gym)) -> dict:
    try:
        name = request.name
        citizen_id = request.citizen_id
        birth_date = request.birth_date
        member_id = gym.approve_daypass(name, citizen_id, birth_date) # NOTE: in reality this is like giving the receptionist your card in exchange for the gym card
        return {
            "success": f"Daypass for {name} has been approved. Please pay to receive your daypass",
            "member_id": member_id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
class MemberCheckInRequest(BaseModel):
    member_id: str

@router.post("/checkinmember", description="Check in a member when they arrive at the gym [ONSITE ACTION by receptionist: in person at reception]") ############
def check_in_member(request: MemberCheckInRequest, gym = Depends(get_gym)) -> dict:
    try:
        member_id = request.member_id
        check_in = gym.check_in_member(member_id)
        return {
            "success": f"Daypass application approved and checked in for member_id: {member_id}",
            "check_in": check_in
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
class ApplyNewMemberRequest(BaseModel):
    name: str
    citizen_id: str
    birth_date: date
    membership_type: Literal["Monthly", "Annual", "Student"]

@router.post("/applynewmember", description="Apply for a new membership [ONSITE ACTION by receptionist: in person at reception]") #############
def apply_new_member(request: ApplyNewMemberRequest, gym = Depends(get_gym)) -> dict:
    try:
        name = request.name
        citizen_id = request.citizen_id
        birth_date = request.birth_date
        membership_type = request.membership_type
        result = gym.apply_new_member(name, citizen_id, birth_date, membership_type)
        return {
            "success": f"Successfully created new {membership_type} membership for {name}. Please pay to confirm application",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
class ChangeMembershipRequest(BaseModel):
    member_id: str
    new_membership_type: Literal["Monthly", "Annual", "Student"]

@router.post("/changemembership", description="Change the membership type of a member [ONSITE ACTION by receptionist: in person at reception]") ###############
def change_membership(request: ChangeMembershipRequest, gym = Depends(get_gym)) -> dict:
    try:
        member_id = request.member_id
        new_membership_type = request.new_membership_type
        gym.change_membership(member_id, new_membership_type) # NOTE: a lot of places ive written like this where we delegate gym to find it, but another way to do it is to gym.get_member_by_id right here, and call it directly here?
        return {
            "success": f"Success. Please pay to confirm application",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.get("/getstockinfo", description="Get the current stock of all products in the gym") ###########
def get_stock_info(gym = Depends(get_gym)):
    try:
        stock = gym.get_stock_info()
        return {
            "stock": stock,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
class SellProductRequest(BaseModel):
    product_id: str
    amount: int
    member_id: str = None

@router.post("/sellproduct", description="Sell a product to a customer [ONSITE ACTION by receptionist: in person at reception]") ###########
def sell_product(request: SellProductRequest, gym = Depends(get_gym)) -> dict:
    try:
        gym.sell_product(request.product_id, request.amount, request.member_id)
        return {
            "success": f"added product_id: {request.product_id} to order list"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
class ReserveLockerRequest(BaseModel):
    member_id: str
    is_vip: bool
    start: datetime = Field(default_factory=datetime.now)
    hours: float = 2.0

@router.post("/reservelocker", description="Reserve a locker for customer [ONSITE ACTION by receptionist: in person at reception]") ###########
def reserve_locker(request: ReserveLockerRequest, gym = Depends(get_gym)) -> dict:
    try:
        result = gym.reserve_locker(request.member_id, request.is_vip, request.start, request.hours)
        return {
            "success": f"added locker booking to order list."
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
# NOTE: a lot of the above function will result in something that is pending > can be paid/confirmed by paying
# onsite payments (cash, creditcard, qr)

class PayOrderCashRequest(BaseModel):
    order_id: str

@router.post("/payorder/cash", description="Pay for an order using cash [ONSITE ACTION by receptionist: in person at reception]") ###########
def pay_order_cash(request: PayOrderCashRequest, gym = Depends(get_gym)) -> dict:
    try:
        order_id = request.order_id
        result = gym.pay_order_cash(order_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
class PayOrderCreditCardRequest(BaseModel):
    order_id: str
    card_num: int
    cvv: int
    expiry: str

@router.post("/pay_order/creditcard", description="Pay for an order using a credit card [ONSITE ACTION by receptionist: in person at reception]") ###########
def pay_order_credit_card(request: PayOrderCreditCardRequest, gym = Depends(get_gym)) -> dict:
    try:
        result = gym.pay_order_credit_card(request.card_num, request.cvv, request.expiry, request.order_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
class PayOrderQR(BaseModel):
    order_id: str

@router.post("/pay_order/qr", description="Create a qr code to pay [ONSITE ACTION by receptionist: in person at reception]") ###########
def pay_order_qr(request: PayOrderQR, gym = Depends(get_gym)) -> dict:
    try:
        result = gym.pay_order_qr(request.order_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/pay_order/qr/validate", description="Check payment state of qr code [ONSITE ACTION by receptionist: in person at reception]") ###########
def pay_order_qr(request: PayOrderQR, gym = Depends(get_gym)) -> dict:
    try:
        result = gym.validate_pay_order_qr(request.order_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
# TODO: notification to show all the bookings of today that going to need to checkin / optional can specify date