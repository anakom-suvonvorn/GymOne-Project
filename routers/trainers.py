from fastapi import  APIRouter, Depends, HTTPException
from database import get_gym
from pydantic import BaseModel
from typing import Literal, Optional

router = APIRouter(
    prefix="/trainer",
    tags=["Trainer"]
)

# NOTE: this whole file is just mainly for structure and knowing what to do
# We can change the function call name or how it works inside or however we like it to be

@router.get("/notifications/{staff_id}")
def show_notifications(staff_id: str, gym = Depends(get_gym)):
    try:
        staff = gym.get_staff_by_id(staff_id)
        notifications = staff.get_notifications()
        return {
            "notifications": notifications,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/cancelsession")
def cancel_session(body: dict, gym = Depends(get_gym)) -> dict:
    try:
        session_id = body["session_id"]
        result = gym.cancel_session_by_id(session_id)
        return {
            "success": f"succesfully cancelled session with session_id: {session_id} with result",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/recordsession")
def record_session(body: dict, gym = Depends(get_gym)) -> dict:
    try:
        session_id = body["session_id"]
        training_log = body["training_log"] # is just a string > log of the whole sessions
        member_training_log = body["member_training_log"] # is {member_id:training_log} > for specific member
        gym.record_session(session_id, training_log, member_training_log)
        return {
            "success": f"succesfully recorded the session"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/recordsession")
def record_session(body: dict, gym = Depends(get_gym)) -> dict:
    try:
        session_id = body["session_id"]
        training_log = body["training_log"] # is just a string > log of the whole sessions
        member_training_log = body["member_training_log"] # is {member_id:training_log} > for specific member
        gym.record_session(session_id, training_log, member_training_log)
        return {
            "success": f"succesfully recorded the session"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
# TODO: write training/workout plan of session and member