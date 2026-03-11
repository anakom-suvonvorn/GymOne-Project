from logging import Manager

from fastapi import  APIRouter, Depends, HTTPException
from database import get_gym
from pydantic import BaseModel
from typing import Literal, Optional

router = APIRouter(
    prefix="/manager",
    tags=["Manager"]
)

# NOTE: this whole file is just mainly for structure and knowing what to do
# We can change the function call name or how it works inside or however we like it to be

@router.get("/getreport", description="Get a report of the gym's performance for a specific month and year") #############
def get_report(month: int, year: int, gym = Depends(get_gym)):
    try:
        report = gym.gather_report(month, year)
        return {
            "report": report,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.get("/checkroom/{room_id}",description = "Manager checks room info by room_id (e.g. R-001). Requires staff_id as query parameter")
def check_room(room_id: str, staff_id: str, gym = Depends(get_gym)):
    try:
        manager = gym.get_manager_by_id(staff_id)
        result = manager.check_room(room_id)
        return {
            "result": result,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
# @router.get("/viewrulebreaks", description="View all rule breaks in the gym")
# def view_rule_breaks(gym = Depends(get_gym)):
#     try:
#         violations = gym.view_rule_breaks() # list of booking that is either no-show or late cancellation
#         return {
#             "violations": violations,
#         }
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))
    
# @router.post("/pardonbooking", description="use to tool to pardon a booking violation, includes ")
# def pardon_booking(body: dict, gym = Depends(get_gym)) -> dict:
#     try:
#         booking_id = body["booking_id"]
#         gym.pardon_booking(booking_id)
#         return {
#             "success": f"succesfully pardoned booking with id: {booking_id}"
#         }
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/product/add", description = "Manager adds stock to a product by product_id (e.g. PRD-001). Requires staff_id, product_id, and amount") #################
def add_stock(body: dict, gym = Depends(get_gym)) -> dict:
    try:
        staff_id = body["staff_id"]
        product_id = body["product_id"]
        amount = body["amount"]
        manager = gym.get_manager_by_id(staff_id)
        final_amount = manager.add_stock(product_id, amount)
        return {
            "success": f"succesfully added stock to product_id: {product_id} final amount: {final_amount}"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/product/remove", description = "Manager removes stock to a product by product_id (e.g. PRD-001). Requires staff_id, product_id, and amount") ####################
def remove_stock(body: dict, gym = Depends(get_gym)) -> dict:
    try:
        staff_id = body["staff_id"]
        product_id = body["product_id"]
        amount = body["amount"]
        manager = gym.get_manager_by_id(staff_id)
        final_amount = manager.remove_stock(product_id, amount)
        return {
            "success": f"succesfully removed stock of product_id: {product_id} final amount: {final_amount}"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/setmemberstatus", description="Manager sets member status. Valid statuses Active, Suspended, Frozen, Expired require member_id, staff_id, status")
def set_member_status(body: dict, gym = Depends(get_gym)) -> dict:
    try:
        staff_id = body["staff_id"]
        member_id = body["member_id"]
        status = body["status"]
        manager = gym.get_manager_by_id(staff_id)
        manager.set_membership_status(member_id, status)
        return {"success": f"{member_id} status has been succesfully set to {status}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# TODO: create class and session (which also assigns a room and trainer to it), cancel session

@router.get("/getstockinfo", description="Get the current stock of all products in the gym")
def get_stock_info(gym = Depends(get_gym)):
    try:
        stock = gym.get_stock_info()
        return {
            "stock": stock,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.get("/getstaffinfo", description="Get info of all staff in the gym")
def get_staff_info(gym = Depends(get_gym)):
    try:
        staff = gym.get_staff_info()
        return {
            "staff": staff,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
