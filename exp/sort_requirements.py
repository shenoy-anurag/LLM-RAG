reqs = """
alembic
bcrypt
langchain
langchain-community
langchain-core
langchain-openai
langchain-qdrant
langchain-text-splitters
langchain_community
qdrant-client
tiktoken
openai
numpy
fastapi[standard]
PyJWT
pydantic
SQLAlchemy
sqlmodel
websockets
pytz
python-dotenv
"""

print("\n".join(sorted([r for r in reqs.split("\n") if r])))
