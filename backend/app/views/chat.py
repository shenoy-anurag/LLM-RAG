import time
from typing import Any, Iterator

from fastapi import APIRouter, WebSocket, status
from fastapi.responses import StreamingResponse, JSONResponse
from langchain_core.messages import AIMessageChunk, message_to_dict

from app.core.bot import (
    retrieve_and_generate, generate_text_chunks,
    SYSTEM_PROMPT, retrieve_and_generate_sync,
    generate_with_tools
)
from app.models.bot import UserQuery


router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


@router.get("/stream/test-stream", response_model=Any)
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


@router.post("/stream/rag", response_model=Any)
async def retrieval_augmented_generation_stream(query: UserQuery) -> Any:
    """
    Do RAG & Stream.
    """
    stream = retrieve_and_generate(prompt=query.prompt)

    return StreamingResponse(generate_text_chunks(stream), media_type="text/event-stream")


@router.post("/sync/rag", response_model=Any)
async def retrieval_augmented_generation(query: UserQuery) -> Any:
    """
    2-Step RAG chain with a single inference step per query.
    Retrieves relevant context from the MedQuad dataset stored in Qdrant vector database, 
    and generates a grounded response.
    """
    message = retrieve_and_generate_sync(prompt=query.prompt)
    # result = smart_retrieve_and_generate(prompt=query.prompt)

    return JSONResponse(status_code=status.HTTP_200_OK, content=message.content)


@router.post("/sync/rag-with-tools", response_model=Any)
async def retrieval_augmented_generation_with_tools(query: UserQuery) -> Any:
    """
    Agentic RAG with tool calling abilities.
    Retrieves relevant context from the MedQuad dataset if required, 
    or checks the FDA drug label API for drug warnings if asked.
    """
    message = generate_with_tools(prompt=query.prompt)

    return JSONResponse(status_code=status.HTTP_200_OK, content=message['messages'][-1].content)


@router.websocket("/ws/rag")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        user_prompt = await websocket.receive_text()

        stream = retrieve_and_generate(prompt=user_prompt)

        async def generate_text_chunks_socket(stream: Iterator[AIMessageChunk]):
            for chunk in stream:
                res = message_to_dict(chunk)['data']['content']
                await websocket.send_text(f"{res}")
            await websocket.send_text(f"[END]")
        await generate_text_chunks_socket(stream)


@router.websocket("/ws/echo")
async def websocket_endpoint_echo(websocket: WebSocket):
    await websocket.accept()
    while True:
        user_message = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {user_message}")
        await websocket.send_text(f"[END]")
