from fastapi import  APIRouter, Depends, HTTPException
from database import get_gym

router = APIRouter(
    prefix="/manager",
    tags=["Manager"]
)

# NOTE: this whole file is just mainly for structure and knowing what to do
# We can change the function call name or how it works inside or however we like it to be

@router.get("/getreport")
def get_report(gym = Depends(get_gym)):
    try:
        report = gym.get_report()
        return {
            "report": report,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.get("/checkroom/{room_id}")
def get_report(room_id: str, gym = Depends(get_gym)):
    try:
        result = gym.check_room(room_id)
        return {
            "result": result,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.get("/viewrulebreaks")
def view_rule_breaks(gym = Depends(get_gym)):
    try:
        violations = gym.view_rule_breaks() # list of booking that is either no-show or late cancellation
        return {
            "violations": violations,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/pardonbooking")
def pardon_booking(body: dict, gym = Depends(get_gym)) -> dict:
    try:
        booking_id = body["booking_id"]
        gym.pardon_booking(booking_id)
        return {
            "success": f"succesfully pardoned booking with id: {booking_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/product/add")
def add_stock(body: dict, gym = Depends(get_gym)) -> dict:
    try:
        product_id = body["product_id"]
        amount = body["amount"]
        final_amount = gym.add_stock(product_id, amount)
        return {
            "success": f"succesfully added stock to product_id: {product_id} final amount: {final_amount}"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/product/remove")
def remove_stock(body: dict, gym = Depends(get_gym)) -> dict:
    try:
        product_id = body["product_id"]
        amount = body["amount"]
        final_amount = gym.remove_stock(product_id, amount)
        return {
            "success": f"succesfully removed stock of product_id: {product_id} final amount: {final_amount}"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/setmemberstatus")
def set_member_status(body: dict, gym = Depends(get_gym)) -> dict:
    try:
        member_id = body["member_id"]
        status = body["status"]
        gym.set_membership_status(member_id, status)
        return {"success": f"{member_id} status has been succesfully set to {status}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))