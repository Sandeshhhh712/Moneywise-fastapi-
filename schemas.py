from pydantic import BaseModel
from datetime import date

class UserCreate(BaseModel):
    username : str
    email : str
    password : str

class UserRead(BaseModel):
    id : int
    username: str
    email : str
    created_at : date

class Token(BaseModel):
    access_token : str
    token_type : str