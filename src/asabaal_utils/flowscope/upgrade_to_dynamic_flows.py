#!/usr/bin/env python3
"""
Upgrade FlowScope Function Flows to Dynamic Visualizations

This script replaces static function flow HTML files with dynamic,
interactive versions using the new dynamic function flow generator.
"""

import json
from pathlib import Path
from typing import Dict, Any, List
import shutil

try:
    from asabaal_utils.flowscope.dynamic_function_flow_generator import generate_dynamic_function_flow
except ImportError:
    try:
        from dynamic_function_flow_generator import generate_dynamic_function_flow
    except ImportError:
        print("❌ Cannot import dynamic function flow generator")
        print("   Make sure the file is in the same directory or installed")
        exit(1)


def upgrade_function_flows_dir(function_flows_dir: Path, backup: bool = True) -> None:
    """
    Upgrade all function flows in a directory to dynamic visualizations.
    
    Args:
        function_flows_dir: Directory containing function_flows/ with JSON files
        backup: Whether to create backup of original files
    """
    
    function_flows_dir = Path(function_flows_dir)
    flows_json_dir = function_flows_dir / "function_flows"
    
    if not flows_json_dir.exists():
        print(f"❌ Function flows directory not found: {flows_json_dir}")
        return
    
    print(f"🔧 Upgrading function flows in: {function_flows_dir}")
    
    # Create backup if requested
    if backup:
        backup_dir = function_flows_dir / "function_flows_backup"
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        shutil.copytree(flows_json_dir, backup_dir)
        print(f"✓ Created backup: {backup_dir}")
    
    # Process each JSON file
    json_files = list(flows_json_dir.glob("*.json"))
    if not json_files:
        print("❌ No JSON files found in function_flows directory")
        return
    
    print(f"📁 Found {len(json_files)} JSON files to process")
    
    total_functions = 0
    successful_upgrades = 0
    
    for json_file in json_files:
        print(f"\n📄 Processing: {json_file.name}")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            module_name = data.get('module', json_file.stem)
            function_flows = data.get('function_flows', {})
            
            if not function_flows:
                print(f"   ⚠️  No function flows found in {json_file.name}")
                continue
            
            print(f"   📊 Found {len(function_flows)} functions in {module_name}")
            
            for func_name, flow_data in function_flows.items():
                total_functions += 1
                
                try:
                    # Generate dynamic HTML
                    output_file = flows_json_dir / f"{func_name}_flow.html"
                    
                    generate_dynamic_function_flow(
                        flow_data,
                        output_file,
                        function_name=func_name,
                        module_name=module_name
                    )
                    
                    successful_upgrades += 1
                    print(f"   ✓ Generated: {func_name}_flow.html")
                    
                except Exception as e:
                    print(f"   ❌ Failed to generate {func_name}: {e}")
        
        except Exception as e:
            print(f"   ❌ Failed to process {json_file.name}: {e}")
    
    print(f"\n🎉 Upgrade complete!")
    print(f"   Total functions: {total_functions}")
    print(f"   Successfully upgraded: {successful_upgrades}")
    print(f"   Success rate: {(successful_upgrades/total_functions*100):.1f}%")


def upgrade_single_function(json_file: Path, function_name: str, output_dir: Path) -> None:
    """
    Upgrade a single function from a JSON file to dynamic visualization.
    
    Args:
        json_file: Path to JSON file containing function flow data
        function_name: Name of function to upgrade
        output_dir: Directory to save the dynamic HTML
    """
    
    print(f"🔧 Upgrading single function: {function_name}")
    print(f"   From: {json_file}")
    print(f"   To: {output_dir}")
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        module_name = data.get('module', json_file.stem)
        function_flows = data.get('function_flows', {})
        
        if function_name not in function_flows:
            print(f"❌ Function '{function_name}' not found in {json_file}")
            return
        
        flow_data = function_flows[function_name]
        output_file = output_dir / f"{function_name}_dynamic.html"
        
        generate_dynamic_function_flow(
            flow_data,
            output_file,
            function_name=function_name,
            module_name=module_name
        )
        
        print(f"✓ Generated dynamic visualization: {output_file}")
        
    except Exception as e:
        print(f"❌ Failed to upgrade {function_name}: {e}")


def list_available_functions(function_flows_dir: Path) -> None:
    """
    List all available functions in function flows directory.
    
    Args:
        function_flows_dir: Directory containing function_flows/ with JSON files
    """
    
    flows_json_dir = function_flows_dir / "function_flows"
    
    if not flows_json_dir.exists():
        print(f"❌ Function flows directory not found: {flows_json_dir}")
        return
    
    print(f"📋 Available functions in: {function_flows_dir}")
    print()
    
    for json_file in sorted(flows_json_dir.glob("*.json")):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            module_name = data.get('module', json_file.stem)
            function_flows = data.get('function_flows', {})
            
            if function_flows:
                print(f"📄 {module_name} ({json_file.name}):")
                for func_name in sorted(function_flows.keys()):
                    print(f"   • {func_name}")
                print()
        
        except Exception as e:
            print(f"❌ Error reading {json_file.name}: {e}")


def main():
    """Main CLI interface."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python upgrade_to_dynamic_flows.py <command> [args]")
        print()
        print("Commands:")
        print("  upgrade <flowscope_dir>     Upgrade all function flows in directory")
        print("  single <json_file> <func> <output_dir>  Upgrade single function")
        print("  list <flowscope_dir>       List available functions")
        print()
        print("Examples:")
        print("  python upgrade_to_dynamic_flows.py upgrade ./flowscope_analysis")
        print("  python upgrade_to_dynamic_flows.py single parser.json build_plan ./output")
        print("  python upgrade_to_dynamic_flows.py list ./flowscope_analysis")
        return
    
    command = sys.argv[1]
    
    if command == "upgrade":
        if len(sys.argv) < 3:
            print("❌ Please specify FlowScope analysis directory")
            return
        upgrade_function_flows_dir(Path(sys.argv[2]))
    
    elif command == "single":
        if len(sys.argv) < 5:
            print("❌ Please specify: <json_file> <function_name> <output_dir>")
            return
        upgrade_single_function(
            Path(sys.argv[2]),
            sys.argv[3],
            Path(sys.argv[4])
        )
    
    elif command == "list":
        if len(sys.argv) < 3:
            print("❌ Please specify FlowScope analysis directory")
            return
        list_available_functions(Path(sys.argv[2]))
    
    else:
        print(f"❌ Unknown command: {command}")


if __name__ == "__main__":
    main()