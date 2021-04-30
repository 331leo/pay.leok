import os
import aiohttp
from typing import Optional
from fastapi import APIRouter, Request, exceptions, status, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates


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

templates = Jinja2Templates(directory="templates")

security = HTTPBasic()


@router.on_event("startup")
async def on_startup():
    await create_index()


@router.post("/PlaceOrder")
async def route_placeorder(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(security),
    orderId: str = Form(None),
    ordername: str = Form(None),
    description: str = Form(None),
    price: int = Form(None),
    customer: str = Form(None),
    email: Optional[str] = Form(None),
    specialcallback: Optional[str] = Form(None),
    aftercomplete: Optional[str] = Form("/"),
    htmlresponse: Optional[str] = Form("False"),
):
    if htmlresponse == "True":
        htmlresponse = True
    else:
        htmlresponse = False

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
            "email": email,
            "specialcallback": specialcallback,
            "aftercomplete": aftercomplete,
        }
        await insert_order_data(payload)
        if htmlresponse:
            return templates.TemplateResponse(
                "notify.html.j2",
                {
                    "request": request,
                    "data": payload,
                    "swal_title": "주문번호 생성이 완료되었습니다!",
                    "footer": f"주문번호: {orderId}",
                },
            )
        else:
            payload.update({"_id": None})
            return payload

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

                if order_data.get("specialcallback", None):
                    json.update(
                        {"auth": os.environ.get("PSTP-ADMIN-PASSWORD"), "_id": None}
                    )
                    async with session.post(
                        order_data.get("specialcallback", None), data=json
                    ):
                        await res.json()
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
