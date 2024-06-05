from fastapi import APIRouter, Response

from llmbase.main.llm.chatglm3.model import (EmbeddingResponse, EmbeddingRequest, ModelList,
                                             ChatCompletionResponse, ChatCompletionRequest)
from llmbase.main.services.chatglm4_service import ChatGLM4Service

router = APIRouter(prefix="/v1")


@router.get("/health")
async def health() -> Response:
    """Health check."""
    return Response(status_code=200)


@router.post("/embeddings", response_model=EmbeddingResponse)
def get_embeddings(request: EmbeddingRequest):
    return ChatGLM4Service.get_embeddings(request)


@router.get("/models", response_model=ModelList)
def models():
    return ChatGLM4Service.models()


@router.post("/chat/completions", response_model=ChatCompletionResponse)
def create_chat_completion(request: ChatCompletionRequest):
    if len(request.messages) > 1:
        return ChatGLM4Service.create_batch_completion(request)
    return ChatGLM4Service.create_chat_completion(request)
