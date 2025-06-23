from pydantic import BaseModel , EmailStr
from datetime import date
from models import TransactionType ,Category
from typing import Optional

class UserCreate(BaseModel):
    username : str
    email : EmailStr
    password : str

class UserRead(BaseModel):
    id : int
    username: str
    email : EmailStr
    created_at : date

class Token(BaseModel):
    access_token : str
    token_type : str

class CategoryCreate(BaseModel):
    name : str

class CategoryRead(BaseModel):
    id : int
    name : str

class TransactionCreate(BaseModel):
    title : str
    amount : int
    type : TransactionType
    category_id : int
    optional_notes : str | None = None

class categoryinfo(BaseModel):
    id : int
    name : str

class TransactionRead(BaseModel):
    id : int
    title : str
    amount : int
    type : TransactionType
    category : Optional[categoryinfo]
    date_added : date
    optional_notes :  str | None = None
    