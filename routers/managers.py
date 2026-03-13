from fastapi import  APIRouter, Depends, HTTPException
from database import get_gym
from pydantic import BaseModel
from typing import Literal, Optional
from datetime import datetime, date, time, timedelta

router = APIRouter(
    prefix="/manager",
    tags=["Manager"]
)

@router.get("/getreport", description="Get a report of the gym's performance for a specific month and year") #############
def get_report(month: int, year: int, gym = Depends(get_gym)):
    try:
        report = gym.gather_report(month, year)
        return {
            "report": report,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.get("/getroominfo",description = "Manager gets info of all the rooms. Requires staff_id as query parameter") #############
def get_room_info(staff_id: str, gym = Depends(get_gym)):
    try:
        manager = gym.get_manager_by_id(staff_id)
        result = manager.get_room_info()
        return {
            "result": result,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.get("/getstockinfo", description="Get the current stock of all products in the gym") #############
def get_stock_info(gym = Depends(get_gym)):
    try:
        stock = gym.get_stock_info()
        return {
            "stock": stock,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.get("/getstaffinfo", description="Get info of all staff in the gym") #############
def get_staff_info(gym = Depends(get_gym)):
    try:
        staff = gym.get_staff_info()
        return {
            "staff": staff,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
class StockRequest(BaseModel):
    staff_id: str
    product_id: str
    amount: int
    
@router.post("/product/add", description = "Manager adds stock to a product by product_id (e.g. PRD-001). Requires staff_id, product_id, and amount") #################
def add_stock(request: StockRequest, gym = Depends(get_gym)) -> dict:
    try:
        manager = gym.get_manager_by_id(request.staff_id)
        final_amount = manager.add_stock(request.product_id, request.amount)
        return {
            "success": f"succesfully added stock to product_id: {request.product_id} final amount: {final_amount}"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/product/remove", description = "Manager removes stock to a product by product_id (e.g. PRD-001). Requires staff_id, product_id, and amount") ####################
def remove_stock(request: StockRequest, gym = Depends(get_gym)) -> dict:
    try:
        manager = gym.get_manager_by_id(request.staff_id)
        final_amount = manager.remove_stock(request.product_id, request.amount)
        return {
            "success": f"succesfully removed stock of product_id: {request.product_id} final amount: {final_amount}"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
class SetMemberStatusRequest(BaseModel):
    staff_id: str
    member_id: str
    status: Literal["Active", "Suspended", "Frozen", "Expired"]
    
@router.post("/setmemberstatus", description="Manager sets member status. Require member_id, staff_id, status") #############
def set_member_status(request: SetMemberStatusRequest, gym = Depends(get_gym)) -> dict:
    try:
        manager = gym.get_manager_by_id(request.staff_id)
        manager.set_membership_status(request.member_id, request.status)
        return {"success": f"{request.member_id} status has been succesfully set to {request.status}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class AddReceptionistRequest(BaseModel):
    citizen_id: str
    name: str
    birth_date: date

@router.post("/addreceptionist", description="Add a receptionist to the gym") #############
def add_receptionist(request: AddReceptionistRequest, gym = Depends(get_gym)):
    try:
        citizen_id = request.citizen_id
        name = request.name
        birth_date = request.birth_date
        receptionist = gym.create_receptionist(citizen_id, name, birth_date)
        return {
            "success": f"succesfully added receptionist with id: {receptionist.staff_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
class AddTrainerRequest(BaseModel):
    citizen_id: str
    name: str
    birth_date: date
    tier: Literal["Junior", "Senior", "Master"]
    specialization: str

@router.post("/addtrainer", description="Add a trainer to the gym") #############
def add_trainer(request: AddTrainerRequest, gym = Depends(get_gym)):
    try:
        citizen_id = request.citizen_id
        name = request.name
        birth_date = request.birth_date
        tier = request.tier
        specialization = request.specialization
        trainer = gym.create_trainer(citizen_id, name, birth_date, tier, specialization)
        return {
            "success": f"succesfully added trainer with id: {trainer.staff_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
# TODO: create class and session (which also assigns a room and trainer to it), show notifications > might not need to do this one

