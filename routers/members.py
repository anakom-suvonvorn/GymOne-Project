from fastapi import  APIRouter, Depends, HTTPException
from database import get_gym

router = APIRouter(
    prefix="/member",
    tags=["Member"],
)

# NOTE: this whole file is just mainly for structure and knowing what to do
# We can change the function call name or how it works inside or however we like it to be

@router.get("/showclass")
def show_available_classes(gym = Depends(get_gym)):
    classes = gym.get_available_classes()
    return {
        "classes": classes,
    }

@router.get("/showprivate")
def show_available_private_sessions(gym = Depends(get_gym)):
    private_sessions = gym.get_available_private_sessions()
    return {
        "private_sessions": private_sessions,
    }

@router.get("/notifications/{member_id}")
def show_notifications(member_id: str, gym = Depends(get_gym)):
    try:
        member = gym.get_member_by_id(member_id)
        notifications = member.get_notifications()
        return {
            "notifications": notifications,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.get("/showbooking/{member_id}")
def show_current_bookings(member_id: str, gym = Depends(get_gym)):
    try:
        member = gym.get_member_by_id(member_id)
        bookings = member.get_current_bookings()
        return {
            "bookings": bookings,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.get("/checkselfinfo/{member_id}")
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

@router.post("/enrollsession")
def enroll_session(body: dict, gym = Depends(get_gym)) -> dict:
    try:
        member_id = body["member_id"]
        session_id = body["session_id"]
        is_private_room = body["is_private_room"]
        gym.enroll_member_by_id(member_id, session_id, is_private_room)
        return {"success": f"{member_id} has been succesfully enrolled into session with session_id: {session_id}. please confirm booking by paying"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/cancelbooking")
def cancel_booking(body: dict, gym = Depends(get_gym)) -> dict:
    try:
        booking_id = body["booking_id"]
        result = gym.cancel_booking_by_id(booking_id)
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
    
