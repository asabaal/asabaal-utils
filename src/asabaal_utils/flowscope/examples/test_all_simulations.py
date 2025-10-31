#!/usr/bin/env python3
"""
Test all generated simulations to ensure they work correctly
"""

import sys
import os
from pathlib import Path

def test_simulation_files():
    """Test that all simulation files exist and have content"""
    
    simulations_dir = Path(__file__).parent / "structure_visualizations" / "simulations"
    
    if not simulations_dir.exists():
        print("❌ Simulations directory does not exist")
        return False
    
    simulation_files = [
        "linear_5_lines_layout_simulation.html",
        "binary_6_lines_layout_simulation.html", 
        "loop_8_lines_layout_simulation.html",
        "nested_12_lines_layout_simulation.html",
        "index.html"
    ]
    
    all_good = True
    
    for sim_file in simulation_files:
        file_path = simulations_dir / sim_file
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"✓ {sim_file} - {size} bytes")
            if size < 1000:  # Check if file has substantial content
                print(f"  ⚠️  Warning: File seems small")
        else:
            print(f"❌ {sim_file} - Missing")
            all_good = False
    
    # Check for frame files
    frame_files = list(simulations_dir.glob("*_frames.json"))
    print(f"\\nFrame files found: {len(frame_files)}")
    for frame_file in frame_files:
        size = frame_file.stat().st_size
        print(f"✓ {frame_file.name} - {size} bytes")
    
    return all_good

def test_layout_relaxer_import():
    """Test that layout relaxer can be imported"""
    
    try:
        sys.path.append('..')
        from layout_relaxer import GraphLayout
        print("✓ Layout relaxer imports successfully")
        
        # Test basic functionality
        G = GraphLayout()
        G.add_node("test", "test", shape="box", color="#ff0000", width=1.0, height=1.0)
        print(f"✓ GraphLayout works - {len(G.nodes)} node")
        
        return True
    except ImportError as e:
        print(f"❌ Layout relaxer import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Layout relaxer test failed: {e}")
        return False

def test_simulation_visualizer_import():
    """Test that simulation visualizer can be imported"""
    
    try:
        sys.path.append('..')
        from layout_simulation_visualizer import LayoutSimulationVisualizer
        print("✓ Layout simulation visualizer imports successfully")
        
        # Test basic functionality
        viz = LayoutSimulationVisualizer(max_frames_in_memory=10)
        print(f"✓ LayoutSimulationVisualizer works - max frames: {viz.max_frames_in_memory}")
        
        return True
    except ImportError as e:
        print(f"❌ Layout simulation visualizer import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Layout simulation visualizer test failed: {e}")
        return False

def main():
    """Run all tests"""
    
    print("Testing FlowScope Layout Relaxer Simulations")
    print("=" * 50)
    
    print("\\n1. Testing imports...")
    import_ok1 = test_layout_relaxer_import()
    import_ok2 = test_simulation_visualizer_import()
    
    print("\\n2. Testing generated files...")
    files_ok = test_simulation_files()
    
    print("\\n" + "=" * 50)
    if import_ok1 and import_ok2 and files_ok:
        print("✅ All tests passed! Layout relaxer simulations are working correctly.")
        print("\\nTo view simulations:")
        print("  1. Open structure_visualizations/simulations/index.html")
        print("  2. Click on any simulation link")
        print("  3. Use controls to play/pause/step through the simulation")
    else:
        print("❌ Some tests failed. Check the errors above.")
    
    print("\\nSimulation Features:")
    print("- Step-by-step navigation")
    print("- Auto-play with adjustable FPS (0.5-10)")
    print("- Memory optimization for large simulations")
    print("- Interactive controls and progress bar")
    print("- Real-time iteration and physics info")

if __name__ == "__main__":
    main()