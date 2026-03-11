from fastapi import  APIRouter, Depends, HTTPException
from database import get_gym
from pydantic import BaseModel
from typing import Literal, Optional

router = APIRouter(
    prefix="/receptionist",
    tags=["Receptionist"]
)

# NOTE: this whole file is just mainly for structure and knowing what to do
# We can change the function call name or how it works inside or however we like it to be

class ApproveDayPassRequest(BaseModel):
    name: str
    citizen_id: str
    birth_date: str

@router.post("/approvedaypass", description="Approve a daypass application for guest") ############
def approve_daypass(request: ApproveDayPassRequest, gym = Depends(get_gym)) -> dict:
    try:
        name = request.name
        citizen_id = request.citizen_id
        birth_date = request.birth_date
        guess_id = gym.approve_daypass(name, citizen_id, birth_date) # NOTE: in reality this is like giving the receptionist your card in exchange for the gym card
        return {
            "success": f"Daypass for {name} has been approved. Please pay to receive your daypass",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
class CheckInGuestRequest(BaseModel):
    guest_id: str

@router.post("/checkinmember", description="Check in a member when they arrive at the gym") ############
def check_in_member(request: CheckInGuestRequest, gym = Depends(get_gym)) -> dict:
    try:
        member_id = request.member_id
        result = gym.check_in_member(member_id)
        return {
            "success": f"Check in successful",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
class ReserveLockerRequest(BaseModel):
    member_id: str
    is_vip: bool 

@router.post("/applynewmember", description="Apply for a new membership") #############
def apply_new_member(request: ReserveLockerRequest, gym = Depends(get_gym)) -> dict:
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
    new_membership_type: str

@router.post("/changemembership", description="Change the membership type of a member") ###############
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
    
class SellProductRequest(BaseModel):
    product_id: str
    amount: int

@router.post("/sellproduct", description="Sell a product to a customer") ###########
def sell_product(request: SellProductRequest, gym = Depends(get_gym)) -> dict:
    try:
        product_id = request.product_id
        amount = request.amount
        gym.sell_product(product_id, amount)
        return {
            "success": f"added product_id: {product_id} to order list"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
class ReserveLockerRequest(BaseModel):
    member_id: str
    is_vip: bool

@router.post("/reservelocker", description="Reserve a locker for customer") ###########
def reserve_locker(request: ReserveLockerRequest, gym = Depends(get_gym)) -> dict:
    try:
        member_id = request.member_id
        is_vip = request.is_vip
        result = gym.reserve_locker(member_id, is_vip)
        return {
            "success": f"added locker booking to order list."
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
# NOTE: a lot of the above function will result in something that is pending > can be paid/confirmed by paying
# onsite payments (cash, creditcard, qr)

class PayOrderCashRequest(BaseModel):
    member_id: str

@router.post("/payorder/cash", description="Pay for an order using cash")
def pay_order_cash(request: PayOrderCashRequest, gym = Depends(get_gym)) -> dict:
    try:
        member_id = request.member_id
        member = gym.get_member_by_id(member_id)
        transaction_id, total, items = gym.pay_order_cash(member) # NOTE: might be member_id or guest_id or order_id to reference the order instead, needs looking into
        return {
            "success": f"{member.name} has succesfully payed a total of {total} with these items",
            "items": [f"{item}" for item in items],
            "transaction_id": transaction_id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
class PayOrderCreditCardRequest(BaseModel):
    member_id: str
    card_num: str
    cvv: str
    expiry: str

@router.post("/payorder/creditcard", description="Pay for an order using a credit card")
def pay_order_credit_card(request: PayOrderCreditCardRequest, gym = Depends(get_gym)) -> dict:
    try:
        member_id = request.member_id
        member = gym.get_member_by_id(member_id)
        card_num = request.card_num
        cvv = request.cvv
        expiry = request.expiry
        transaction_id, total, items = gym.pay_order_credit_card(member, card_num, cvv, expiry) # NOTE: might be member_id or guest_id or order_id to reference the order instead, needs looking into
        return {
            "success": f"{member.name} has succesfully payed a total of {total} with these items",
            "items": [f"{item}" for item in items],
            "transaction_id": transaction_id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
class PayOrderQRRequest(BaseModel):
    member_id: str
    order_id: str 

@router.post("/payorder/qr", description="Pay for an order using a QR code")
def pay_order_qr(request: PayOrderQRRequest, gym = Depends(get_gym)) -> dict:
    try:
        member_id = request.member_id
        order_id = request.order_id
        member = gym.get_member_by_id(member_id)
        transaction_id, total, items = gym.pay_order_qr(member, order_id) # NOTE: might be member_id or guest_id or order_id to reference the order instead, needs looking into
        return {
            "success": f"{member.name} has succesfully payed a total of {total} with these items",
            "items": [f"{item}" for item in items],
            "transaction_id": transaction_id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))