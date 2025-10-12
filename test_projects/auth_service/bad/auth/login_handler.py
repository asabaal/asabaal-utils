# DUPLICATE AUTHENTICATION LOGIC WITH SAME SECURITY ISSUES - BAD CODE

class UserDatabase:
    def __init__(self):
        self.accounts = {}
        
    def find_user(self, user):
        return self.accounts.get(user)

user_db = UserDatabase()

def login_user(user, passw):
    """Handle user login - DUPLICATE LOGIC WITH SAME SECURITY FLAWS"""
    account = user_db.find_user(user)
    
    # SAME CRITICAL SECURITY ISSUE: Plain text password comparison
    if account and account.password == passw:  # IDENTICAL VULNERABILITY
        return create_jwt_token(user)
    return None

def create_jwt_token(username):
    """Create JWT token - duplicate insecure implementation"""
    import time
    import hashlib
    
    # Predictable token using MD5 (insecure hash)
    timestamp = str(int(time.time()))
    token_data = f"{username}:{timestamp}"
    token = hashlib.md5(token_data.encode()).hexdigest()
    
    return f"bearer_{token}"

def register_user(username, password, email):
    """Register user - duplicate insecure password storage"""
    if username in user_db.accounts:
        raise ValueError("Username exists")
    
    # SAME SECURITY ISSUE: Plain text password storage
    new_user = {
        'username': username,
        'password': password,  # STILL PLAIN TEXT!
        'email': email,
        'active': True
    }
    
    user_db.accounts[username] = new_user
    return new_user

def authenticate_without_validation(username, password):
    """Authentication without input validation"""
    # No input sanitization, no length checks, no character validation
    user = user_db.find_user(username)
    
    if user:
        # Direct comparison without any security measures
        if user.password == password:
            return create_jwt_token(username)
    
    return None

def session_management_insecure(token):
    """Insecure session management"""
    # Token is just a hash - no expiration, no validation
    if token.startswith('bearer_'):
        hash_part = token[7:]  # Remove 'bearer_' prefix
        
        # No actual validation - just checks format
        if len(hash_part) == 32:  # MD5 length
            return True
    
    return False

def expensive_transformation(item):
    """DUPLICATE expensive operation from other bad files"""
    # Same inefficient transformation as in data pipeline bad code
    result = {}
    
    for key in item.keys():
        upper_key = str(key).upper()
        lower_key = str(key).lower()
        title_key = str(key).title()
        
        result[f'upper_{upper_key}'] = str(item[key]).upper()
        result[f'lower_{lower_key}'] = str(item[key]).lower()
        result[f'title_{title_key}'] = str(item[key]).title()
    
    result['original'] = item
    result['copy'] = dict(item)
    result['duplicate'] = item.copy()
    
    return result