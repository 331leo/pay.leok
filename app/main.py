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


app.include_router(router, prefix="/test")