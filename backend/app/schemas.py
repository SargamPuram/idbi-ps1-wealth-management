"""Pydantic request/response models for PS1 — Dhanvi Wealth Advisory API."""
from typing import Optional

from pydantic import BaseModel, Field


class ChatHistoryTurn(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str


class ChatRequest(BaseModel):
    customer_id: str
    message: str
    language: Optional[str] = None
    conversation_history: Optional[list[ChatHistoryTurn]] = None


class SuitabilityRequest(BaseModel):
    customer_id: Optional[str] = None
    answers: dict = Field(..., description="Map of question id (1-10, as string or int) -> option index (0-4)")


class GoalPlanRequest(BaseModel):
    customer_id: Optional[str] = None
    goal_type: str
    target_amount: float
    target_date: str = Field(..., description="ISO date YYYY-MM-DD")
    current_progress: float = 0
    risk_profile: Optional[str] = None


class EscalateRequest(BaseModel):
    customer_id: str
    reason: str
    context_summary: Optional[str] = None
    conversation_snippet: Optional[str] = None


class TTSRequest(BaseModel):
    text: str
    language: Optional[str] = "English"
