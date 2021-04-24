import os
import aiohttp
from typing import Optional
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, JSONResponse
from base64 import b64encode
from utils.database import (
    get_order_data,
    insert_order_data,
    get_paid_data,
    insert_paid_data,
    create_index,
)

router = APIRouter()


@router.on_event("startup")
async def on_startup():
    await create_index()


@router.get("/PayCallback")
async def route_paycallback(
    request: Request, paymentKey: str, orderId: str, amount: int
):
    order_data = await get_order_data({"orderId": orderId})
    order_data.pop("_id")
    toss_api_key = (
        "Basic " + b64encode(f"{os.environ.get('PSTP-TOSS-SECRET')}:".encode()).decode()
    )
    header = {"Authorization": toss_api_key, "Content-Type": "application/json"}
    data = {"orderId": orderId, "amount": amount}
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"https://api.tosspayments.com/v1/payments/{paymentKey}",
            headers=header,
            json=data,
        ) as res:
            json = await res.json()
            if json.get("status", None) == "DONE":
                json.update(order_data)
                inserted_id = str((await insert_paid_data(json)).inserted_id)
                return RedirectResponse(f"/paid?code={inserted_id}")
            else:
                return {
                    "status": json.get("status"),
                    "message": "알 수 없는 오류.",
                    "orderId": orderId,
                }


@router.get("/FailCallback")
async def route_failcallback(request: Request, code: str, message: str):
    return {"message": message}
