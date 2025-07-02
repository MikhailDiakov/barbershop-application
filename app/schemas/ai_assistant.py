from pydantic import BaseModel


class QuestionIn(BaseModel):
    question: str


class AnswerOut(BaseModel):
    answer: str
