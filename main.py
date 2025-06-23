from datetime import timedelta
from fastapi import FastAPI , Depends ,HTTPException
from sqlmodel import Session, select
from enum import Enum
from sqlalchemy.orm import selectinload
#authentication
from auth import authenticate , create_access_token , get_current_user , hash_password , verify_hash_password , ACCESS_TOKEN_EXPIRY_MINUTES
from fastapi.security import OAuth2PasswordRequestForm

#models and schemas
from models import User , Category , Transaction
from schemas import UserCreate , UserRead , Token , CategoryCreate , CategoryRead , TransactionCreate , TransactionRead , categoryinfo

#database
from database import get_session , create_db

class Tags(str , Enum):
    User = "User"
    Category = "Category"
    Transaction = "Transaction"

app = FastAPI()

@app.on_event('startup')
def create_database_instance():
    create_db()

@app.post('/register' ,response_model= UserRead ,  tags=[Tags.User.value])
def register(user:UserCreate , session : Session = Depends(get_session)):
    new_password = hash_password(user.password)
    new_user = User(username=user.username , email=user.email , password=new_password)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user

@app.post('/token' , response_model=Token , tags=[Tags.User.value])
def login(form_data : OAuth2PasswordRequestForm = Depends(), session:Session = Depends(get_session)):
    user = authenticate(form_data.username , form_data.password , session)
    if not user:
        raise HTTPException (status_code=401 , detail="User not found")
    access_token = create_access_token(data = {"sub":user.username},expiry_time=timedelta(minutes=ACCESS_TOKEN_EXPIRY_MINUTES))
    return {"access_token":access_token ,"token_type":"bearer"}

#Category

@app.post("/category/add" ,response_model=CategoryRead , tags=[Tags.Category.value])
def add_category(category : CategoryCreate , session: Session = Depends(get_session), current_user : User = Depends(get_current_user)):
    new_category = Category(name=category.name , user_id=current_user.id)
    session.add(new_category)
    session.commit()
    session.refresh(new_category)
    return new_category

#Category List

@app.get("/category/all" ,response_model=list[CategoryRead] , tags=[Tags.Category.value])
def all_category(session: Session = Depends(get_session) , current_user :User = Depends(get_current_user)):
    user = current_user.id
    categories = session.exec(select(Category).where(Category.user_id == user)).all()
    return categories

#Category Delete

@app.delete("/category/delete/{category_id}", tags=[Tags.Category.value])
def delete_category(
    category_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    category = session.get(Category, category_id)

    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    if category.user_id != current_user.id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    session.delete(category)
    session.commit()
    return {"detail": "Deleted"}


#Transaction

@app.post("/transactions/add" , response_model=TransactionRead , tags=[Tags.Transaction.value])
def add_transactions(transactions : TransactionCreate , session:Session = Depends(get_session) , current_user : User = Depends(get_current_user)):
    new_transaction = Transaction(user_id=current_user.id ,title=transactions.title , amount= transactions.amount , type = transactions.type , category_id=transactions.category_id , optional_notes=transactions.optional_notes)
    session.add(new_transaction)
    session.commit()
    session.refresh(new_transaction)
    return new_transaction


#Transaction History

@app.get("/transactions/history" ,response_model=list[TransactionRead] , tags=[Tags.Transaction.value])
def all_transactions(session : Session = Depends(get_session) , current_user : User = Depends(get_current_user)):
    user = current_user.id
    transactions = session.exec(select(Transaction).where(Transaction.user_id ==user).options(selectinload(Transaction.category))).all()
    
    return [
        TransactionRead(
            id=i.id,
            title =i.title,
            amount=i.amount,
            type=i.type,
            category = categoryinfo(
                id = i.category.id,
                name= i.category.name
            )if i.category else None,
            date_added=i.date_added,
            optional_notes=i.optional_notes

        )
        for i in transactions
    ]

#Transaction Delete

@app.delete("/transactions/delete/{transaction_id}", tags=[Tags.Transaction.value])
def delete_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    transaction = session.get(Transaction, transaction_id)

    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if transaction.user_id != current_user.id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    session.delete(transaction)
    session.commit()
    return {"detail": "Deleted"}
