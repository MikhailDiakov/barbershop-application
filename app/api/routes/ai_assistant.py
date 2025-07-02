from fastapi import APIRouter

from app.schemas.ai_assistant import AnswerOut, QuestionIn
from app.services.ai_assistant_service import ask_barber_ai

router = APIRouter()


@router.post("/ask", response_model=AnswerOut)
async def ask_ai(question_data: QuestionIn):
    answer = await ask_barber_ai(question_data.question)
    return {"answer": answer}
