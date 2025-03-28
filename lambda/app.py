from datetime import datetime, timedelta, timezone
import json
import secrets
import uuid
import jwt
import bcrypt
from mangum import Mangum
from fastapi import APIRouter, FastAPI, Depends, status
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import func
from sqlmodel import Field, SQLModel, Session, create_engine, select
from collections.abc import Generator
from sqlmodel import Session
import uvicorn
from langchain_qdrant import QdrantVectorStore
from langchain_core.messages import BaseMessageChunk, message_to_dict
from langchain_core.vectorstores import VectorStore
from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAIEmbeddings
from langchain.chat_models import init_chat_model
from typing import Dict, List, Optional, Text, Union
from typing import Annotated, Any, Literal
from pydantic import (
    AnyUrl,
    BaseModel,
    BeforeValidator,
    EmailStr,
    HttpUrl,
    computed_field,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


# ----------------------------------------- #
#              Settings Section             #

def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    FRONTEND_HOST: str = "http://localhost:8501"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = []

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS] + [
            self.FRONTEND_HOST
        ]

    PROJECT_NAME: str
    SENTRY_DSN: HttpUrl | None = None

    SQLALCHEMY_DATABASE_URI: str

    FIRST_SUPERUSER: EmailStr
    FIRST_SUPERUSER_PASSWORD: str
    FIRST_SUPERUSER_FIRST_NAME: str
    FIRST_SUPERUSER_LAST_NAME: str

    JWT_USER: EmailStr
    JWT_USER_PASSWORD: str
    JWT_USER_FIRST_NAME: str
    JWT_USER_LAST_NAME: str

    TIME_ZONE: str

    # LLM RAG
    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL_NAME: str
    OPENAI_EMBEDDINGS_NAME: str
    # Qdrant
    QDRANT_COLLECTION_NAME: str
    QDRANT_API_KEY: str
    QDRANT_URL: str


settings = Settings()  # type: ignore

#            End Settings Section           #
# ----------------------------------------- #

# ----------------------------------------- #
#           FastAPI Setup Section           #

app = FastAPI()


def add_cors(app: FastAPI):
    # function for enabling CORS on web server
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"])


add_cors(app)

handler = Mangum(app)

#         End FastAPI Setup Section         #
# ----------------------------------------- #

# ----------------------------------------- #
#             LLM & RAG Section             #

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
    yield "[END]"


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


#           LLM & RAG Section End           #
# ----------------------------------------- #

#             Security Section              #
# ----------------------------------------- #

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(
    subject: str | Any,
    expires_delta: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=ALGORITHM
    )
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def generate_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# ----------------------------------------- #
#             End Security Section          #

#                  DB Section               #
# ----------------------------------------- #


engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))


reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]

# ----------------------------------------- #
#               End DB Section              #


#               Model Section               #
# ----------------------------------------- #


class UserQuery(SQLModel):
    prompt: Text
    collection: Optional[Text] = Field(None, description="Collection to query")


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    first_name: str = Field(default=None, max_length=255, nullable=False)
    last_name: str | None = Field(default='', max_length=255, nullable=True)
    is_superuser: bool = False


class User(UserBase, table=True):
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True, nullable=False
    )
    password_hash: str = Field(max_length=512, nullable=False)
    is_active: bool = True
    created_at: datetime = Field(default_factory=func.now)
    updated_at: datetime = Field(
        default_factory=func.now,
        sa_column_kwargs={"onupdate": func.now()}
    )

    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify the user's password."""
        return verify_password(password, self.password_hash)


class UserPublicToken(UserBase):
    id: uuid.UUID
    token: Token


class UserLogin(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)


def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    return session_user


def verify_and_generate_token(*, session: Session, email: str, password: str) -> Token | None:
    user = get_user_by_email(session=session, email=email)
    if not user:
        raise ValueError("Incorrect email and password combination!")
    is_authenticated = user.check_password(password=password)
    if not is_authenticated:
        raise ValueError("Incorrect email and password combination!")
    access_token = create_access_token(subject=user.id)
    token = Token(access_token=access_token)
    resp = UserPublicToken(
        email=user.email, first_name=user.first_name, last_name=user.last_name,
        is_superuser=user.is_superuser, id=user.id, token=token
    )
    return resp


# ----------------------------------------- #
#             End Model Section             #

router = APIRouter()


@app.get("/")
def read_root():
    return {"Welcome to": "My first FastAPI deployment using AWS Lambda"}


@app.get("/ping", status_code=status.HTTP_200_OK)
async def ping():
    return {"message": "pong"}


@router.get("/{text}")
def read_item(text: str):
    return JSONResponse({"result": text})


@router.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return JSONResponse({"item_id": item_id, "q": q})


@router.post("/login", response_model=UserPublicToken)
async def login_user(session: SessionDep, user_in: UserLogin) -> Any:
    """
    Log in a user.
    """
    user = verify_and_generate_token(
        session=session, email=user_in.email, password=user_in.password)
    print(user)
    return user


@router.post("/chat/rag", response_model=Any)
async def retrieval_augmented_generation(query: UserQuery) -> Any:
    """
    Do RAG.
    """
    stream = retrieve_and_generate(prompt=query.prompt)

    return StreamingResponse(generate_text_chunks(stream), media_type="text/event-stream")


app.include_router(router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
