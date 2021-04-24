from typing import Optional
from fastapi import APIRouter
from utils.database import get_order_data, insert_order_data

router = APIRouter()
