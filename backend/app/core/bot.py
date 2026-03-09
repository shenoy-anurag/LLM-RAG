import json
import os
import re
from pydantic import BaseModel
from typing import List, Dict, Optional

from langchain.chat_models import init_chat_model
from langchain_openai import OpenAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.vectorstores import VectorStore
from langchain_core.messages import BaseMessageChunk, message_to_dict
from langchain_qdrant import QdrantVectorStore
from langchain_classic.agents import AgentExecutor, create_openai_functions_agent

from app.core.config import settings
from app.core.tools import DRUG_TOOLS


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


def generate_sync(state: State):
    docs_content = "\n\n".join(doc.page_content for doc in state["context"])
    messages = PROMPT.invoke(
        {"question": state["question"], "context": docs_content})
    # print(messages)
    stream = LLM.invoke(messages)
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


def retrieve_and_generate_sync(prompt, tenant=None):
    state = {'question': prompt, 'context': None, 'answer': ''}
    if tenant:
        state.update({'tenant': tenant})

    context = retrieve(VECTOR_STORE, state)
    state['context'] = context['context']

    message = generate_sync(state)
    return message


AGENT_SYSTEM_PROMPT = """You are a medical assistant. Your job is to help users with medication-related questions.

You have access to the following tools:
- check_drug_interactions: Check for interactions between multiple medications
- get_drug_info: Get detailed information about a single drug

When a user asks about:
- Drug interactions (e.g., "Can I take X with Y?")
- Taking multiple medications together
- Safety of combining drugs

You MUST use the check_drug_interactions tool.

When a user asks about:
- What a drug is used for
- Side effects of a drug
- General information about a medication

You should use the get_drug_info tool.

If the question is about general medical topics (not specific drugs), use the provided context to answer.

Always prioritize patient safety - if unsure, recommend consulting a healthcare professional.
"""

DRUG_INTERACTION_PATTERNS = [
    r"\b(can i take|can i take|can\s+.*take|taking.*with|interact|interaction)",
    r"\b(together|combine|with|while on|on medication)",
    r"\b(drug|drugs|medication|medicine|pill)",
]

DRUG_KEYWORDS = [
    "warfarin", "aspirin", "ibuprofen", "acetaminophen", " Tylenol ",
    "lipitor", "zoloft", "metformin", "amoxicillin", "prednisone",
    "lisinopril", "metoprolol", "omeprazole", "amlodipine", "losartan",
    "xanax", "valium", "ambien", "prozac", "neurontin", "lyrica",
    "coumadin", "heparin", "plavix", "eliquis", "xarelto",
    "zocor", "crestor", "effexor", "celexa", "lexapro",
]


def is_drug_interaction_query(prompt: str) -> bool:
    """Detect if the prompt is asking about drug interactions."""
    prompt_lower = prompt.lower()
    
    if any(kw in prompt_lower for kw in DRUG_KEYWORDS):
        if any(re.search(pattern, prompt_lower) for pattern in DRUG_INTERACTION_PATTERNS):
            return True
    
    interaction_phrases = [
        "interact", "interaction", "can i take", "taking together",
        "combine", "safe to take", "side effects", "with warfarin",
        "with aspirin", "with ibuprofen", "with acetaminophen",
    ]
    return any(phrase in prompt_lower for phrase in interaction_phrases)


def get_drug_names(prompt: str) -> List[str]:
    """Extract potential drug names from the prompt."""
    prompt_lower = prompt.lower()
    found_drugs = []
    
    common_drugs = [
        "warfarin", "coumadin", "aspirin", "ibuprofen", "advil", "motrin",
        "acetaminophen", "tylenol", "naproxen", "aleve", "meloxicam",
        "diclofenac", "celecoxib", "prednisone", "methylprednisolone",
        "heparin", "enoxaparin", "plavix", "clopidogrel", "prasugrel",
        "apixaban", "rivaroxaban", "dabigatran", "eliquis", "xarelto",
        "lipitor", "atorvastatin", "simvastatin", "zocor", "rosuvastatin",
        "zoloft", "sertraline", "fluoxetine", "prozac", "paroxetine",
        "paxil", "citalopram", "escitalopram", "lexapro", "effexor",
        "venlafaxine", "duloxetine", "cymbalta", "metformin", "glipizide",
        "glyburide", "insulin", "lisinopril", "losartan", "valsartan",
        "atenolol", "metoprolol", "propranolol", "carvedilol", "amlodipine",
        "diltiazem", "verapamil", "omeprazole", "pantoprazole", "esomeprazole",
        "nexium", "prilosec", "xanax", "alprazolam", "lorazepam",
        "ativan", "valium", "diazepam", "klonopin", "clonazepam",
        "ambien", "zolpidem", "lunesta", "eszopiclone", "benadryl",
        "diphenhydramine", "zyrtec", "claritin", "allegra", "advair",
        "symbicort", "albuterol", "ventolin", "prednisone", "medrol",
    ]
    
    for drug in common_drugs:
        if drug in prompt_lower:
            found_drugs.append(drug.title())
    
    return found_drugs


def create_agent():
    """Create a LangChain agent with drug interaction tools."""
    prompt = PromptTemplate.from_template("{input}\n\n{agent_scratchpad}")
    
    agent = create_openai_functions_agent(
        llm=LLM,
        tools=DRUG_TOOLS,
        prompt=prompt
    )
    
    agent_executor = AgentExecutor(
        agent=agent,
        tools=DRUG_TOOLS,
        verbose=True,
        max_iterations=5,
        handle_parsing_errors=True
    )
    
    return agent_executor


AGENT_EXECUTOR = create_agent()


def process_with_tools(prompt: str) -> str:
    """Process a prompt using the agent with drug interaction tools."""
    try:
        result = AGENT_EXECUTOR.invoke({"input": prompt})
        return result.get("output", "No response generated.")
    except Exception as e:
        return f"Error processing request: {str(e)}"


def smart_retrieve_and_generate(prompt: str, tenant=None) -> str:
    """
    Intelligently route the prompt to either:
    1. Drug interaction checker (if it's a drug-related query)
    2. Standard RAG pipeline (for general medical questions)
    """
    if is_drug_interaction_query(prompt):
        drug_names = get_drug_names(prompt)
        if len(drug_names) >= 2:
            return process_with_tools(prompt)
    
    state = {'question': prompt, 'context': None, 'answer': ''}
    if tenant:
        state.update({'tenant': tenant})

    context = retrieve(VECTOR_STORE, state)
    state['context'] = context['context']

    message = generate_sync(state)
    return message