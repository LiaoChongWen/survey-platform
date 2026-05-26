import json
from datetime import datetime
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path

from app.database import get_db
from app.models import Form

router = APIRouter()
BASE_DIR = Path(__file__).parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@router.get("/form/{form_id}", response_class=HTMLResponse)
def fill_form(form_id: str, request: Request, db: Session = Depends(get_db)):
    form = db.query(Form).filter(Form.form_id == form_id).first()
    if not form:
        return templates.TemplateResponse(request, "student/not_found.html", {})

    now = datetime.utcnow()
    error = None
    if form.status == "draft":
        error = "此問卷尚未開放填答。"
    elif form.status == "closed":
        error = "此問卷已關閉，無法填答。"
    elif form.start_time and now < form.start_time:
        error = f"此問卷將於 {form.start_time.strftime('%Y-%m-%d %H:%M')} 開放。"
    elif form.end_time and now > form.end_time:
        error = "此問卷已過截止時間。"

    questions = []
    for q in form.questions:
        questions.append({
            "question_id": q.question_id,
            "question_type": q.question_type,
            "question_group": q.question_group,
            "question_text": q.question_text,
            "options": json.loads(q.options or "[]"),
            "required": q.required,
            "order_index": q.order_index,
        })

    return templates.TemplateResponse(request, "student/fill_form.html", {
        "form": form,
        "questions": questions,
        "questions_json": json.dumps(questions, ensure_ascii=False),
        "error": error,
    })


@router.get("/form/{form_id}/complete", response_class=HTMLResponse)
def form_complete(form_id: str, request: Request, db: Session = Depends(get_db)):
    form = db.query(Form).filter(Form.form_id == form_id).first()
    score = request.query_params.get("score")
    return templates.TemplateResponse(request, "student/complete.html", {
        "form": form,
        "score": score,
    })
