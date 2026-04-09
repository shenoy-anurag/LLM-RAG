import logging
import requests
from pydantic import BaseModel, SecretStr
from typing import Iterator, List, Optional

from langchain_core.tools import tool
from langchain_core.documents import Document
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_openai import OpenAIEmbeddings
# from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from langchain_core.vectorstores import VectorStore
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage, message_to_dict
from langchain_qdrant import QdrantVectorStore

from app.core.config import settings
from app.loggers import log_langchain_event_v2

logger = logging.getLogger(__name__)


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
You are a medical assistant. Use the MedQuad RAG context for general questions, 
but ALWAYS use the 'get_drug_interaction_warnings' tool for drug interaction concerns, 
and ALWAYS use the 'get_pregnancy_warnings' for pregnancy and breastfeeding related concerns.
If you don't know the answer, just say that you don't know. 
Keep the answer short and concise. Try to use less than 5 sentences.
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


def retrieve_and_generate(prompt, tenant=None) -> Iterator[AIMessageChunk]:
    state = State(question=prompt, context=None, answer='', tenant=None)
    if tenant:
        state.tenant = tenant

    context = retrieve(VECTOR_STORE, state)
    state.context = context['context']

    stream = generate(state)
    return stream


def generate_text_chunks(stream: Iterator[AIMessageChunk]):
    for chunk in stream:
        res = message_to_dict(chunk)['data']['content']
        yield res


def generate_sync(state: State):
    if state.context is None:
        state.context = []
    docs_content = "\n\n".join(doc.page_content for doc in state.context)
    messages = PROMPT.invoke(
        {"question": state.question, "context": docs_content})
    # print(messages)
    stream = LLM.invoke(messages)
    return stream


def retrieve_and_generate_sync(prompt, tenant=None) -> AIMessage:
    state = State(question=prompt, context=None, answer='', tenant=None)
    if tenant:
        state.tenant = tenant

    context = retrieve(VECTOR_STORE, state)
    state.context = context['context']

    message = generate_sync(state)
    return message


@tool
def get_drug_interaction_warnings(drug_name: str) -> str:
    """
    Queries the OpenFDA API for official boxed warnings or adverse 
    reactions for a specific medication or substance. Use this for specific safety 
    concerns rather than general information.
    """
    url = f"https://api.fda.gov/drug/label.json?search=drug_interactions:{drug_name}&limit=2"
    log_langchain_event_v2(
        event={'event': 'tool', 'name': 'get_drug_interaction_warnings', 'input': {'drug_name': drug_name}})

    try:
        response = requests.get(url)
        data = response.json()

        if "results" in data:
            # Extract warnings if they exist
            result = data["results"][0]
            warning = result.get(
                "warnings", ["No warnings found."])[0]
            adverse = result.get(
                "adverse_reactions", ["No data on reactions."]
            )[0]
            do_not_use = result.get(
                "do_not_use", ["No data on do not use."]
            )[0]
            return f"Official FDA Safety Data for {drug_name}:\nWarning: {warning[:500]}...\nAdverse Reactions: {adverse[:500]}...\nDo Not Use: {do_not_use[:500]}"
        return f"No specific safety data found for {drug_name} in OpenFDA."
    except Exception as e:
        return f"Error connecting to safety database: {str(e)}"


@tool
def get_pregnancy_warnings(drug_name: str) -> str:
    """
    Queries the OpenFDA API for official pregnancy related drug warnings for a specific medication or substance.
    """
    url = f"https://api.fda.gov/drug/label.json?search=drug_interactions:{drug_name}&limit=2"
    log_langchain_event_v2(
        event={'event': 'tool', 'name': 'get_pregnancy_warnings', 'input': {'drug_name': drug_name}})

    try:

        response = requests.get(url)
        data = response.json()

        if "results" in data:
            # Extract boxed warnings if they exist
            result = data["results"][0]
            pregnancy = result.get(
                "pregnancy", ["No pregnancy warning found."])[0]
            pregnancy_or_breast_feeding = result.get(
                "pregnancy_or_breast_feeding", [
                    "No data on pregnancy or breast feeding adverse interactions."]
            )[0]
            return f"Official FDA Safety Data for {drug_name}:\nPregnancy warnings: {pregnancy[:500]}...\nBreastfeeding warnings: {pregnancy_or_breast_feeding[:500]}..."
        return f"No specific safety data found for {drug_name} in OpenFDA."
    except Exception as e:
        return f"Error connecting to safety database: {str(e)}"


@tool(response_format="content_and_artifact")
def retrieve_context(query: str):
    """Retrieve information to help answer a query."""
    # log_langchain_event(
    #     event={'event': 'tool', 'name': 'retrieve_context', 'input': {'query': query}})
    log_langchain_event_v2(
        {'event': 'tool', 'name': 'retrieve_context', 'input': {'query': query}})
    retrieved_docs = VECTOR_STORE.similarity_search(query, k=4)
    serialized = "\n\n".join(
        (f"Source: {doc.metadata}\nContent: {doc.page_content}")
        for doc in retrieved_docs
    )
    return serialized, retrieved_docs


tools = [retrieve_context, get_drug_interaction_warnings, get_pregnancy_warnings]

agent = create_agent(LLM, tools=tools)


def generate_with_tools(prompt: str):
    log_langchain_event_v2(
        {'event': 'invoke', 'name': 'generate_with_tools', 'input': {'prompt': prompt}})
    response = agent.invoke({
        'messages': [
            HumanMessage(content=prompt)
        ]
    })
    return response
