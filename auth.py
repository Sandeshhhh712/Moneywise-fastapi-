from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session , select
from database import get_session
from models import User
from datetime import timedelta , timezone ,datetime
from fastapi import Depends , HTTPException
from jose import jwt , JWTError




SECRET_KEY = "3ef77f2a8c8db6f7fcf987cc0ac6510fccb18bc46c2f341d00e20ff0549d09e6"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRY_MINUTES = 30

pwd_context = CryptContext(schemes=['bcrypt'])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

#User verification and password hashing

def hash_password(password):
    return pwd_context.hash(password)

def verify_hash_password(plain , hashed):
    return pwd_context.verify(plain , hashed)

def authenticate(username : str , password : str , session:Session):
    user = session.exec(select(User).where(User.username == username)).first()
    if not user:
        return None
    return user

#Token generation and verification

def create_access_token(data:dict , expiry_time : timedelta | None = None ):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expiry_time or timedelta(minutes=15))
    to_encode.update({"exp":expire})
    return jwt.encode(to_encode , SECRET_KEY , algorithm=ALGORITHM)

def get_current_user(token : str = Depends(oauth2_scheme) , session : Session = Depends(get_session)):
    try:
        payload = jwt.decode(token , SECRET_KEY ,algorithms=[ALGORITHM])
        username : str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401 , detail='Unauthorized')
    except JWTError:
        raise HTTPException(status_code=401 , detail="Unauthorized")
    user = session.exec(select(User).where(User.username == username)).first()
    if not user:
        raise HTTPException(status_code=401 , detail="User does not exist")
    return user
