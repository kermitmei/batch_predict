from fastapi import APIRouter, Response

from llmbase.main.llm.chatglm3.model import (EmbeddingResponse, EmbeddingRequest, ModelList,
                                             ChatCompletionResponse, ChatCompletionRequest)
from llmbase.main.services.chatglm3_service import ChatGLM3Service

router = APIRouter(prefix="/v1")


@router.get("/health")
async def health() -> Response:
    """Health check."""
    return Response(status_code=200)


@router.post("/embeddings", response_model=EmbeddingResponse)
def get_embeddings(request: EmbeddingRequest):
    return ChatGLM3Service.get_embeddings(request)


@router.get("/models", response_model=ModelList)
def models():
    return ChatGLM3Service.models()


@router.post("/chat/completions", response_model=ChatCompletionResponse)
def create_chat_completion(request: ChatCompletionRequest):
    return ChatGLM3Service.create_chat_completion(request)
