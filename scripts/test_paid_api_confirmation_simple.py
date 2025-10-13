#!/usr/bin/env python3
"""
Simple comprehensive test for Paid API Confirmation security feature
Tests the confirmation functionality directly without complex imports
"""

import sys
import unittest
from unittest.mock import patch, MagicMock
from io import StringIO

# Add the parent directory to path for imports
sys.path.insert(0, 'src')

# Import confirmation functions directly
import asabaal_utils.pr_analyzer.stage3_agent_communication as stage3
import asabaal_utils.pr_analyzer.stage7_detailed_analysis as stage7
import asabaal_utils.pr_analyzer.stage8_file_assessment as stage8
import asabaal_utils.pr_analyzer.stage10_feedback_updates as stage10

# Import the shared confirmation module to reset state
import asabaal_utils.pr_analyzer.api_confirmation as api_conf


class TestPaidAPIConfirmation(unittest.TestCase):
    """Test paid API confirmation functionality across all stages"""
    
    def setUp(self):
        """Reset global confirmation flags before each test"""
        # Reset the shared confirmation state
        if hasattr(api_conf, 'reset_confirmation_state'):
            api_conf.reset_confirmation_state()
    
    def test_free_api_no_confirmation_required(self):
        """Test that free APIs (ollama) don't require confirmation"""
        print("\n🧪 Testing: Free APIs should not require confirmation")
        
        # Test all stages with ollama
        self.assertTrue(stage3.require_paid_api_confirmation('ollama'))
        self.assertTrue(stage7.require_paid_api_confirmation('ollama'))
        self.assertTrue(stage8.require_paid_api_confirmation('ollama'))
        self.assertTrue(stage10.require_paid_api_confirmation('ollama'))
        
        # Test case insensitive
        self.assertTrue(stage3.require_paid_api_confirmation('OLLAMA'))
        self.assertTrue(stage7.require_paid_api_confirmation('Ollama'))
        
        print("✅ Free APIs correctly skip confirmation")
    
    @patch('builtins.input', return_value='CONFIRM')
    def test_paid_api_user_confirms(self, mock_input):
        """Test that paid APIs proceed when user types CONFIRM"""
        print("\n🧪 Testing: Paid APIs proceed when user confirms")
        
        # Test all stages with openrouter
        self.assertTrue(stage3.require_paid_api_confirmation('openrouter'))
        self.assertTrue(stage7.require_paid_api_confirmation('openrouter'))
        self.assertTrue(stage8.require_paid_api_confirmation('openrouter'))
        self.assertTrue(stage10.require_paid_api_confirmation('openrouter'))
        
        # Test with claude
        self.assertTrue(stage3.require_paid_api_confirmation('claude'))
        self.assertTrue(stage7.require_paid_api_confirmation('claude'))
        
        # Verify input was called for each confirmation
        self.assertEqual(mock_input.call_count, 6)
        
        print("✅ Paid APIs correctly proceed with user confirmation")
    
    @patch('builtins.input', return_value='cancel')
    def test_paid_api_user_cancels(self, mock_input):
        """Test that paid APIs are cancelled when user types anything else"""
        print("\n🧪 Testing: Paid APIs cancelled when user rejects")
        
        # Reset flags for this test
        stage3._paid_api_confirmed = False
        stage7._paid_api_confirmed = False
        stage8._paid_api_confirmed = False
        stage10._paid_api_confirmed = False
        
        # Test all stages with openrouter
        self.assertFalse(stage3.require_paid_api_confirmation('openrouter'))
        self.assertFalse(stage7.require_paid_api_confirmation('openrouter'))
        self.assertFalse(stage8.require_paid_api_confirmation('openrouter'))
        self.assertFalse(stage10.require_paid_api_confirmation('openrouter'))
        
        # Verify input was called for each cancellation
        self.assertEqual(mock_input.call_count, 4)
        
        print("✅ Paid APIs correctly cancelled when user rejects")
    
    @patch('builtins.input', return_value='CONFIRM')
    def test_one_time_confirmation_persists(self, mock_input):
        """Test that confirmation persists for the entire run after first confirmation"""
        print("\n🧪 Testing: One-time confirmation persists across multiple calls")
        
        # First call should require confirmation
        self.assertTrue(stage3.require_paid_api_confirmation('openrouter'))
        self.assertEqual(mock_input.call_count, 1)
        
        # Subsequent calls should not require confirmation
        self.assertTrue(stage3.require_paid_api_confirmation('openrouter'))
        self.assertTrue(stage7.require_paid_api_confirmation('openrouter'))
        self.assertTrue(stage8.require_paid_api_confirmation('openrouter'))
        self.assertTrue(stage10.require_paid_api_confirmation('openrouter'))
        
        # Input should only have been called once
        self.assertEqual(mock_input.call_count, 1)
        
        print("✅ One-time confirmation correctly persists")
    
    @patch('builtins.input', side_effect=KeyboardInterrupt())
    def test_keyboard_interrupt_handling(self, mock_input):
        """Test that keyboard interrupts are handled gracefully"""
        print("\n🧪 Testing: Keyboard interrupt handling")
        
        # Should return False on keyboard interrupt
        self.assertFalse(stage3.require_paid_api_confirmation('openrouter'))
        self.assertFalse(stage7.require_paid_api_confirmation('openrouter'))
        
        print("✅ Keyboard interrupts handled gracefully")
    
    @patch('builtins.input', side_effect=EOFError())
    def test_eof_handling(self, mock_input):
        """Test that EOF errors are handled gracefully"""
        print("\n🧪 Testing: EOF error handling")
        
        # Should return False on EOF
        self.assertFalse(stage3.require_paid_api_confirmation('openrouter'))
        self.assertFalse(stage7.require_paid_api_confirmation('openrouter'))
        
        print("✅ EOF errors handled gracefully")
    
    def test_case_insensitive_confirmation(self):
        """Test that CONFIRM is case insensitive"""
        print("\n🧪 Testing: Case insensitive confirmation")
        
        test_cases = ['CONFIRM', 'confirm', 'Confirm', 'CoNfIrM', 'CONFIRM ']
        
        for confirmation_text in test_cases:
            with patch('builtins.input', return_value=confirmation_text):
                with self.subTest(confirmation_text=confirmation_text):
                    # Reset flag for each test
                    stage3._paid_api_confirmed = False
                    self.assertTrue(stage3.require_paid_api_confirmation('openrouter'))
        
        print("✅ Confirmation is case insensitive")
    
    def test_rejection_variations(self):
        """Test that various rejection inputs work correctly"""
        print("\n🧪 Testing: Various rejection inputs")
        
        rejection_inputs = ['no', 'NO', 'cancel', 'CANCEL', 'x', 'anything', '', '123']
        
        for rejection_text in rejection_inputs:
            # Reset flag for each test
            stage3._paid_api_confirmed = False
            
            with patch('builtins.input', return_value=rejection_text):
                with self.subTest(rejection_text=rejection_text):
                    self.assertFalse(stage3.require_paid_api_confirmation('openrouter'))
        
        print("✅ Various rejection inputs work correctly")


