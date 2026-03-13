from fastapi import  APIRouter, Depends, HTTPException
from database import get_gym
from pydantic import BaseModel, Field, model_validator
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
    
class CreateClassRequest(BaseModel):
    name: str
    detail: str

@router.post("/createclass", description="Create a new class") #############
def create_class(request: CreateClassRequest, gym = Depends(get_gym)):
    try:
        new_class = gym.create_class(request.name, request.detail)
        return {
            "success": f"succesfully created a new class named: {new_class.name} with class_id: {new_class.class_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
class CreateClassSessionRequest(BaseModel):
    class_id: str
    room_id: str
    start_time: time
    end_time: time
    session_date: date = Field(
        description="is the date of the session for a singular session, or the start date of for a repeating session"
    )
    max_participants: int
    staff_id: str = Field(
        description="staff_id of a Trainer"
    )
    is_repeating: bool
    days_interval: Optional[int] = None
    times: Optional[int] = None

    @model_validator(mode='after')
    def validate_repeating_logic(self):
        if self.is_repeating:
            if self.days_interval is None or self.times is None:
                raise ValueError("If 'is_repeating' is True, you must provide both 'days_interval' and 'times'.")
        else:
            if self.days_interval is not None or self.times is not None:
                raise ValueError("If 'is_repeating' is False, 'days_interval' and 'times' should not be provided.")
        return self

@router.post("/createsession/class", description="Create a new session for a class") #############
def create_class_session(request: CreateClassSessionRequest, gym = Depends(get_gym)):
    try:
        gym_class = gym.get_class_by_id(request.class_id)
        room = gym.get_room_by_id(request.room_id)
        staff = gym.get_staff_by_id(request.staff_id)
        if request.is_repeating:
            gym_class.create_repeating_session(request.start_time,request.end_time,request.session_date,request.days_interval,request.times,request.max_participants,room,staff)
        else:
            new_session = gym_class.create_session(request.start_time,request.end_time,request.session_date,request.max_participants,room,staff)
        return {
            "success": f"succesfully created a new session",
            "session(s)_info": new_session.info if not request.is_repeating else gym_class.info
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
class CreateTrainerSessionRequest(BaseModel):
    room_id: str
    start_time: time
    end_time: time
    session_date: date = Field(
        description="is the date of the session for a singular session, or the start date of for a repeating session"
    )
    max_participants: int
    staff_id: str = Field(
        description="staff_id of a Trainer"
    )
    is_repeating: bool
    days_interval: Optional[int] = None
    times: Optional[int] = None

    @model_validator(mode='after')
    def validate_repeating_logic(self):
        if self.is_repeating:
            if self.days_interval is None or self.times is None:
                raise ValueError("If 'is_repeating' is True, you must provide both 'days_interval' and 'times'.")
        else:
            if self.days_interval is not None or self.times is not None:
                raise ValueError("If 'is_repeating' is False, 'days_interval' and 'times' should not be provided.")
        return self

@router.post("/createsession/trainer", description="Create a new session for a trainer") #############
def create_trainer_session(request: CreateTrainerSessionRequest, gym = Depends(get_gym)):
    try:
        room = gym.get_room_by_id(request.room_id)
        staff = gym.get_staff_by_id(request.staff_id)
        if request.is_repeating:
            staff.create_repeating_session(request.start_time,request.end_time,request.session_date,request.days_interval,request.times,request.max_participants,room)
        else:
            new_session = staff.create_session(request.start_time,request.end_time,request.session_date,request.max_participants,room)
        return {
            "success": f"succesfully created a new session",
            "session(s)_info": new_session.info if not request.is_repeating else staff.session_info
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))