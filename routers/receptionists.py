from fastapi import  APIRouter, Depends, HTTPException
from main import get_gym

router = APIRouter(
    prefix="/receptionist",
    tags=["Receptionist"]
)

@router.post("/showsession")
def show_session(gym = Depends(get_gym)):
    
    return {
        # "classes": classes,
    }