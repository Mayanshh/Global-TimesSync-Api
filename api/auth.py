from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional, Dict
import jwt
import os
from passlib.context import CryptContext
import logging
from flask import request, jsonify, g

# Initialize router
router = APIRouter()

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# JWT Secret and configuration
SECRET_KEY = os.environ.get("JWT_SECRET", "insecure_default_secret_key_for_development")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Mock user database (would be replaced with a real database in production)
# In a real-world scenario, this would connect to a database
fake_users_db = {
    "testuser": {
        "username": "testuser",
        "full_name": "Test User",
        "email": "user@example.com",
        "hashed_password": pwd_context.hash("password123"),
        "disabled": False,
    }
}

# Models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

class UserInDB(User):
    hashed_password: str

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except jwt.PyJWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Routes
@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=User)
async def register_user(user: UserCreate):
    if user.username in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    
    # Create a new user with hashed password
    hashed_password = get_password_hash(user.password)
    
    # In a real application, you would save this to a database
    fake_users_db[user.username] = {
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "hashed_password": hashed_password,
        "disabled": False,
    }
    
    return {
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "disabled": False
    }

@router.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

# Flask-compatible functions
def login_for_access_token_flask():
    """
    Flask-compatible function for user login.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid request data"}), 400
            
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"error": "Missing username or password"}), 400
            
        user = authenticate_user(fake_users_db, username, password)
        if not user:
            return jsonify({"error": "Incorrect username or password"}), 401
            
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        return jsonify({"access_token": access_token, "token_type": "bearer"})
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        return jsonify({"error": "Login failed"}), 500

def register_user_flask():
    """
    Flask-compatible function for user registration.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid request data"}), 400
            
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        full_name = data.get('full_name')
        
        if not username or not email or not password:
            return jsonify({"error": "Missing required fields"}), 400
            
        if username in fake_users_db:
            return jsonify({"error": "Username already registered"}), 400
            
        # Create a new user with hashed password
        hashed_password = get_password_hash(password)
        
        # In a real application, you would save this to a database
        fake_users_db[username] = {
            "username": username,
            "email": email,
            "full_name": full_name,
            "hashed_password": hashed_password,
            "disabled": False,
        }
        
        return jsonify({
            "username": username,
            "email": email,
            "full_name": full_name,
            "disabled": False
        })
    except Exception as e:
        logger.error(f"Error during registration: {str(e)}")
        return jsonify({"error": "Registration failed"}), 500

def get_current_user_flask():
    """
    Flask-compatible function to get current user details.
    """
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Missing or invalid authorization header"}), 401
            
        token = auth_header.split(' ')[1]
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            if username is None:
                return jsonify({"error": "Invalid token"}), 401
                
            user = get_user(fake_users_db, username)
            if user is None:
                return jsonify({"error": "User not found"}), 401
                
            if user.disabled:
                return jsonify({"error": "Inactive user"}), 400
                
            return jsonify({
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "disabled": user.disabled
            })
        except jwt.PyJWTError:
            return jsonify({"error": "Invalid token"}), 401
    except Exception as e:
        logger.error(f"Error getting user: {str(e)}")
        return jsonify({"error": "Authentication failed"}), 500
