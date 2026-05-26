import json
from collections import Counter
from sqlalchemy.orm import Session
from app.models import Form, Question, Response, Answer


def get_score_distribution(form_id: str, db: Session) -> dict:
    responses = db.query(Response).filter(Response.form_id == form_id).all()
    if not responses:
        return {"labels": [], "data": [], "avg": 0, "std": 0, "max": 0, "min": 0, "count": 0}

    scores = [r.total_score for r in responses]
    buckets = {f"{i*10}-{i*10+9}": 0 for i in range(10)}
    buckets["100"] = 0
    for s in scores:
        idx = int(s // 10)
        if idx >= 10:
            buckets["100"] += 1
        else:
            key = f"{idx*10}-{idx*10+9}"
            buckets[key] += 1

    labels = list(buckets.keys())
    data = list(buckets.values())
    n = len(scores)
    avg = sum(scores) / n
    variance = sum((s - avg) ** 2 for s in scores) / n
    std = variance ** 0.5

    return {
        "labels": labels,
        "data": data,
        "avg": round(avg, 2),
        "std": round(std, 2),
        "max": max(scores),
        "min": min(scores),
        "count": n,
    }


def get_question_correct_rate(form_id: str, db: Session) -> list:
    form = db.query(Form).filter(Form.form_id == form_id).first()
    if not form:
        return []

    result = []
    for q in form.questions:
        if q.question_group != "statistics":
            continue
        answers = db.query(Answer).filter(Answer.question_id == q.question_id).all()
        if not answers:
            continue
        correct = sum(1 for a in answers if a.is_correct)
        total = len(answers)
        result.append({
            "question_text": q.question_text[:30] + ("..." if len(q.question_text) > 30 else ""),
            "correct_rate": round(correct / total * 100, 1),
            "wrong_rate": round((total - correct) / total * 100, 1),
            "total": total,
        })
    return result


SURVEY_TYPES = ("single", "multiple", "scale", "dropdown", "rating", "number", "short_text", "date")


def get_survey_question_stats(form_id: str, db: Session) -> list:
    form = db.query(Form).filter(Form.form_id == form_id).first()
    if not form:
        return []

    result = []
    for q in form.questions:
        if q.question_group != "survey":
            continue
        if q.question_type not in SURVEY_TYPES:
            continue

        answers = db.query(Answer).filter(Answer.question_id == q.question_id).all()
        if not answers:
            continue

        options = json.loads(q.options or "[]")
        counter = Counter()
        for a in answers:
            val = json.loads(a.answer_value or "null")
            if isinstance(val, list):
                for v in val:
                    counter[str(v)] += 1
            elif val is not None:
                counter[str(val)] += 1

        qtype = q.question_type

        if qtype in ("scale", "rating"):
            total_ans = len(answers)
            total_val = sum(
                float(k) * v for k, v in counter.items()
                if k.replace(".", "").lstrip("-").isdigit()
            )
            avg = total_val / total_ans if total_ans else 0
            sorted_keys = sorted(counter.keys(), key=lambda x: float(x) if x.replace(".", "").lstrip("-").isdigit() else 0)
            result.append({
                "question_id": q.question_id,
                "question_text": q.question_text,
                "question_type": qtype,
                "labels": sorted_keys,
                "data": [counter[k] for k in sorted_keys],
                "avg": round(avg, 2),
                "total": total_ans,
            })

        elif qtype == "number":
            vals = []
            for a in answers:
                val = json.loads(a.answer_value or "null")
                try:
                    vals.append(float(val))
                except (TypeError, ValueError):
                    pass
            if vals:
                avg = sum(vals) / len(vals)
                result.append({
                    "question_id": q.question_id,
                    "question_text": q.question_text,
                    "question_type": "number_stat",
                    "avg": round(avg, 2),
                    "min_val": round(min(vals), 2),
                    "max_val": round(max(vals), 2),
                    "total": len(vals),
                })

        elif qtype in ("short_text", "date"):
            # 顯示最常見的前 10 個回答
            top = counter.most_common(10)
            result.append({
                "question_id": q.question_id,
                "question_text": q.question_text,
                "question_type": qtype,
                "labels": [k for k, _ in top],
                "data": [v for _, v in top],
                "total": len(answers),
            })

        else:
            # single, multiple, dropdown
            labels = options if options else list(counter.keys())
            data = [counter.get(str(l), 0) for l in labels]
            result.append({
                "question_id": q.question_id,
                "question_text": q.question_text,
                "question_type": qtype,
                "labels": [str(l) for l in labels],
                "data": data,
                "total": len(answers),
            })
    return result


def get_essay_texts(form_id: str, db: Session) -> list:
    form = db.query(Form).filter(Form.form_id == form_id).first()
    if not form:
        return []
    texts = []
    for q in form.questions:
        if q.question_group != "essay" or q.question_type != "essay":
            continue
        answers = db.query(Answer).filter(Answer.question_id == q.question_id).all()
        for a in answers:
            val = json.loads(a.answer_value or "null")
            if val and isinstance(val, str) and val.strip():
                texts.append(val.strip())
    return texts
