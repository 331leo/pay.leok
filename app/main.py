import os
from fastapi import FastAPI, Request, Depends, status
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from bson import ObjectId
from utils import database
from routes import router_api


app = FastAPI(title="PayService_TP")

templates = Jinja2Templates(directory="templates")

security = HTTPBasic()


@app.get("/")
async def route_root(request: Request):
    return {"ok": "OK"}


@app.get("/pay", response_class=HTMLResponse)
async def route_pay(request: Request):
    return templates.TemplateResponse(
        "pay.html.j2",
        {"request": request, "toss_ck": os.environ.get("PSTP-TOSS-CLIENT")},
    )


@app.get("/generate", response_class=JSONResponse)
async def route_generate(
    request: Request, credentials: HTTPBasicCredentials = Depends(security)
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
    return templates.TemplateResponse("generate.html.j2", {"request": request})


@app.get("/paid/{objId}", response_class=HTMLResponse)
async def route_paid(request: Request, objId: str):
    try:
        data = await database.get_paid_data({"_id": ObjectId(objId)})
    except:
        data = None
    return templates.TemplateResponse(
        "notify.html.j2",
        {
            "request": request,
            "data": data,
            "swal_title": "결제가 완료되었습니다!",
            "footer": "감사합니다.",
        },
    )


@app.get("/pay/{orderId}", response_class=HTMLResponse)
async def route_pay_with_ordernum(request: Request, orderId: str):
    return templates.TemplateResponse(
        "pay.html.j2",
        {
            "request": request,
            "toss_ck": os.environ.get("PSTP-TOSS-CLIENT"),
            "orderId": orderId,
        },
    )


app.include_router(router_api, prefix="/api")
