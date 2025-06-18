# Progress Monitoring System

A flexible, reusable progress monitoring system for Asabaal Utils that can be easily added to any tool or process.

## Features

- **Multiple Monitoring Levels**: Choose from NONE, BASIC, DETAILED, or DEBUG
- **Easy Integration**: Use as context manager, decorator, or standalone
- **Customizable**: Add custom statistics, change display format
- **Thread-Safe**: Safe to use in multi-threaded applications
- **Specialized Monitors**: Pre-built monitors for video and file processing
- **Performance Metrics**: Automatic calculation of speed, ETA, and elapsed time

## Quick Start

### Basic Usage

```python
from asabaal_utils.monitoring import ProgressMonitor

# Simple progress tracking
monitor = ProgressMonitor(100, "Processing items")
monitor.start()

for i in range(100):
    # Do work
    monitor.update(i)
    
monitor.finish()
```

### Context Manager

```python
with ProgressMonitor(100, "Processing") as monitor:
    for i in range(100):
        # Do work
        monitor.update(i)
```

### Decorator Pattern

```python
@ProgressMonitor.track(title="Processing files")
def process_files(files):
    for i, file in enumerate(files):
        ProgressMonitor.update_current(i, len(files))
        # Process file
```

## Monitoring Levels

### MonitorLevel.NONE
No output - completely silent

### MonitorLevel.BASIC
Simple percentage display:
```
Processing: 45.2%
```

### MonitorLevel.DETAILED (default)
Full progress bar with statistics:
```
🎬 Rendering: [████████████░░░░░░░░] 45.2% | 452/1000 frames | 30.1 fps | ETA: 00:18 | Elapsed: 00:15
```

### MonitorLevel.DEBUG
Everything plus debug information (memory usage, thread info)

## Specialized Monitors

### VideoProgressMonitor

Optimized for video processing with FPS tracking:

```python
from asabaal_utils.monitoring.progress_monitor import VideoProgressMonitor

monitor = VideoProgressMonitor(total_frames=1500, fps=30)
monitor.start()

for frame_num in range(1500):
    # Render frame
    monitor.update(frame_num)
    
monitor.finish()
```

### FileProgressMonitor

Optimized for file processing with filename display:

```python
from asabaal_utils.monitoring.progress_monitor import FileProgressMonitor

files = ["file1.txt", "file2.txt", "file3.txt"]
monitor = FileProgressMonitor(files)
monitor.start()

for i, file in enumerate(files):
    # Process file
    monitor.update_file(i, file)
    
monitor.finish()
```

## Custom Statistics

Add any custom statistics to track:

```python
monitor = ProgressMonitor(100, "Processing")
monitor.start()

errors = 0
for i in range(100):
    try:
        # Do work
        pass
    except:
        errors += 1
    
    monitor.update(i, errors=errors, success_rate=f"{((i-errors)/i)*100:.1f}%")
    
monitor.finish()
```

## Integration Example

### Adding to Existing Tool

```python
def my_existing_function(items):
    # Original code
    for item in items:
        process_item(item)

# With monitoring
def my_existing_function(items):
    with ProgressMonitor(len(items), "Processing items") as monitor:
        for i, item in enumerate(items):
            process_item(item)
            monitor.update(i)
```

### Environment Variables

Control monitoring level via environment:

```bash
# Set globally
export MONITOR_LEVEL=basic

# Or per-command
MONITOR_LEVEL=debug python my_script.py
```

## Advanced Usage

### Custom Display Format

```python
monitor = ProgressMonitor(
    100,
    "Custom format",
    custom_format="{title}: {current}/{total} ({percentage:.0f}%)"
)
```

### Different Update Intervals

```python
# Update display every 2 seconds instead of default 0.5
monitor = ProgressMonitor(100, "Slow updates", update_interval=2.0)
```

### Force Display Update

```python
# Force immediate display update
monitor.update(50, force_display=True)
```

## Thread Safety

The monitor is thread-safe and can be used in multi-threaded applications:

```python
import threading

monitor = ProgressMonitor(100, "Multi-threaded")
monitor.start()

def worker(start, end):
    for i in range(start, end):
        # Do work
        monitor.update(i)

threads = []
for i in range(0, 100, 25):
    t = threading.Thread(target=worker, args=(i, i+25))
    threads.append(t)
    t.start()

for t in threads:
    t.join()
    
monitor.finish()
```

## Best Practices

1. **Choose appropriate level**: Use DETAILED for user-facing operations, BASIC for logs
2. **Update reasonably**: Don't update every iteration if you have millions of items
3. **Add meaningful stats**: Include information that helps users understand progress
4. **Use specialized monitors**: Use VideoProgressMonitor for video, FileProgressMonitor for files
5. **Clean up properly**: Always call finish() or use context manager

## Examples

See `examples.py` for comprehensive examples of all features.