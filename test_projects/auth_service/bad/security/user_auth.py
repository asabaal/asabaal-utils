# CRITICAL SECURITY VULNERABILITIES - BAD CODE

class SimpleDatabase:
    def __init__(self):
        self.users = {}
        
    def get_user(self, username):
        return self.users.get(username)

db = SimpleDatabase()

def authenticate_user(username, password):
    """PLAIN TEXT PASSWORD COMPARISON - CRITICAL SECURITY FLAW"""
    user = db.get_user(username)
    
    # CRITICAL: Comparing plain text passwords
    if user and user.password == password:  # NEVER DO THIS!
        return generate_token(username)
    return None

def generate_token(username):
    """Insecure token generation"""
    # Predictable token - can be easily guessed
    import time
    token = f"{username}_{int(time.time())}"
    return token

def create_user(username, password, email):
    """Store password in plain text - CRITICAL SECURITY ISSUE"""
    if username in db.users:
        raise ValueError("User already exists")
    
    # CRITICAL: Storing plain text password
    user = {
        'username': username,
        'password': password,  # PLAIN TEXT!
        'email': email,
        'created_at': 'now'
    }
    
    db.users[username] = user
    return user

def login_without_rate_limiting(username, password):
    """Login with no rate limiting - vulnerable to brute force"""
    # No attempt counting, no delays, no protection
    return authenticate_user(username, password)

def reset_password_insecure(username, new_password):
    """Insecure password reset"""
    user = db.get_user(username)
    if user:
        # Set new password without verification
        user['password'] = new_password  # Still plain text!
        return True
    return False

def verify_token_insecure(token):
    """Insecure token verification"""
    # Token is just username_timestamp - easily forgeable
    if '_' in token:
        username, timestamp = token.split('_', 1)
        return db.get_user(username)
    return None