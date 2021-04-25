import os
import aiohttp
from typing import Optional
from fastapi import APIRouter, Request, exceptions, status, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from base64 import b64encode

from starlette.status import HTTP_404_NOT_FOUND
from utils.database import (
    get_order_data,
    insert_order_data,
    get_paid_data,
    insert_paid_data,
    create_index,
    delete_order_data,
)

router = APIRouter()

security = HTTPBasic()


@router.on_event("startup")
async def on_startup():
    await create_index()


@router.post("/PlaceOrder")
async def route_placeorder(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(security),
    orderId: str = Form("orderId"),
    ordername: str = Form("ordername"),
    description: str = Form("description"),
    price: int = Form("price"),
    customer: str = Form("customer"),
):
    if not (
        credentials.username == "admin"
        and credentials.password == os.environ.get("PSTP-ADMIN-PASSWORD")
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    try:
        payload = {
            "orderId": orderId,
            "title": ordername,
            "description": description,
            "price": price,
            "customer": customer,
        }
        await insert_order_data(payload)
        payload.pop("_id", None)
        return JSONResponse(
            payload, 200, headers={"content-type": "text/html; charset=UTF-8"}
        )
    except Exception as e:
        return JSONResponse(
            {"error": f"{e}"}, 500, headers={"content-type": "text/html; charset=UTF-8"}
        )


@router.post("/FindOrderData")
async def route_findorderdata(orderId: str = Form("orderId")):
    data = await get_order_data({"orderId": orderId})
    if data:
        data.pop("_id", None)
        return data
    else:
        return {"message": "Not Found"}


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
    assert order_data.get("price") == amount, "Price must be same between Toss and DB"
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
                await delete_order_data({"orderId": orderId})
                return RedirectResponse(f"/paid/{inserted_id}")
            else:
                return {
                    "status": json.get("status"),
                    "message": "알 수 없는 오류.",
                    "orderId": orderId,
                }


@router.get("/FailCallback")
async def route_failcallback(request: Request, code: str, message: str):
    return {"message": message}
