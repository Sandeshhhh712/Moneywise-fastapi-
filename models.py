# creating a User Model

from sqlmodel import Relationship, SQLModel , Field
from typing import Optional
from pydantic import EmailStr
from datetime import date
from enum import Enum


class TransactionType(str , Enum):
    income = "income"
    expense = "expense"


class User(SQLModel , table = True):
    id : Optional[int] = Field(default=None , primary_key=True)
    username : str = Field(unique= True , index= True)
    email : EmailStr
    password : str
    created_at : date = Field(default_factory=date.today)

    transactions : list['Transaction'] = Relationship(back_populates="user")
    category : list['Category'] = Relationship(back_populates="user")


class Category(SQLModel , table=True):
    id : Optional[int] = Field(default=None , primary_key=True)
    name : str

    user_id : int = Field(foreign_key="user.id")
    user : Optional['User'] = Relationship(back_populates="category")

    transactions : list["Transaction"] = Relationship(back_populates="category")

class Transaction(SQLModel , table = True):
    id : Optional[int] = Field(default=None , primary_key=True)
    title : str = Field(index=True)
    amount : int
    type : TransactionType = Field(default=TransactionType.expense)

    category_id : Optional[int] = Field(default=None , foreign_key="category.id")
    category : Optional[Category] = Relationship(back_populates="transactions")

    date_added : date = Field(default_factory=date.today)
    optional_notes : str | None = Field(default=None)

    user_id : int = Field(foreign_key="user.id")
    user : Optional["User"] = Relationship(back_populates = "transactions")

Transaction.update_forward_refs() # because model has been called before it had been made
Category.update_forward_refs()
User.update_forward_refs()


 
