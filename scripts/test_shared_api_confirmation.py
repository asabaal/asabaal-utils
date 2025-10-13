#!/usr/bin/env python3
"""
Simple test for the shared API confirmation module
"""

import sys
import unittest
from unittest.mock import patch, MagicMock
from io import StringIO

# Add the parent directory to path for imports
sys.path.insert(0, 'src')

# Import the shared confirmation module directly
from asabaal_utils.pr_analyzer.api_confirmation import require_paid_api_confirmation, reset_confirmation_state, is_confirmed


class TestSharedAPIConfirmation(unittest.TestCase):
    """Test the shared API confirmation functionality"""
    
    def setUp(self):
        """Reset global confirmation state before each test"""
        reset_confirmation_state()
    
    def test_free_api_no_confirmation_required(self):
        """Test that free APIs (ollama) don't require confirmation"""
        print("\n🧪 Testing: Free APIs should not require confirmation")
        
        # Test ollama
        self.assertTrue(require_paid_api_confirmation('ollama'))
        self.assertTrue(require_paid_api_confirmation('OLLAMA'))
        self.assertTrue(require_paid_api_confirmation('Ollama'))
        
        print("✅ Free APIs correctly skip confirmation")
    
    @patch('builtins.input', return_value='CONFIRM')
    def test_paid_api_user_confirms(self, mock_input):
        """Test that paid APIs proceed when user types CONFIRM"""
        print("\n🧪 Testing: Paid APIs proceed when user confirms")
        
        # First call should ask for confirmation
        self.assertTrue(require_paid_api_confirmation('openrouter'))
        
        # Should not ask again for the same or other paid APIs
        self.assertTrue(require_paid_api_confirmation('claude'))
        self.assertTrue(require_paid_api_confirmation('openrouter'))
        
        # Should only have asked once
        self.assertEqual(mock_input.call_count, 1)
        self.assertTrue(is_confirmed())
        
        print("✅ Paid API confirmation works correctly")
    
    @patch('builtins.input', return_value='cancel')
    def test_paid_api_user_cancels(self, mock_input):
        """Test that paid APIs are cancelled when user types anything else"""
        print("\n🧪 Testing: Paid APIs cancelled when user rejects")
        
        # Should return False when user cancels
        self.assertFalse(require_paid_api_confirmation('openrouter'))
        
        # Should ask again for subsequent calls
        self.assertFalse(require_paid_api_confirmation('claude'))
        
        # Should have asked twice
        self.assertEqual(mock_input.call_count, 2)
        self.assertFalse(is_confirmed())
        
        print("✅ Paid API cancellation works correctly")
    
    @patch('builtins.input', side_effect=EOFError())
    def test_eof_handling(self, mock_input):
        """Test that EOF errors are handled gracefully"""
        print("\n🧪 Testing: EOF error handling")
        
        # Should return False when EOF occurs
        self.assertFalse(require_paid_api_confirmation('openrouter'))
        
        print("✅ EOF handling works correctly")
    
    @patch('builtins.input', side_effect=KeyboardInterrupt())
    def test_keyboard_interrupt_handling(self, mock_input):
        """Test that keyboard interrupts are handled gracefully"""
        print("\n🧪 Testing: Keyboard interrupt handling")
        
        # Should return False when KeyboardInterrupt occurs
        self.assertFalse(require_paid_api_confirmation('openrouter'))
        
        print("✅ KeyboardInterrupt handling works correctly")
    
    def test_case_insensitive_confirmation(self):
        """Test that CONFIRM is case insensitive"""
        print("\n🧪 Testing: Case insensitive confirmation")
        
        with patch('builtins.input', return_value='confirm'):
            self.assertTrue(require_paid_api_confirmation('openrouter'))
        
        with patch('builtins.input', return_value='Confirm'):
            reset_confirmation_state()
            self.assertTrue(require_paid_api_confirmation('openrouter'))
        
        with patch('builtins.input', return_value='CONFIRM'):
            reset_confirmation_state()
            self.assertTrue(require_paid_api_confirmation('openrouter'))
        
        print("✅ Confirmation is case insensitive")
    
    def test_rejection_variations(self):
        """Test that various rejection inputs work correctly"""
        print("\n🧪 Testing: Various rejection inputs")
        
        rejection_texts = ['no', 'NO', 'cancel', 'CANCEL', 'x', 'anything', '', '123']
        
        for rejection_text in rejection_texts:
            with patch('builtins.input', return_value=rejection_text):
                reset_confirmation_state()
                result = require_paid_api_confirmation('openrouter')
                self.assertFalse(result, f"Should reject '{rejection_text}'")
        
        print("✅ Various rejection inputs work correctly")


if __name__ == '__main__':
    print("=" * 80)
    print("🔒 SHARED API CONFIRMATION SECURITY TESTS")
    print("=" * 80)
    
    unittest.main(verbosity=2)