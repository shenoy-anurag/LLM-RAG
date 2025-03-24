import time
from typing import Any, Iterator

from fastapi import APIRouter, WebSocket
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import BaseMessageChunk, message_to_dict

from app.core.bot import retrieve_and_generate, generate_chunks, generate_text_chunks, SYSTEM_PROMPT
from app.models.bot import UserQuery


router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


@router.get("/test-stream", response_model=Any)
async def test() -> Any:
    """
    Test Streaming API.
    """

    stream = SYSTEM_PROMPT.split()

    def generate(stream):
        for chunk in stream:
            time.sleep(0.2)
            yield chunk + " "

    return StreamingResponse(generate(stream), media_type="text/event-stream")


@router.post("/rag", response_model=Any)
async def retrieval_augmented_generation(query: UserQuery) -> Any:
    """
    Do RAG.
    """
    stream = retrieve_and_generate(prompt=query.prompt)

    return StreamingResponse(generate_text_chunks(stream), media_type="text/event-stream")


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        user_prompt = await websocket.receive_text()

        stream = retrieve_and_generate(prompt=user_prompt)

        async def generate_text_chunks_socket(stream: Iterator[BaseMessageChunk]):
            for chunk in stream:
                res = message_to_dict(chunk)['data']['content']
                await websocket.send_text(f"{res}")
            await websocket.send_text(f"[END]")
        await generate_text_chunks_socket(stream)


@router.websocket("/echo")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        user_message = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {user_message}")
        await websocket.send_text(f"[END]")
