from __future__ import annotations
import json
from typing import Any, Tuple, Optional


def normalize(val: Any) -> Any:
    if isinstance(val, str):
        return val.strip().lower()
    if isinstance(val, list):
        return sorted([str(v).strip().lower() for v in val])
    return val


def score_answer(question, answer_value: Any) -> Tuple[Optional[bool], float]:
    """Returns (is_correct, score_received). is_correct is None for non-graded questions."""
    correct_raw = question.correct_answer
    if correct_raw is None or correct_raw == "null":
        return None, 0.0

    correct = json.loads(correct_raw) if isinstance(correct_raw, str) else correct_raw
    if correct is None:
        return None, 0.0

    qtype = question.question_type

    if qtype == "single":
        if normalize(answer_value) == normalize(correct):
            return True, float(question.score)
        return False, 0.0

    elif qtype == "multiple":
        ans_set = set(normalize(answer_value) if isinstance(answer_value, list) else [normalize(answer_value)])
        cor_set = set(normalize(correct) if isinstance(correct, list) else [normalize(correct)])
        if ans_set == cor_set:
            return True, float(question.score)
        return False, 0.0

    elif qtype == "number":
        try:
            ans_num = float(str(answer_value).strip())
            cor_num = float(str(correct).strip())
            if abs(ans_num - cor_num) < 1e-9:
                return True, float(question.score)
            return False, 0.0
        except (ValueError, TypeError):
            return False, 0.0

    elif qtype == "short_text":
        if normalize(answer_value) == normalize(correct):
            return True, float(question.score)
        return False, 0.0

    return None, 0.0
