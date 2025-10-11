"""
Examples of using the Progress Monitor system
"""

import time
import random
from asabaal_utils.monitoring import ProgressMonitor, MonitorLevel


def example_basic():
    """Basic usage example"""
    print("=== Basic Usage Example ===")
    
    # Simple progress tracking
    monitor = ProgressMonitor(100, "Processing items")
    monitor.start()
    
    for i in range(100):
        # Simulate work
        time.sleep(0.01)
        monitor.update(i)
    
    monitor.finish()


def example_context_manager():
    """Context manager example"""
    print("\n=== Context Manager Example ===")
    
    with ProgressMonitor(50, "Processing with context", level=MonitorLevel.DETAILED) as monitor:
        for i in range(50):
            time.sleep(0.02)
            # Add custom stats
            monitor.update(i, batch=i//10, status="active")


def example_decorator():
    """Decorator pattern example"""
    print("\n=== Decorator Example ===")
    
    @ProgressMonitor.track(title="Processing files", level=MonitorLevel.DETAILED)
    def process_files(files):
        for i, file in enumerate(files):
            # Update progress within decorated function
            ProgressMonitor.update_current(i, len(files))
            time.sleep(0.05)
            # Process file...
    
    # Call decorated function
    test_files = [f"file_{i}.txt" for i in range(20)]
    process_files(test_files)


def example_video_monitor():
    """Specialized video monitor example"""
    print("\n=== Video Monitor Example ===")
    
    from asabaal_utils.monitoring.progress_monitor import VideoProgressMonitor
    
    # Video rendering at 30 fps
    total_frames = 150
    fps = 30
    
    monitor = VideoProgressMonitor(total_frames, fps=fps)
    monitor.start()
    
    for frame in range(total_frames):
        # Simulate variable rendering speed
        render_time = random.uniform(0.02, 0.04)
        time.sleep(render_time)
        monitor.update(frame)
    
    monitor.finish("Video rendered successfully!")


def example_levels():
    """Different monitoring levels example"""
    print("\n=== Monitoring Levels Example ===")
    
    levels = [
        (MonitorLevel.NONE, "No output"),
        (MonitorLevel.BASIC, "Basic percentage only"),
        (MonitorLevel.DETAILED, "Full progress bar"),
        (MonitorLevel.DEBUG, "Debug information")
    ]
    
    for level, description in levels:
        print(f"\n--- Level: {description} ---")
        
        with ProgressMonitor(30, f"Testing {level.name}", level=level) as monitor:
            for i in range(30):
                time.sleep(0.03)
                monitor.update(i)


def example_custom_stats():
    """Custom statistics tracking example"""
    print("\n=== Custom Stats Example ===")
    
    monitor = ProgressMonitor(
        100, 
        "Processing with custom stats",
        level=MonitorLevel.DETAILED
    )
    monitor.start()
    
    errors = 0
    processed = 0
    
    for i in range(100):
        time.sleep(0.01)
        
        # Simulate occasional errors
        if random.random() < 0.1:
            errors += 1
        else:
            processed += 1
        
        # Update with custom stats
        monitor.update(
            i,
            processed=processed,
            errors=errors,
            success_rate=f"{(processed/(i+1))*100:.1f}%"
        )
    
    monitor.finish(f"Completed with {errors} errors")


def example_file_monitor():
    """File processing monitor example"""
    print("\n=== File Monitor Example ===")
    
    from asabaal_utils.monitoring.progress_monitor import FileProgressMonitor
    
    # Simulate file list
    files = [f"/path/to/file_{i:03d}.txt" for i in range(25)]
    
    monitor = FileProgressMonitor(files)
    monitor.start()
    
    for i, file_path in enumerate(files):
        # Simulate file processing
        time.sleep(random.uniform(0.05, 0.1))
        monitor.update_file(i, file_path)
    
    monitor.finish()


if __name__ == "__main__":
    print("Progress Monitor Examples")
    print("========================\n")
    
    # Run all examples
    example_basic()
    example_context_manager()
    example_decorator()
    example_video_monitor()
    example_levels()
    example_custom_stats()
    example_file_monitor()
    
    print("\n✅ All examples completed!")