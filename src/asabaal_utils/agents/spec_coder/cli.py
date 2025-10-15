#!/usr/bin/env python3
"""
spec-coder CLI

Command-line interface for the OpenSpec-driven autonomous coding agent.
"""

import sys
import argparse
import logging
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    # Try relative imports first (when installed as package)
    from .generator import CodeGenerator
    from .tester import TestAnalyzer  
    from .healer import FailurePatcher
    from .organizer import CodeOrganizer
    from .orchestrator import IntegrationOrchestrator
except ImportError:
    # Fall back to absolute imports (when running directly)
    from generator import CodeGenerator
    from tester import TestAnalyzer  
    from healer import FailurePatcher
    from organizer import CodeOrganizer
    from orchestrator import IntegrationOrchestrator


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def cmd_generate(args):
    """Generate code from spec."""
    setup_logging(args.verbose)
    
    if not args.spec_file.exists():
        print(f"Error: Specification file not found: {args.spec_file}")
        return 1
    
    try:
        generator = CodeGenerator()
        print(f"Generating code from: {args.spec_file}")
        result = generator.generate_from_spec(args.spec_file, args.output)
        
        if result.success:
            print(f"✅ Generation completed successfully!")
            print(f"📁 Generated {len(result.files_generated)} files:")
            for file_path in result.files_generated:
                print(f"   - {file_path}")
            print(f"⏱️  Execution time: {result.execution_time:.2f}s")
            
            if result.warnings:
                print(f"⚠️  Warnings:")
                for warning in result.warnings:
                    print(f"   - {warning}")
            return 0
        else:
            print(f"❌ Generation failed!")
            for error in result.errors:
                print(f"   - {error}")
            return 1
            
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cmd_test(args):
    """Run automated tests."""
    setup_logging(args.verbose)
    
    try:
        tester = TestAnalyzer()
        print("🧪 Running automated tests...")
        success = tester.run_tests()
        
        if success:
            print("✅ All tests passed!")
            return 0
        else:
            print("❌ Some tests failed!")
            return 1
            
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cmd_heal(args):
    """Repair failing tests."""
    setup_logging(args.verbose)
    
    try:
        healer = FailurePatcher()
        print("🧩 Starting healing process...")
        success = healer.run()
        
        if success:
            print("✅ Healing completed successfully!")
            return 0
        else:
            print("⚠️ Healing completed with some issues")
            return 1
            
    except Exception as e:
        print(f"❌ Healing failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cmd_organize(args):
    """Restructure code."""
    setup_logging(args.verbose)
    
    try:
        organizer = CodeOrganizer()
        print("📁 Starting code organization...")
        success = organizer.run()
        
        if success:
            print("✅ Code organization completed!")
            return 0
        else:
            print("❌ Code organization failed!")
            return 1
            
    except Exception as e:
        print(f"❌ Organization failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cmd_full_run(args):
    """Run the entire pipeline."""
    setup_logging(args.verbose)
    
    if not args.spec_file.exists():
        print(f"Error: Specification file not found: {args.spec_file}")
        return 1
    
    try:
        runner = IntegrationOrchestrator()
        print("🚀 Starting full pipeline...")
        success = runner.run_full_pipeline(args.spec_file, args.output)
        
        if success:
            print("✅ Full pipeline completed successfully!")
            return 0
        else:
            print("❌ Pipeline failed!")
            return 1
            
    except Exception as e:
        print(f"❌ Pipeline execution failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="OpenSpec-driven autonomous coding agent"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate code from spec')
    gen_parser.add_argument(
        'spec_file',
        type=Path,
        help='Path to the OpenSpec YAML file'
    )
    gen_parser.add_argument(
        '-o', '--output',
        type=Path,
        default=None,
        help='Output directory (default: ./output)'
    )
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Run automated tests')
    
    # Heal command
    heal_parser = subparsers.add_parser('heal', help='Repair failing tests')
    
    # Organize command
    org_parser = subparsers.add_parser('organize', help='Restructure code')
    
    # Full run command
    full_parser = subparsers.add_parser('full-run', help='Run the entire pipeline')
    full_parser.add_argument(
        'spec_file',
        type=Path,
        help='Path to the OpenSpec YAML file'
    )
    full_parser.add_argument(
        '-o', '--output',
        type=Path,
        default=None,
        help='Output directory (default: ./output)'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Route to appropriate command
    if args.command == 'generate':
        return cmd_generate(args)
    elif args.command == 'test':
        return cmd_test(args)
    elif args.command == 'heal':
        return cmd_heal(args)
    elif args.command == 'organize':
        return cmd_organize(args)
    elif args.command == 'full-run':
        return cmd_full_run(args)
    else:
        print(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())