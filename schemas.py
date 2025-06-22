from pydantic import BaseModel , EmailStr
from datetime import date

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