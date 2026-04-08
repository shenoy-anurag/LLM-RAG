from pydantic import BaseModel, SecretStr
from typing import Iterator, List, Optional

from langchain_core.documents import Document
from langchain.chat_models import init_chat_model
from langchain_openai import OpenAIEmbeddings
# from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.vectorstores import VectorStore
from langchain_core.messages import AIMessage, AIMessageChunk, message_to_dict
from langchain_qdrant import QdrantVectorStore

from app.core.config import settings

# OPENAI
LLM = init_chat_model(
    settings.OPENAI_MODEL_NAME or "gpt-4o-mini",
    model_provider="openai",
    api_key=settings.OPENAI_API_KEY
)
EMBEDDINGS = OpenAIEmbeddings(
    model=settings.OPENAI_EMBEDDINGS_NAME or "text-embedding-3-small",
    api_key=SecretStr(settings.OPENAI_API_KEY),
)
VECTOR_STORE = QdrantVectorStore.from_existing_collection(
    embedding=EMBEDDINGS,
    collection_name=settings.QDRANT_COLLECTION_NAME,
    url=settings.QDRANT_URL,
    api_key=settings.QDRANT_API_KEY,
)

# GOOGLE GEMINI AI
# LLM = init_chat_model(
#     "google_genai:" + (settings.GOOGLE_MODEL_NAME or "gemini-2.5-flash-lite"),
#     model_provider="google_genai",
#     api_key=settings.GOOGLE_API_KEY
# )
# EMBEDDINGS = GoogleGenerativeAIEmbeddings(
#     model=settings.GOOGLE_EMBEDDINGS_NAME or "gemini-embedding-001",
#     api_key=SecretStr(settings.GOOGLE_API_KEY),
# )
# VECTOR_STORE = QdrantVectorStore.from_existing_collection(
#     embedding=EMBEDDINGS,
#     collection_name=settings.QDRANT_COLLECTION_NAME,
#     url=settings.QDRANT_URL,
#     api_key=settings.QDRANT_API_KEY,
# )

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
    context: Optional[List[Document]]
    answer: str
    tenant: Optional[str]


def retrieve(db: VectorStore, state: State):
    # defaults to k = 4, so max 4 documents are returned.
    retrieved_docs = db.similarity_search(state.question)
    return {"context": retrieved_docs}


def generate(state: State) -> Iterator[AIMessageChunk]:
    if state.context is None:
        state.context = []
    docs_content = "\n\n".join(doc.page_content for doc in state.context)
    messages = PROMPT.invoke(
        {"question": state.question, "context": docs_content})
    # print(messages)
    stream = LLM.stream(messages)
    return stream


def generate_sync(state: State):
    if state.context is None:
        state.context = []
    docs_content = "\n\n".join(doc.page_content for doc in state.context)
    messages = PROMPT.invoke(
        {"question": state.question, "context": docs_content})
    # print(messages)
    stream = LLM.invoke(messages)
    return stream


def generate_text_chunks(stream: Iterator[AIMessageChunk]):
    for chunk in stream:
        # print(message_to_dict(chunk))
        res = message_to_dict(chunk)['data']['content']
        yield res
    # yield "[END]"


def retrieve_and_generate(prompt, tenant=None) -> Iterator[AIMessageChunk]:
    state = State(question=prompt, context=None, answer='', tenant=None)
    if tenant:
        state.tenant = tenant

    context = retrieve(VECTOR_STORE, state)
    state.context = context['context']

    stream = generate(state)
    return stream


def retrieve_and_generate_sync(prompt, tenant=None) -> AIMessage:
    state = State(question=prompt, context=None, answer='', tenant=None)
    if tenant:
        state.tenant = tenant

    context = retrieve(VECTOR_STORE, state)
    state.context = context['context']

    message = generate_sync(state)
    return message
