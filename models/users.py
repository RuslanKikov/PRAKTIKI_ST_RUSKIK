from typing import Optional
from sqlmodel import SQLModel, Field
from pydantic import EmailStr

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: EmailStr
    password: str

class UserSignIn(SQLModel):
    email: EmailStr
    password: str
