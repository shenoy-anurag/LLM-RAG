import time
from typing import Any

from fastapi import APIRouter
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from app.core.bot import retrieve_and_generate, generate_chunks, generate_text_chunks, SYSTEM_PROMPT


router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


@router.get("/test-stream", response_model=Any)
async def test(user_prompt: str) -> Any:
    """
    Test RAG.
    """
    
    print(user_prompt)
    
    stream = SYSTEM_PROMPT.split()
    
    def generate(stream):
        for chunk in stream:
            # print(chunk + " ")
            time.sleep(0.2)
            yield chunk + " "
    
    return StreamingResponse(generate(stream), media_type="text/event-stream")


@router.get("/rag", response_model=Any)
async def do_rag(user_prompt: str) -> Any:
    """
    Do RAG.
    """
    stream = retrieve_and_generate(user_prompt=user_prompt)
    
    return StreamingResponse(generate_text_chunks(stream), media_type="text/event-stream")