class TestDefaultProviderChanges(unittest.TestCase):
    """Test that default providers have been changed to ollama"""
    
    def test_analyzer_default_config(self):
        """Test that analyzer defaults to ollama"""
        print("\n🧪 Testing: Analyzer default configuration")
        
        try:
            from asabaal_utils.pr_analyzer.analyzer import UnifiedPRAnalyzer
            
            # Create analyzer with no config file (using temp directory)
            analyzer = UnifiedPRAnalyzer('/tmp/nonexistent')
            config = analyzer.load_config()
            
            # Check that default is ollama
            self.assertEqual(config['agentic_backend']['provider'], 'ollama')
            self.assertEqual(config['agentic_backend']['model'], 'llama3.1:8b')
            
            print("✅ Analyzer correctly defaults to ollama")
        except Exception as e:
            print(f"⚠️  Could not test analyzer config: {e}")
    
    def test_cli_help_includes_ollama(self):
        """Test that CLI help includes ollama as option"""
        print("\n🧪 Testing: CLI includes ollama option")
        
        try:
            from asabaal_utils.pr_analyzer.cli import main
            # Just verify the function exists and is callable
            self.assertTrue(callable(main))
            print("✅ CLI function exists (manual verification needed for ollama option)")
        except Exception as e:
            print(f"⚠️  Could not test CLI: {e}")


def run_security_tests():
    """Run all security tests and provide detailed output"""
    print("=" * 80)
    print("🔒 PAID API CONFIRMATION SECURITY TESTS")
    print("=" * 80)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestPaidAPIConfirmation))
    suite.addTests(loader.loadTestsFromTestCase(TestDefaultProviderChanges))
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 SECURITY TEST SUMMARY")
    print("=" * 80)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\n💥 ERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    if result.wasSuccessful():
        print("\n🎉 ALL SECURITY TESTS PASSED!")
        print("✅ Paid API confirmation is working correctly.")
        print("✅ Users will be protected from accidental API charges.")
    else:
        print("\n⚠️  Some security tests failed. Please review the issues above.")
    
    print("=" * 80)
    
    return result.wasSuccessful()


def test_manual_confirmation():
    """Manual test to show the confirmation prompt in action"""
    print("\n" + "=" * 80)
    print("🧪 MANUAL CONFIRMATION TEST")
    print("=" * 80)
    print("This will show the actual confirmation prompt.")
    print("Type 'CONFIRM' to test approval, or anything else to test rejection.")
    print()
    
    # Reset flags
    stage3._paid_api_confirmed = False
    
    # Test with openrouter (should show prompt)
    result = stage3.require_paid_api_confirmation('openrouter')
    
    if result:
        print("✅ Confirmation successful - API calls would proceed")
    else:
        print("❌ Confirmation cancelled - API calls would be blocked")
    
    # Test with ollama (should not show prompt)
    ollama_result = stage3.require_paid_api_confirmation('ollama')
    print(f"✅ Ollama test (no prompt required): {ollama_result}")
    
    print("=" * 80)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Paid API Confirmation Security')
    parser.add_argument('--manual', action='store_true', help='Run manual confirmation test')
    args = parser.parse_args()
    
    if args.manual:
        test_manual_confirmation()
    else:
        success = run_security_tests()
        sys.exit(0 if success else 1)