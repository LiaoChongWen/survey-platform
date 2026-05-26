from typing import Optional, List, Any
from pydantic import BaseModel
from datetime import datetime


class QuestionCreate(BaseModel):
    question_id: Optional[str] = None
    question_type: str
    question_group: str
    question_text: str
    options: List[str] = []
    correct_answer: Any = None
    score: float = 0.0
    required: bool = True
    order_index: int = 0
    explanation: str = ""


class FormCreate(BaseModel):
    title: str
    description: str = ""
    status: str = "draft"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_anonymous: bool = False
    show_result: bool = False
    questions: List[QuestionCreate] = []


class AnswerSubmit(BaseModel):
    question_id: str
    answer_value: Any


class ResponseSubmit(BaseModel):
    student_name: str = ""
    student_id: str = ""
    student_class: str = ""
    answers: List[AnswerSubmit]


class AnalyzeRequest(BaseModel):
    chart_type: str
    x_column: str
    y_column: Optional[str] = None
    group_column: Optional[str] = None
