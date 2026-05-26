from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Form as FastForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse
from datetime import timedelta
from pathlib import Path

from app.database import init_db
from app.auth import authenticate_admin, create_access_token, get_current_admin
from app.config import UPLOAD_DIR

from app.routers import admin, forms, responses, analytics, student

BASE_DIR = Path(__file__).parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    init_db()
    yield


app = FastAPI(title="問卷分析平台", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    user = get_current_admin(request)
    if user:
        return RedirectResponse("/admin/dashboard", status_code=302)
    return RedirectResponse("/admin/login", status_code=302)


@app.get("/admin/login", response_class=HTMLResponse)
def login_page(request: Request, error: str = ""):
    return templates.TemplateResponse(request, "admin/login.html", {"error": error})


@app.post("/admin/login")
async def login_submit(
    request: Request,
    username: str = FastForm(...),
    password: str = FastForm(...),
):
    if authenticate_admin(username, password):
        token = create_access_token({"sub": username}, timedelta(hours=8))
        response = RedirectResponse("/admin/dashboard", status_code=302)
        response.set_cookie("access_token", token, httponly=True, samesite="lax")
        return response
    return templates.TemplateResponse(
        request,
        "admin/login.html",
        {"error": "帳號或密碼錯誤"},
        status_code=401,
    )


@app.get("/admin/logout")
def logout():
    response = RedirectResponse("/admin/login", status_code=302)
    response.delete_cookie("access_token")
    return response


app.include_router(admin.router, prefix="/admin")
app.include_router(forms.router, prefix="/api/forms")
app.include_router(responses.router)
app.include_router(analytics.router, prefix="/api")
app.include_router(student.router)
