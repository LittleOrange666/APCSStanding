from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from modules.constants import ContestRes, allows
from modules.utils import StandingCache


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.cache = StandingCache()
    await app.state.cache.init()
    yield

app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/contest/{name}", response_model=ContestRes)
async def data(name: str):
    res = await app.state.cache.ask_data(name)
    if res is None:
        return {"error": "not found"}, 404
    return res

@app.get("/contests")
async def get_contest_list():
    return {"contests": list(allows.keys())}

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
    )