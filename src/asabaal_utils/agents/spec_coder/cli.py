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
    from .healer import Healer
    from .organizer import CodeOrganizer
    from .orchestrator import IntegrationOrchestrator
except ImportError:
    # Fall back to absolute imports (when running directly)
    from generator import CodeGenerator
    from tester import TestAnalyzer  
    from healer import Healer
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
        from .healer import Healer
        healer = Healer(healer_dir=Path.cwd())
        print("🧩 Starting healing process...")
        results = healer.heal_all_functions()
        success = all(r.success for r in results)
        
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


def cmd_stage1(args):
    """Stage 1: OpenSpec → Tests/Scaffold."""
    setup_logging(args.verbose)
    
    if not args.spec_file.exists():
        print(f"Error: Specification file not found: {args.spec_file}")
        return 1
    
    try:
        runner = IntegrationOrchestrator()
        print("🔧 Stage 1: Converting OpenSpec to test scaffold...")
        success = runner._stage1_spec_to_scaffold(args.spec_file, args.output)
        
        if success:
            print("✅ Stage 1 completed successfully!")
            return 0
        else:
            print("❌ Stage 1 failed!")
            return 1
            
    except Exception as e:
        print(f"❌ Stage 1 execution failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cmd_stage2(args):
    """Stage 2: Test/Scaffold → Logical Requirements."""
    setup_logging(args.verbose)
    
    try:
        runner = IntegrationOrchestrator()
        print("🧪 Stage 2: Extracting logical requirements from test scaffold...")
        success = runner._stage2_scaffold_to_requirements(args.output)
        
        if success:
            print("✅ Stage 2 completed successfully!")
            return 0
        else:
            print("❌ Stage 2 failed!")
            return 1
            
    except Exception as e:
        print(f"❌ Stage 2 execution failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cmd_stage3(args):
    """Stage 3: Logical Requirements → Behavioral Alignment."""
    setup_logging(args.verbose)
    
    try:
        runner = IntegrationOrchestrator()
        print("🎯 Stage 3: Performing behavioral alignment...")
        success = runner._stage3_requirements_to_alignment(args.output)
        
        if success:
            print("✅ Stage 3 completed successfully!")
            return 0
        else:
            print("❌ Stage 3 failed!")
            return 1
            
    except Exception as e:
        print(f"❌ Stage 3 execution failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cmd_stage4(args):
    """Stage 4: Behavioral Alignment → Final Code."""
    setup_logging(args.verbose)
    
    try:
        runner = IntegrationOrchestrator()
        print("⚡ Stage 4: Generating final code from alignment...")
        success = runner._stage4_alignment_to_code(args.output, dry_run=args.dry_run)
        
        if success:
            print("✅ Stage 4 completed successfully!")
            return 0
        else:
            print("❌ Stage 4 failed!")
            return 1
            
    except Exception as e:
        print(f"❌ Stage 4 execution failed: {e}")
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
    heal_parser.add_argument(
        '--retest',
        action='store_true',
        help='Force re-running tests even if test results already exist'
    )
    
    # Organize command
    org_parser = subparsers.add_parser('organize', help='Restructure code')
    
    # Stage 1 command
    stage1_parser = subparsers.add_parser('stage1', help='Stage 1: OpenSpec → Tests/Scaffold')
    stage1_parser.add_argument(
        'spec_file',
        type=Path,
        help='Path to the OpenSpec YAML file'
    )
    stage1_parser.add_argument(
        '-o', '--output',
        type=Path,
        default=None,
        help='Output directory (default: ./output)'
    )
    
    # Stage 2 command
    stage2_parser = subparsers.add_parser('stage2', help='Stage 2: Test/Scaffold → Logical Requirements')
    stage2_parser.add_argument(
        '-o', '--output',
        type=Path,
        default=None,
        help='Output directory (default: ./output)'
    )
    
    # Stage 3 command
    stage3_parser = subparsers.add_parser('stage3', help='Stage 3: Logical Requirements → Behavioral Alignment')
    stage3_parser.add_argument(
        '-o', '--output',
        type=Path,
        default=None,
        help='Output directory (default: ./output)'
    )
    
    # Stage 4 command
    stage4_parser = subparsers.add_parser('stage4', help='Stage 4: Behavioral Alignment → Final Code')
    stage4_parser.add_argument(
        '-o', '--output',
        type=Path,
        default=None,
        help='Output directory (default: ./output)'
    )
    stage4_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run mode - check setup without calling AI models'
    )
    
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
    try:
        if args.command == 'generate':
            return cmd_generate(args)
        elif args.command == 'test':
            return cmd_test(args)
        elif args.command == 'heal':
            return cmd_heal(args)
        elif args.command == 'organize':
            return cmd_organize(args)
        elif args.command == 'stage1':
            return cmd_stage1(args)
        elif args.command == 'stage2':
            return cmd_stage2(args)
        elif args.command == 'stage3':
            return cmd_stage3(args)
        elif args.command == 'stage4':
            return cmd_stage4(args)
        elif args.command == 'full-run':
            return cmd_full_run(args)
        else:
            print(f"Unknown command: {args.command}")
            return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())