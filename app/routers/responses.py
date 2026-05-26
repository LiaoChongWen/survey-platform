import json
import uuid
import hashlib
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Form, Question, Response, Answer
from app.schemas import ResponseSubmit
from app.services.scoring import score_answer
from app.auth import get_current_admin

router = APIRouter()


@router.post("/form/{form_id}/submit")
async def submit_response(form_id: str, request: Request, db: Session = Depends(get_db)):
    form = db.query(Form).filter(Form.form_id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="問卷不存在")
    if form.status != "open":
        raise HTTPException(status_code=403, detail="問卷已關閉")

    now = datetime.utcnow()
    if form.start_time and now < form.start_time:
        raise HTTPException(status_code=403, detail="問卷尚未開始")
    if form.end_time and now > form.end_time:
        raise HTTPException(status_code=403, detail="問卷已截止")

    body = await request.json()
    payload = ResponseSubmit(**body)

    client_ip = request.client.host if request.client else "unknown"
    ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()

    resp = Response(
        response_id=str(uuid.uuid4()),
        form_id=form_id,
        student_name=payload.student_name,
        student_id=payload.student_id,
        student_class=payload.student_class,
        submitted_at=datetime.utcnow(),
        ip_hash=ip_hash,
    )
    db.add(resp)
    db.flush()

    total_score = 0.0
    question_map = {q.question_id: q for q in form.questions}

    for ans_data in payload.answers:
        question = question_map.get(ans_data.question_id)
        if not question:
            continue
        is_correct, score_received = score_answer(question, ans_data.answer_value)
        total_score += score_received

        answer = Answer(
            answer_id=str(uuid.uuid4()),
            response_id=resp.response_id,
            question_id=ans_data.question_id,
            answer_value=json.dumps(ans_data.answer_value, ensure_ascii=False),
            is_correct=is_correct,
            score_received=score_received,
        )
        db.add(answer)

    resp.total_score = total_score
    db.commit()

    show_score = form.show_result
    return {
        "message": "填答成功",
        "response_id": resp.response_id,
        "total_score": total_score if show_score else None,
        "show_result": show_score,
    }


@router.get("/api/forms/{form_id}/responses")
def get_responses(form_id: str, request: Request, db: Session = Depends(get_db)):
    user = get_current_admin(request)
    if not user:
        raise HTTPException(status_code=401, detail="未登入")
    responses = db.query(Response).filter(Response.form_id == form_id).order_by(Response.submitted_at.desc()).all()
    result = []
    for r in responses:
        result.append({
            "response_id": r.response_id,
            "student_name": r.student_name,
            "student_id": r.student_id,
            "student_class": r.student_class,
            "submitted_at": r.submitted_at.isoformat() if r.submitted_at else None,
            "total_score": r.total_score,
        })
    return result
