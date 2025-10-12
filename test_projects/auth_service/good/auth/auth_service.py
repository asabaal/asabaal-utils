import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class User:
    id: int
    username: str
    email: str
    password_hash: str
    is_active: bool = True
    created_at: Optional[datetime] = None

@dataclass
class AuthToken:
    token: str
    expires_at: datetime
    user_id: int

class AuthService:
    def __init__(self, secret_key: str, token_expiry_hours: int = 24):
        self.secret_key = secret_key
        self.token_expiry = timedelta(hours=token_expiry_hours)
        
    def hash_password(self, password: str) -> str:
        """Secure password hashing using bcrypt"""
        if not password or len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
            
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
        
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against secure hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception:
            return False
            
    def generate_token(self, user: User) -> AuthToken:
        """Generate secure JWT token"""
        payload = {
            'user_id': user.id,
            'username': user.username,
            'exp': datetime.utcnow() + self.token_expiry,
            'iat': datetime.utcnow()
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        expires_at = datetime.utcnow() + self.token_expiry
        
        return AuthToken(token=token, expires_at=expires_at, user_id=user.id)
        
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
            
    def authenticate_user(self, username: str, password: str, user_db: Dict[str, User]) -> Optional[AuthToken]:
        """Authenticate user with proper security measures"""
        if not username or not password:
            return None
            
        user = user_db.get(username)
        if not user or not user.is_active:
            return None
            
        if not self.verify_password(password, user.password_hash):
            return None
            
        return self.generate_token(user)
        
    def create_user(self, username: str, email: str, password: str, user_db: Dict[str, User]) -> User:
        """Create new user with secure password handling"""
        if not username or not email or not password:
            raise ValueError("All fields are required")
            
        if username in user_db:
            raise ValueError("Username already exists")
            
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
            
        # Generate new user ID
        new_id = max([user.id for user in user_db.values()], default=0) + 1
        
        password_hash = self.hash_password(password)
        
        user = User(
            id=new_id,
            username=username,
            email=email,
            password_hash=password_hash,
            created_at=datetime.utcnow()
        )
        
        user_db[username] = user
        return user