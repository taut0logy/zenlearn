from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.gemini_service import gemini_service

router = APIRouter()


class AIRequest(BaseModel):
    prompt: str


class AIResponse(BaseModel):
    response: str


@router.post("/test-ai", response_model=AIResponse)
async def test_ai_endpoint(request: AIRequest):
    try:
        response_text = await gemini_service.generate_response(request.prompt)
        return AIResponse(response=response_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
