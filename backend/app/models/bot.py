from typing import Optional, Text

from sqlmodel import Field, SQLModel


class UserQuery(SQLModel):
    prompt: Text
    collection: Optional[Text] = Field(None, description="Collection to query")
