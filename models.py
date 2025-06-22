# creating a User Model

from sqlmodel import SQLModel , Field
from typing import Optional
from pydantic import EmailStr
from datetime import date

class User(SQLModel , table = True):
    id : Optional[int] = Field(default=None , primary_key=True)
    username : str = Field(unique= True , index= True)
    email : EmailStr
    password : str
    created_at : date = Field(default_factory=date.today)
