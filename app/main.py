import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from utils import database
from routes import router


app = FastAPI(title="PayService_TP")

templates = Jinja2Templates(directory="templates")


@app.get("/")
async def route_root(request: Request):
    return {"ok": "OK"}

@app.get("/pay", response_class=HTMLResponse)
async def route_pay(request: Request):
    return templates.TemplateResponse("pay.html.j2", {"request": request, "toss_ck": os.environ.get("PSTP-TOSS-CLIENT")})

@app.get("/pay/{ordernum}", response_class=HTMLResponse)
async def route_pay_with_ordernum(request: Request,ordernum):
    return templates.TemplateResponse("pay.html.j2", {"request":request, "toss_ck": os.environ.get("PSTP-TOSS-CLIENT"), "ordernum": ordernum})
app.include_router(router, prefix="/test")