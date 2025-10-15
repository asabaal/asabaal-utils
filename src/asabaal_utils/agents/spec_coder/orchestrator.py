#!/usr/bin/env python3
"""
🧩 Full Integration Orchestration Layer

This script unifies the entire software development pipeline from OpenSpec 
specifications through code generation, testing, and optional healing.

Usage:
    python scripts/run_integration.py --mode fresh
    python scripts/run_integration.py --mode heal
    python scripts/run_integration.py --mode test
"""

import subprocess
import json
import time
import argparse
import os
import sys
from pathlib import Path
from datetime import datetime

class IntegrationOrchestrator:
    """Main integration orchestrator."""
    
    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or Path(__file__).parent.parent
        self.scripts_dir = self.base_dir / "scripts"
        self.healer_dir = self.base_dir / "healer"
        self.prompts_dir = self.base_dir / "prompts"
        self.generated_dir = self.base_dir / "generated_functions"
        self.reports_dir = self.base_dir / "reports"
        
        # Create reports directory with timestamp
        self.timestamp = datetime.now().strftime("%Y%m%d-%H%M")
        self.run_reports_dir = self.reports_dir / self.timestamp
        self.run_reports_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"🧩 Integration Orchestrator - Run: {self.timestamp}")
        print(f"📁 Reports directory: {self.run_reports_dir}")
    
    def run(self, cmd: str, cwd: Path | None = None, capture: bool = True) -> subprocess.CompletedProcess:
        """Run a command and return the result."""
        work_dir = cwd or self.base_dir
        print(f"→ {cmd}")
        print(f"  (in {work_dir})")
        
        try:
            if capture:
                result = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True, 
                    cwd=work_dir, timeout=300
                )
                if result.stdout:
                    print(result.stdout)
                if result.stderr:
                    print(f"STDERR: {result.stderr}")
                return result
            else:
                result = subprocess.run(cmd, shell=True, cwd=work_dir, timeout=300)
                return result
                
        except subprocess.TimeoutExpired:
            print(f"❌ Command timed out: {cmd}")
            return subprocess.CompletedProcess(cmd, 1, "", "Timeout")
        except Exception as e:
            print(f"❌ Command failed: {e}")
            return subprocess.CompletedProcess(cmd, 1, "", str(e))
    
    def validate_specs(self) -> bool:
        """Validate OpenSpec specifications."""
        print("\n📋 Step 1: Validating OpenSpec specifications...")
        
        # Check if openspec is available
        result = self.run("which openspec", capture=True)
        if result.returncode != 0:
            print("⚠️  openspec CLI not found, skipping spec validation")
            return True
        
        # Run spec validation
        result = self.run("openspec validate --all", cwd=self.base_dir.parent.parent)
        
        # Save validation report
        validation_report = {
            "timestamp": datetime.now().isoformat(),
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
        
        with open(self.run_reports_dir / "spec_validation.json", "w") as f:
            json.dump(validation_report, f, indent=2)
        
        return result.returncode == 0
    
    def build_prompts(self) -> bool:
        """Build prompts from validated specs."""
        print("\n📝 Step 2: Building prompts from specifications...")
        
        # Use existing prompt generation
        prompt_script = self.base_dir / "generate_prompts.py"
        if not prompt_script.exists():
            print("❌ Prompt generation script not found")
            return False
        
        result = self.run(f"python {prompt_script}")
        
        # Copy generated prompts to reports
        if self.prompts_dir.exists():
            import shutil
            prompts_report_dir = self.run_reports_dir / "prompts"
            shutil.copytree(self.prompts_dir, prompts_report_dir, dirs_exist_ok=True)
        
        return result.returncode == 0
    
    def generate_functions(self) -> bool:
        """Generate functions from prompts."""
        print("\n🔨 Step 3: Generating functions from prompts...")
        
        # Use existing function generation
        gen_script = self.base_dir / "generate_functions.py"
        if not gen_script.exists():
            print("❌ Function generation script not found")
            return False
        
        result = self.run(f"python {gen_script}")
        
        # Copy generated functions to reports
        if self.generated_dir.exists():
            import shutil
            gen_report_dir = self.run_reports_dir / "generated_functions"
            shutil.copytree(self.generated_dir, gen_report_dir, dirs_exist_ok=True)
        
        return result.returncode == 0
    
    def run_tests(self) -> bool:
        """Run test suite."""
        print("\n🧪 Step 4: Running test suite...")
        
        # Use the existing test runner infrastructure
        test_runner_script = self.base_dir / "run_tests.py"
        if not test_runner_script.exists():
            print("❌ Test runner script not found")
            return False
        
        # Run the test runner which will create test environments and execute tests
        result = self.run(f"python {test_runner_script}")
        
        # Create test results directory in this run's reports
        test_report_dir = self.run_reports_dir / "test_results"
        test_report_dir.mkdir(exist_ok=True)
        
        # Copy test reports if they exist
        if (self.reports_dir / "latest_test_results.json").exists():
            import shutil
            shutil.copy2(
                self.reports_dir / "latest_test_results.json",
                test_report_dir / "test_results.json"
            )
        
        # Also copy the test environment for analysis
        test_env_dir = self.reports_dir / "test_env"
        if test_env_dir.exists():
            import shutil
            test_env_copy = test_report_dir / "test_env"
            if test_env_copy.exists():
                shutil.rmtree(test_env_copy)
            shutil.copytree(test_env_dir, test_env_copy)
        
        return result.returncode == 0
    
    def run_healing(self) -> bool:
        """Run self-healing layer."""
        print("\n🔧 Step 5: Running self-healing layer...")
        
        # Classify failures
        classify_script = self.healer_dir / "classify_failures.py"
        result = self.run(f"python {classify_script}")
        if result.returncode != 0:
            print("⚠️  Classification failed, continuing...")
        
        # Plan patches
        plan_script = self.healer_dir / "plan_patches.py"
        result = self.run(f"python {plan_script}")
        if result.returncode != 0:
            print("⚠️  Patch planning failed, continuing...")
        
        # Run healing (with timeout to prevent hanging)
        heal_script = self.healer_dir / "heal.py"
        result = self.run(f"timeout 300 python {heal_script} --model llama3.1:latest")
        if result.returncode != 0:
            print("⚠️  Healing failed or timed out, continuing...")
        
        # Re-run tests after healing
        print("🔄 Re-running tests after healing...")
        self.run_tests()
        
        # Copy healing artifacts
        if (self.healer_dir / "artifacts").exists():
            import shutil
            healing_report_dir = self.run_reports_dir / "healing"
            shutil.copytree(
                self.healer_dir / "artifacts", 
                healing_report_dir, 
                dirs_exist_ok=True
            )
        
        return True  # Healing failures shouldn't stop the pipeline
    
    def aggregate_reports(self) -> bool:
        """Aggregate all reports into summary."""
        print("\n📊 Step 6: Aggregating reports...")
        
        summary = {
            "run_timestamp": self.timestamp,
            "completed_at": datetime.now().isoformat(),
            "stages": {},
            "overall_success": True
        }
        
        # Collect reports from each stage
        stages = [
            ("spec_validation", "spec_validation.json"),
            ("test_results", "test_results/test_results.json"),
            ("healing", "healing/latest_healing_results.yaml")
        ]
        
        for stage_name, report_file in stages:
            report_path = self.run_reports_dir / report_file
            if report_path.exists():
                try:
                    if report_file.endswith('.json'):
                        with open(report_path) as f:
                            summary["stages"][stage_name] = json.load(f)
                    else:
                        # For YAML files, just note existence
                        summary["stages"][stage_name] = {"file_exists": True}
                except Exception as e:
                    summary["stages"][stage_name] = {"error": str(e)}
                    summary["overall_success"] = False
            else:
                summary["stages"][stage_name] = {"file_exists": False}
        
        # Save summary
        summary_path = self.run_reports_dir / "integration_summary.json"
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)
        
        # Also save as latest
        latest_path = self.reports_dir / "latest_integration_summary.json"
        with open(latest_path, "w") as f:
            json.dump(summary, f, indent=2)
        
        print(f"📄 Integration summary saved: {summary_path}")
        return summary["overall_success"]
    
    def run_mode(self, mode: str) -> bool:
        """Run the integration pipeline in the specified mode."""
        print(f"\n🚀 Starting integration pipeline in '{mode}' mode")
        print("=" * 60)
        
        success = True
        
        if mode in ["fresh", "update", "validate"]:
            if not self.validate_specs():
                print("❌ Spec validation failed")
                if mode == "validate":
                    return False
                success = False
        
        if mode in ["fresh", "update"]:
            if not self.build_prompts():
                print("❌ Prompt building failed")
                success = False
            
            if not self.generate_functions():
                print("❌ Function generation failed")
                success = False
        
        if mode in ["fresh", "update", "test"]:
            if not self.run_tests():
                print("❌ Tests failed")
                success = False
        
        if mode == "heal":
            if not self.run_healing():
                print("❌ Healing failed")
                success = False
        
        # Always aggregate reports
        self.aggregate_reports()
        
        print(f"\n✅ Integration pipeline complete ({mode})")
        print(f"📁 Reports available at: {self.run_reports_dir}")
        
        if success:
            print("🎉 All stages completed successfully!")
        else:
            print("⚠️  Some stages had issues - check reports for details")
        
        return success


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Full Integration Orchestration Layer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  fresh    - Start from specs, regenerate everything
  update   - Start from specs, update only changed components  
  heal     - Start from failed tests, run self-healing
  validate - Validate specs only, no code generation
  test     - Skip generation, re-run tests and reporting
        """
    )
    
    parser.add_argument(
        "--mode", 
        choices=["fresh", "update", "heal", "validate", "test"],
        default="fresh",
        help="Integration pipeline mode"
    )
    
    parser.add_argument(
        "--base-dir",
        type=Path,
        help="Base directory for the project"
    )
    
    args = parser.parse_args()
    
    orchestrator = IntegrationOrchestrator(args.base_dir)
    
    try:
        success = orchestrator.run_mode(args.mode)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Integration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Integration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()