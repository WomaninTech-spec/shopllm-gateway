"""OpenAI-compatible request/response schemas."""
from __future__ import annotations
 
from typing import Literal
from pydantic import BaseModel, Field
 
 
class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str
 
 
class ChatCompletionRequest(BaseModel):
    model: str = Field(..., description="Logical model name, e.g. 'claude-haiku-4-5'.")
    messages: list[ChatMessage]
    max_tokens: int = Field(default=512, ge=1, le=8192)
    temperature: float = Field(default=1.0, ge=0.0, le=2.0)
 
 
class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
 
 
class ChatChoice(BaseModel):
    index: int = 0
    message: ChatMessage
    finish_reason: str = "stop"
 
 
class ChatCompletionResponse(BaseModel):
    id: str
    object: Literal["chat.completion"] = "chat.completion"
    created: int
    model: str
    choices: list[ChatChoice]
    usage: Usage