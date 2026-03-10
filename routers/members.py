from fastapi import  APIRouter, Depends, HTTPException
from main import get_gym

router = APIRouter(
    prefix="/member",
    tags=["Member"]
)

@router.get("/showclass")
def show_available_classes(gym = Depends(get_gym)):
    classes = gym.get_available_classes()
    return {
        "classes": classes,
    }
    
@router.get("/showbooking")
def show_current_bookings(gym = Depends(get_gym)):
    # bookings = bob_membership.get_current_bookings()
    # needs to search the member with id first
    return {
        # "bookings": bookings,
    }

@router.post("/enrollclass/{session_id}")
def enroll_class(session_id: str, body: dict, gym = Depends(get_gym)) -> dict:
    try:
        member_id = body["member_id"]
        gym.enroll_member_by_id(member_id, session_id)
        return {"success": f"{member_id} has been succesfully enrolled into class with session_id: {session_id}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/pay_bookings")
def pay_bookings(body: dict, gym = Depends(get_gym)) -> dict:
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