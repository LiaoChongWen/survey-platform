import json
import io
import uuid
import base64
import qrcode
from datetime import datetime
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path

from app.database import get_db
from app.auth import admin_redirect, get_current_admin
from app.models import Form, Response as ResponseModel, Dataset, Question

router = APIRouter()
BASE_DIR = Path(__file__).parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _make_qr_base64(url: str) -> str:
    qr = qrcode.QRCode(box_size=8, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    redir = admin_redirect(request)
    if redir:
        return redir
    total_forms = db.query(Form).count()
    open_forms = db.query(Form).filter(Form.status == "open").count()
    total_responses = db.query(ResponseModel).count()
    recent_forms = db.query(Form).order_by(Form.created_at.desc()).limit(5).all()
    return templates.TemplateResponse(request, "admin/dashboard.html", {
        "total_forms": total_forms,
        "open_forms": open_forms,
        "total_responses": total_responses,
        "recent_forms": recent_forms,
    })


@router.get("/forms", response_class=HTMLResponse)
def forms_list(request: Request, db: Session = Depends(get_db)):
    redir = admin_redirect(request)
    if redir:
        return redir
    forms = db.query(Form).order_by(Form.created_at.desc()).all()
    return templates.TemplateResponse(request, "admin/forms_list.html", {
        "forms": forms,
    })


@router.get("/forms/create", response_class=HTMLResponse)
def form_create_page(request: Request, db: Session = Depends(get_db)):
    redir = admin_redirect(request)
    if redir:
        return redir
    form = Form(
        form_id=str(uuid.uuid4()),
        title="新問卷",
        description="",
        status="draft",
    )
    db.add(form)
    db.commit()
    return RedirectResponse(f"/admin/forms/{form.form_id}/edit", status_code=302)


@router.get("/forms/{form_id}/edit", response_class=HTMLResponse)
def form_edit_page(form_id: str, request: Request, db: Session = Depends(get_db)):
    redir = admin_redirect(request)
    if redir:
        return redir
    form = db.query(Form).filter(Form.form_id == form_id).first()
    if not form:
        return RedirectResponse("/admin/forms", status_code=302)
    questions = []
    for q in form.questions:
        questions.append({
            "question_id": q.question_id,
            "question_type": q.question_type,
            "question_group": q.question_group,
            "question_text": q.question_text,
            "options": json.loads(q.options or "[]"),
            "correct_answer": json.loads(q.correct_answer or "null"),
            "score": q.score,
            "required": q.required,
            "order_index": q.order_index,
            "explanation": q.explanation,
        })
    return templates.TemplateResponse(request, "admin/form_edit.html", {
        "form": form,
        "questions_json": json.dumps(questions, ensure_ascii=False),
    })


@router.get("/forms/{form_id}/qrcode", response_class=HTMLResponse)
def qrcode_page(form_id: str, request: Request, db: Session = Depends(get_db)):
    redir = admin_redirect(request)
    if redir:
        return redir
    form = db.query(Form).filter(Form.form_id == form_id).first()
    if not form:
        return RedirectResponse("/admin/forms", status_code=302)
    base_url = str(request.base_url).rstrip("/")
    form_url = f"{base_url}/form/{form_id}"
    qr_b64 = _make_qr_base64(form_url)
    return templates.TemplateResponse(request, "admin/qrcode_view.html", {
        "form": form,
        "form_url": form_url,
        "qr_b64": qr_b64,
    })


@router.get("/forms/{form_id}/results", response_class=HTMLResponse)
def form_results(form_id: str, request: Request, db: Session = Depends(get_db)):
    redir = admin_redirect(request)
    if redir:
        return redir
    form = db.query(Form).filter(Form.form_id == form_id).first()
    if not form:
        return RedirectResponse("/admin/forms", status_code=302)
    response_count = db.query(ResponseModel).filter(ResponseModel.form_id == form_id).count()
    linked_dataset = db.query(Dataset).filter(Dataset.form_id == form_id).first()
    return templates.TemplateResponse(request, "admin/form_results.html", {
        "form": form,
        "response_count": response_count,
        "linked_dataset": linked_dataset,
    })


@router.get("/analysis", response_class=HTMLResponse)
def analysis_page(request: Request, db: Session = Depends(get_db)):
    redir = admin_redirect(request)
    if redir:
        return redir
    datasets = db.query(Dataset).order_by(Dataset.uploaded_at.desc()).all()
    return templates.TemplateResponse(request, "admin/csv_analysis.html", {
        "datasets": datasets,
        "current_dataset": None,
        "column_info": [],
    })


@router.get("/analysis/{dataset_id}", response_class=HTMLResponse)
def analysis_dataset(dataset_id: str, request: Request, db: Session = Depends(get_db)):
    redir = admin_redirect(request)
    if redir:
        return redir
    datasets = db.query(Dataset).order_by(Dataset.uploaded_at.desc()).all()
    current = db.query(Dataset).filter(Dataset.dataset_id == dataset_id).first()
    if not current:
        return RedirectResponse("/admin/analysis", status_code=302)
    column_info = json.loads(current.column_info or "[]")
    return templates.TemplateResponse(request, "admin/csv_analysis.html", {
        "datasets": datasets,
        "current_dataset": current,
        "column_info": column_info,
    })
