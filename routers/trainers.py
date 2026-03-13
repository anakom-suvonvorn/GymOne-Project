from fastapi import  APIRouter, Depends, HTTPException
from database import get_gym
from pydantic import BaseModel, Field
from typing import Literal, Optional

router = APIRouter(
    prefix="/trainer",
    tags=["Trainer"]
)

@router.get("/notifications/{staff_id}", description="Show notifications for a specific staff") #############
def show_notifications(staff_id: str, gym = Depends(get_gym)):
    try:
        staff = gym.get_staff_by_id(staff_id)
        notifications = staff.show_notifications()
        return {
            "notifications": notifications,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
class CancelSessionRequest(BaseModel):
    session_id: str

@router.post("/cancelsession", description="Cancel a scheduled session") ###########
def cancel_session(request: CancelSessionRequest, gym = Depends(get_gym)) -> dict:
    try:
        session_id = request.session_id
        result = gym.cancel_session(session_id)
        return {
            "success": f"succesfully cancelled session with session_id: {session_id} with result",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
class RecordSessionRequest(BaseModel):
    session_id: str
    training_log: str = Field(
        description="The general log or notes for the entire session."
    )
    member_training_log: dict[str, str] = Field(
        default={}, 
        description="A dictionary mapping specific member IDs to their individual training logs. Key must be the member_id (str), and Value must be their specific training_log (str)."
    )

@router.post("/recordsession", description="Record the details of a completed session, including class training log and private training logs") #############
def record_session(request: RecordSessionRequest, gym = Depends(get_gym)) -> dict:
    try:
        gym.record_session(request.session_id, request.training_log, request.member_training_log)
        return {
            "success": f"succesfully recorded the session"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
# # TODO: write training/workout plan of session and member