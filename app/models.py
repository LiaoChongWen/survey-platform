import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Boolean, Float, Integer,
    DateTime, Enum, ForeignKey
)
from sqlalchemy.orm import relationship
from app.database import Base

import enum


class FormStatus(str, enum.Enum):
    draft = "draft"
    open = "open"
    closed = "closed"


class QuestionType(str, enum.Enum):
    single = "single"
    multiple = "multiple"
    scale = "scale"
    number = "number"
    short_text = "short_text"
    essay = "essay"
    dropdown = "dropdown"
    rating = "rating"
    date = "date"


class QuestionGroup(str, enum.Enum):
    statistics = "statistics"
    survey = "survey"
    essay = "essay"


def gen_uuid():
    return str(uuid.uuid4())


class Form(Base):
    __tablename__ = "forms"

    form_id = Column(String, primary_key=True, default=gen_uuid)
    title = Column(String(200), nullable=False)
    description = Column(Text, default="")
    status = Column(String(20), default=FormStatus.draft)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    is_anonymous = Column(Boolean, default=False)
    show_result = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    questions = relationship("Question", back_populates="form",
                             cascade="all, delete-orphan",
                             order_by="Question.order_index")
    responses = relationship("Response", back_populates="form",
                             cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"

    question_id = Column(String, primary_key=True, default=gen_uuid)
    form_id = Column(String, ForeignKey("forms.form_id"), nullable=False)
    question_type = Column(String(20), default=QuestionType.single)
    question_group = Column(String(20), default=QuestionGroup.survey)
    question_text = Column(Text, nullable=False)
    options = Column(Text, default="[]")
    correct_answer = Column(Text, default="null")
    score = Column(Float, default=0.0)
    required = Column(Boolean, default=True)
    order_index = Column(Integer, default=0)
    explanation = Column(Text, default="")

    form = relationship("Form", back_populates="questions")
    answers = relationship("Answer", back_populates="question",
                           cascade="all, delete-orphan")


class Response(Base):
    __tablename__ = "responses"

    response_id = Column(String, primary_key=True, default=gen_uuid)
    form_id = Column(String, ForeignKey("forms.form_id"), nullable=False)
    student_name = Column(String(100), default="")
    student_id = Column(String(50), default="")
    student_class = Column(String(50), default="")
    submitted_at = Column(DateTime, default=datetime.utcnow)
    total_score = Column(Float, default=0.0)
    ip_hash = Column(String(64), default="")

    form = relationship("Form", back_populates="responses")
    answers = relationship("Answer", back_populates="response",
                           cascade="all, delete-orphan")


class Answer(Base):
    __tablename__ = "answers"

    answer_id = Column(String, primary_key=True, default=gen_uuid)
    response_id = Column(String, ForeignKey("responses.response_id"), nullable=False)
    question_id = Column(String, ForeignKey("questions.question_id"), nullable=False)
    answer_value = Column(Text, default="null")
    is_correct = Column(Boolean, nullable=True)
    score_received = Column(Float, default=0.0)

    response = relationship("Response", back_populates="answers")
    question = relationship("Question", back_populates="answers")


class Dataset(Base):
    __tablename__ = "datasets"

    dataset_id = Column(String, primary_key=True, default=gen_uuid)
    dataset_name = Column(String(200), nullable=False)
    file_name = Column(String(300), nullable=False)
    file_path = Column(String(500), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    row_count = Column(Integer, default=0)
    column_count = Column(Integer, default=0)
    column_info = Column(Text, default="[]")
    form_id = Column(String, nullable=True)
