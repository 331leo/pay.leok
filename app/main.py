import os
from fastapi import FastAPI, Request, Depends
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials

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
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return {"username": credentials.username, "password": credentials.password}


@app.get("/pay/{orderId}", response_class=HTMLResponse)
async def route_pay_with_ordernum(request: Request, ordernum):
    return templates.TemplateResponse(
        "pay.html.j2",
        {
            "request": request,
            "toss_ck": os.environ.get("PSTP-TOSS-CLIENT"),
            "orderId": ordernum,
        },
    )


app.include_router(router_api, prefix="/api")
