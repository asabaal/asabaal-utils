"""
Shared API confirmation module for all PR analyzer stages
Provides centralized paid API confirmation functionality
"""

import sys

# Global flag to track if user has confirmed paid API usage for this run
_paid_api_confirmed = False

def require_paid_api_confirmation(backend_type: str) -> bool:
    """Require user confirmation before making paid API calls
    
    Args:
        backend_type: The type of backend being used (e.g., 'openrouter', 'claude', 'ollama')
        
    Returns:
        bool: True if API calls should proceed, False if they should be blocked
    """
    global _paid_api_confirmed
    
    # Only require confirmation for paid APIs
    if backend_type.lower() not in ['openrouter', 'claude']:
        return True
    
    if _paid_api_confirmed:
        return True
    
    print("\n" + "="*60)
    print("🚨 PAID API CONFIRMATION REQUIRED")
    print("="*60)
    print(f"You are about to use the {backend_type.upper()} API, which costs money.")
    print("This will make API calls that consume your credits/budget.")
    print("")
    print("Type 'CONFIRM' to proceed with paid API calls:")
    print("Type anything else to cancel:")
    
    try:
        user_input = input("> ").strip().upper()
        if user_input == 'CONFIRM':
            _paid_api_confirmed = True
            print("✅ Paid API usage confirmed for this run.")
            print("="*60)
            return True
        else:
            print("❌ Paid API usage cancelled by user.")
            print("="*60)
            return False
    except (KeyboardInterrupt, EOFError):
        print("\n❌ Paid API usage cancelled.")
        print("="*60)
        return False

def reset_confirmation_state():
    """Reset the confirmation state (for testing)"""
    global _paid_api_confirmed
    _paid_api_confirmed = False

def is_confirmed() -> bool:
    """Check if paid API usage has been confirmed"""
    return _paid_api_confirmed