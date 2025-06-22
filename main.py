from datetime import timedelta
from fastapi import FastAPI , Depends ,HTTPException
from sqlmodel import Session

#authentication
from auth import authenticate , create_access_token , get_current_user , hash_password , verify_hash_password , ACCESS_TOKEN_EXPIRY_MINUTES
from fastapi.security import OAuth2PasswordRequestForm

#models and schemas
from models import User
from schemas import UserCreate , UserRead , Token

#database
from database import get_session , create_db

app = FastAPI()

@app.on_event('startup')
def create_database_instance():
    create_db()

@app.post('/register' ,response_model= UserRead ,  tags=['User'])
def register(user:UserCreate , session : Session = Depends(get_session)):
    new_password = hash_password(user.password)
    new_user = User(username=user.username , email=user.email , password=new_password)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user

@app.post('/token' , response_model=Token , tags=['User'])
def login(form_data : OAuth2PasswordRequestForm = Depends(), session:Session = Depends(get_session)):
    user = authenticate(form_data.username , form_data.password , session)
    if not user:
        raise HTTPException (status_code=401 , detail="User not found")
    access_token = create_access_token(data = {"sub":user.username},expiry_time=timedelta(minutes=ACCESS_TOKEN_EXPIRY_MINUTES))
    return {"access_token":access_token ,"token_type":"bearer"}

@app.get("/user/me", response_model=UserRead )
def get_logged_user(current_user: User = Depends(get_current_user)):
    return current_user
