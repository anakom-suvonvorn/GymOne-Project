from fastapi import  APIRouter, Depends, HTTPException
from main import get_gym

router = APIRouter(
    prefix="/trainer",
    tags=["Trainer"]
)

@router.post("/showsession")
def show_session(gym = Depends(get_gym)):
    
    return {
        # "classes": classes,
    }