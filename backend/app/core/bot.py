import json
import os
from pydantic import BaseModel
from typing import List, Dict, Optional

from langchain.chat_models import init_chat_model
from langchain_openai import OpenAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.vectorstores import VectorStore
from langchain_core.messages import BaseMessageChunk, message_to_dict
from langchain_qdrant import QdrantVectorStore

from app.core.config import settings


LLM = init_chat_model(
    settings.OPENAI_MODEL_NAME or "gpt-4o-mini",
    model_provider="openai",
    api_key=settings.OPENAI_API_KEY
)

EMBEDDINGS = OpenAIEmbeddings(
    model=settings.OPENAI_EMBEDDINGS_NAME or "text-embedding-3-small",
    api_key=settings.OPENAI_API_KEY,
)


VECTOR_STORE = QdrantVectorStore.from_existing_collection(
    embedding=EMBEDDINGS,
    collection_name=settings.QDRANT_COLLECTION_NAME,
    url=settings.QDRANT_URL,
    api_key=settings.QDRANT_API_KEY,
)

SYSTEM_PROMPT = """
You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. 
If you don't know the answer, just say that you don't know. Keep the answer short and concise. Try to use less than 5 sentences.
"""

PROMPT_TEMPLATE = SYSTEM_PROMPT + """
Question: {question} 
Context: {context} 
Answer: 
"""

PROMPT = PromptTemplate.from_template(PROMPT_TEMPLATE)


class State(BaseModel):
    question: str
    context: Optional[List[Dict]]
    answer: str


def retrieve(db: VectorStore, state: State):
    # defaults to k = 4, so max 4 documents are returned.
    retrieved_docs = db.similarity_search(state["question"])
    return {"context": retrieved_docs}


def generate(state: State):
    docs_content = "\n\n".join(doc.page_content for doc in state["context"])
    messages = PROMPT.invoke(
        {"question": state["question"], "context": docs_content})
    # print(messages)
    stream = LLM.stream(messages)
    return stream


def generate_chunks(stream: BaseMessageChunk):
    for chunk in stream:
        res = message_to_dict(chunk)
        yield json.dumps(res)


def generate_text_chunks(stream: BaseMessageChunk):
    for chunk in stream:
        # print(message_to_dict(chunk))
        res = message_to_dict(chunk)['data']['content']
        yield res
    # yield "[END]"


def generate_text_chunks_socket(stream: BaseMessageChunk):
    for chunk in stream:
        # print(message_to_dict(chunk))
        res = message_to_dict(chunk)['data']['content']
        yield res
    yield "[END]"


def retrieve_and_generate(prompt, tenant=None):
    state = {'question': prompt, 'context': None, 'answer': ''}
    if tenant:
        state.update({'tenant': tenant})

    context = retrieve(VECTOR_STORE, state)
    state['context'] = context['context']

    stream = generate(state)
    return stream
