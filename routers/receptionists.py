from fastapi import  APIRouter, Depends, HTTPException
from database import get_gym

router = APIRouter(
    prefix="/receptionist",
    tags=["Receptionist"]
)

# NOTE: this whole file is just mainly for structure and knowing what to do
# We can change the function call name or how it works inside or however we like it to be

@router.post("/approvedaypass")
def approve_daypass(body: dict, gym = Depends(get_gym)) -> dict:
    try:
        name = body["name"]
        citizen_id = body["citizen_id"]
        birth_date = body["birth_date"]
        guess_id = gym.approve_daypass(name, citizen_id, birth_date) # NOTE: in reality this is like giving the receptionist your card in exchange for the gym card
        return {
            "success": f"Daypass for {name} has been approved. Please pay to receive your daypass",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/checkinmember")
def check_in_member(body: dict, gym = Depends(get_gym)) -> dict:
    try:
        member_id = body["member_id"]
        result = gym.check_in_member(member_id)
        return {
            "success": f"Check in successful",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/applynewmember")
def apply_new_member(body: dict, gym = Depends(get_gym)) -> dict:
    try:
        name = body["name"]
        citizen_id = body["citizen_id"]
        birth_date = body["birth_date"]
        membership_type = body["membership_type"]
        result = gym.apply_new_member(name, citizen_id, birth_date, membership_type)
        return {
            "success": f"Successfully created new {membership_type} membership for {name}. Please pay to confirm application",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/changemembership")
def change_membership(body: dict, gym = Depends(get_gym)) -> dict:
    try:
        member_id = body["member_id"]
        new_membership_type = body["new_membership_type"]
        gym.change_memberhsip(member_id, new_membership_type) # NOTE: a lot of places ive written like this where we delegate gym to find it, but another way to do it is to gym.get_member_by_id right here, and call it directly here?
        return {
            "success": f"Success. Please pay to confirm application",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/sellproduct")
def sell_product(body: dict, gym = Depends(get_gym)) -> dict:
    try:
        product_id = body["product_id"]
        amount = body["amount"]
        gym.sell_product(product_id, amount)
        return {
            "success": f"added product_id: {product_id} to order list"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/reservelocker")
def reserve_locker(body: dict, gym = Depends(get_gym)) -> dict:
    try:
        member_id = body["member_id"]
        is_vip = body["is_vip"]
        result = gym.reserve_locker(member_id, is_vip)
        return {
            "success": f"added locker booking to order list."
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
# NOTE: a lot of the above function will result in something that is pending > can be paid/confirmed by paying
# onsite payments (cash, creditcard, qr)

@router.post("/payorder/cash")
def pay_order_cash(body: dict, gym = Depends(get_gym)) -> dict:
    try:
        member_id = body["member_id"]
        member = gym.get_member_by_id(member_id)
        transaction_id, total, items = gym.pay_order_cash(member) # NOTE: might be member_id or guest_id or order_id to reference the order instead, needs looking into
        return {
            "success": f"{member.name} has succesfully payed a total of {total} with these items",
            "items": [f"{item}" for item in items],
            "transaction_id": transaction_id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/payorder/creditcard")
def pay_order_credit_card(body: dict, gym = Depends(get_gym)) -> dict:
    try:
        member_id = body["member_id"]
        member = gym.get_member_by_id(member_id)
        card_num = body["card_num"]
        cvv = body["cvv"]
        expiry = body["expiry"]
        transaction_id, total, items = gym.pay_order_credit_card(member, card_num, cvv, expiry) # NOTE: might be member_id or guest_id or order_id to reference the order instead, needs looking into
        return {
            "success": f"{member.name} has succesfully payed a total of {total} with these items",
            "items": [f"{item}" for item in items],
            "transaction_id": transaction_id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/payorder/qr")
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