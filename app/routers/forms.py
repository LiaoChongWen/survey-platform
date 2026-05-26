import json
import uuid
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_admin
from app.models import Form, Question
from app.schemas import FormCreate

router = APIRouter()


def _require_admin(request: Request):
    user = get_current_admin(request)
    if not user:
        raise HTTPException(status_code=401, detail="未登入")
    return user


@router.get("")
def list_forms(request: Request, db: Session = Depends(get_db)):
    _require_admin(request)
    forms = db.query(Form).order_by(Form.created_at.desc()).all()
    result = []
    for f in forms:
        result.append({
            "form_id": f.form_id,
            "title": f.title,
            "status": f.status,
            "created_at": f.created_at.isoformat() if f.created_at else None,
            "response_count": len(f.responses),
        })
    return result


@router.post("")
def create_form(payload: FormCreate, request: Request, db: Session = Depends(get_db)):
    _require_admin(request)
    form = Form(
        form_id=str(uuid.uuid4()),
        title=payload.title,
        description=payload.description,
        status=payload.status,
        start_time=payload.start_time,
        end_time=payload.end_time,
        is_anonymous=payload.is_anonymous,
        show_result=payload.show_result,
    )
    db.add(form)
    db.flush()

    for idx, q in enumerate(payload.questions):
        question = Question(
            question_id=str(uuid.uuid4()),
            form_id=form.form_id,
            question_type=q.question_type,
            question_group=q.question_group,
            question_text=q.question_text,
            options=json.dumps(q.options, ensure_ascii=False),
            correct_answer=json.dumps(q.correct_answer, ensure_ascii=False),
            score=q.score,
            required=q.required,
            order_index=idx,
            explanation=q.explanation,
        )
        db.add(question)

    db.commit()
    db.refresh(form)
    return {"form_id": form.form_id, "message": "建立成功"}


@router.get("/{form_id}")
def get_form(form_id: str, db: Session = Depends(get_db)):
    form = db.query(Form).filter(Form.form_id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="問卷不存在")
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
    return {
        "form_id": form.form_id,
        "title": form.title,
        "description": form.description,
        "status": form.status,
        "is_anonymous": form.is_anonymous,
        "show_result": form.show_result,
        "start_time": form.start_time.isoformat() if form.start_time else None,
        "end_time": form.end_time.isoformat() if form.end_time else None,
        "questions": questions,
    }


@router.put("/{form_id}")
def update_form(form_id: str, payload: FormCreate, request: Request, db: Session = Depends(get_db)):
    _require_admin(request)
    form = db.query(Form).filter(Form.form_id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="問卷不存在")

    form.title = payload.title
    form.description = payload.description
    form.status = payload.status
    form.start_time = payload.start_time
    form.end_time = payload.end_time
    form.is_anonymous = payload.is_anonymous
    form.show_result = payload.show_result
    form.updated_at = datetime.utcnow()

    # 智能合併題目：有 question_id 的題目原地更新（保留 Answer 記錄），
    # 無 question_id 的新題目建立新列，不在 payload 的舊題目才刪除。
    existing_questions = {q.question_id: q for q in form.questions}
    incoming_ids = {q.question_id for q in payload.questions if q.question_id}

    for qid, old_q in existing_questions.items():
        if qid not in incoming_ids:
            db.delete(old_q)
    db.flush()

    for idx, q in enumerate(payload.questions):
        if q.question_id and q.question_id in existing_questions:
            eq = existing_questions[q.question_id]
            eq.question_type = q.question_type
            eq.question_group = q.question_group
            eq.question_text = q.question_text
            eq.options = json.dumps(q.options, ensure_ascii=False)
            eq.correct_answer = json.dumps(q.correct_answer, ensure_ascii=False)
            eq.score = q.score
            eq.required = q.required
            eq.order_index = idx
            eq.explanation = q.explanation
        else:
            question = Question(
                question_id=str(uuid.uuid4()),
                form_id=form.form_id,
                question_type=q.question_type,
                question_group=q.question_group,
                question_text=q.question_text,
                options=json.dumps(q.options, ensure_ascii=False),
                correct_answer=json.dumps(q.correct_answer, ensure_ascii=False),
                score=q.score,
                required=q.required,
                order_index=idx,
                explanation=q.explanation,
            )
            db.add(question)

    db.commit()
    return {"message": "更新成功"}


@router.patch("/{form_id}/status")
def update_status(form_id: str, request: Request, db: Session = Depends(get_db)):
    _require_admin(request)
    import asyncio
    body = None

    async def _get_body():
        return await request.json()

    try:
        import asyncio
        loop = asyncio.get_event_loop()
        body = loop.run_until_complete(_get_body())
    except Exception:
        pass

    form = db.query(Form).filter(Form.form_id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="問卷不存在")
    return {"message": "請使用 PUT 更新"}


@router.delete("/{form_id}")
def delete_form(form_id: str, request: Request, db: Session = Depends(get_db)):
    _require_admin(request)
    form = db.query(Form).filter(Form.form_id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="問卷不存在")
    db.delete(form)
    db.commit()
    return {"message": "刪除成功"}


@router.post("/{form_id}/toggle")
async def toggle_status(form_id: str, request: Request, db: Session = Depends(get_db)):
    _require_admin(request)
    form = db.query(Form).filter(Form.form_id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="問卷不存在")
    body = await request.json()
    new_status = body.get("status", "open")
    form.status = new_status
    form.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "狀態更新", "status": form.status}
