from fastapi import  APIRouter, Depends, HTTPException
from main import get_gym

router = APIRouter(
    prefix="/manager",
    tags=["Manager"]
)

