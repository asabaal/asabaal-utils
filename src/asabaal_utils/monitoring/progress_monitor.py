"""
Reusable Progress Monitoring System

Features:
- Multiple monitoring levels (NONE, BASIC, DETAILED, DEBUG)
- Easy decorator pattern for adding to any function
- Customizable display formats
- Performance metrics tracking
- Can be easily swapped out for different implementations
"""

import time
import sys
from enum import IntEnum
from typing import Optional, Dict, Any, Callable
from datetime import timedelta
import threading
from dataclasses import dataclass


class MonitorLevel(IntEnum):
    """Monitoring detail levels"""
    NONE = 0      # No output
    BASIC = 1     # Simple percentage
    DETAILED = 2  # Progress bar + stats
    DEBUG = 3     # Everything including internal metrics


@dataclass
class ProgressMetrics:
    """Container for progress metrics"""
    current: int = 0
    total: int = 0
    start_time: Optional[float] = None
    last_update_time: Optional[float] = None
    custom_stats: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_stats is None:
            self.custom_stats = {}


class ProgressMonitor:
    """
    Flexible progress monitoring system
    
    Usage:
        # Basic usage
        monitor = ProgressMonitor(total_items=100, title="Processing")
        monitor.start()
        for i in range(100):
            # Do work
            monitor.update(i)
        monitor.finish()
        
        # With context manager
        with ProgressMonitor(100, "Processing") as monitor:
            for i in range(100):
                # Do work
                monitor.update(i)
                
        # As a decorator
        @ProgressMonitor.track(title="Processing files")
        def process_files(files):
            for i, file in enumerate(files):
                ProgressMonitor.update_current(i, len(files))
                # Process file
    """
    
    # Class variable for decorator pattern
    _current_monitor: Optional['ProgressMonitor'] = None
    
    def __init__(self, 
                 total_items: int,
                 title: str = "Progress",
                 level: MonitorLevel = MonitorLevel.DETAILED,
                 update_interval: float = 0.5,
                 show_eta: bool = True,
                 show_speed: bool = True,
                 custom_format: Optional[str] = None,
                 bar_width: int = 50,
                 units: str = "items",
                 units_per_second: Optional[str] = None):
        """
        Initialize progress monitor
        
        Args:
            total_items: Total number of items to process
            title: Title to display
            level: Monitoring detail level
            update_interval: Minimum seconds between display updates
            show_eta: Show estimated time remaining
            show_speed: Show processing speed
            custom_format: Custom format string for display
            bar_width: Width of progress bar (for DETAILED level)
            units: Name of items being processed (e.g., "frames", "files")
            units_per_second: Custom unit for speed (e.g., "fps", "MB/s")
        """
        self.metrics = ProgressMetrics(total=total_items)
        self.title = title
        self.level = level
        self.update_interval = update_interval
        self.show_eta = show_eta
        self.show_speed = show_speed
        self.custom_format = custom_format
        self.bar_width = bar_width
        self.units = units
        self.units_per_second = units_per_second or f"{units}/s"
        
        self._lock = threading.Lock()
        self._finished = False
        
    def start(self):
        """Start monitoring"""
        with self._lock:
            self.metrics.start_time = time.time()
            self.metrics.last_update_time = 0
            self._finished = False
            
            if self.level == MonitorLevel.NONE:
                return
                
            # Initial display
            if self.level >= MonitorLevel.BASIC:
                print(f"\n{self.title}:")
                
            # Set as current monitor for decorator pattern
            ProgressMonitor._current_monitor = self
    
    def update(self, current: int, force_display: bool = False, **custom_stats):
        """
        Update progress
        
        Args:
            current: Current item number (0-based)
            force_display: Force display update regardless of interval
            **custom_stats: Additional statistics to track
        """
        with self._lock:
            if self._finished or self.level == MonitorLevel.NONE:
                return
                
            self.metrics.current = current
            self.metrics.custom_stats.update(custom_stats)
            
            # Check if we should update display
            current_time = time.time()
            if not force_display and current_time - self.metrics.last_update_time < self.update_interval:
                return
                
            self.metrics.last_update_time = current_time
            self._display_progress()
    
    def _display_progress(self):
        """Display progress based on level"""
        if self.level == MonitorLevel.BASIC:
            self._display_basic()
        elif self.level == MonitorLevel.DETAILED:
            self._display_detailed()
        elif self.level == MonitorLevel.DEBUG:
            self._display_debug()
    
    def _display_basic(self):
        """Simple percentage display"""
        if self.metrics.total > 0:
            percentage = (self.metrics.current / self.metrics.total) * 100
            print(f"\r{self.title}: {percentage:.1f}%", end='', flush=True)
    
    def _display_detailed(self):
        """Detailed progress bar with stats"""
        if self.metrics.total <= 0:
            return
            
        # Calculate progress
        progress = self.metrics.current / self.metrics.total
        percentage = progress * 100
        
        # Calculate elapsed time
        elapsed = time.time() - self.metrics.start_time
        
        # Build progress bar
        filled = int(self.bar_width * progress)
        bar = '█' * filled + '░' * (self.bar_width - filled)
        
        # Build display string
        display_parts = [f"\r{self.title}: [{bar}] {percentage:.1f}%"]
        
        # Add current/total
        display_parts.append(f"{self.metrics.current}/{self.metrics.total} {self.units}")
        
        # Add speed if requested
        if self.show_speed and elapsed > 0:
            speed = self.metrics.current / elapsed
            display_parts.append(f"{speed:.1f} {self.units_per_second}")
        
        # Add ETA if requested
        if self.show_eta and self.metrics.current > 0:
            eta = (elapsed / self.metrics.current) * (self.metrics.total - self.metrics.current)
            eta_str = str(timedelta(seconds=int(eta)))
            display_parts.append(f"ETA: {eta_str}")
        
        # Add elapsed time
        elapsed_str = str(timedelta(seconds=int(elapsed)))
        display_parts.append(f"Elapsed: {elapsed_str}")
        
        # Custom stats
        for key, value in self.metrics.custom_stats.items():
            display_parts.append(f"{key}: {value}")
        
        # Display
        display = " | ".join(display_parts)
        
        # Ensure we clear the line properly
        terminal_width = 120  # Safe default
        try:
            import os
            terminal_width = os.get_terminal_size().columns
        except:
            pass
            
        print(f"{display:<{terminal_width}}", end='', flush=True)
    
    def _display_debug(self):
        """Debug level - shows everything"""
        self._display_detailed()
        
        # Additional debug info on new lines
        if self.metrics.current % 10 == 0:  # Every 10 items
            print(f"\n[DEBUG] Memory usage: {self._get_memory_usage():.1f} MB", end='')
            print(f" | Thread: {threading.current_thread().name}", end='')
            print(f" | Lock acquisitions: {self._lock._count if hasattr(self._lock, '_count') else 'N/A'}")
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except:
            return 0.0
    
    def finish(self, message: Optional[str] = None):
        """Finish monitoring and display final stats"""
        with self._lock:
            if self._finished:
                return
                
            self._finished = True
            self.metrics.current = self.metrics.total
            
            if self.level == MonitorLevel.NONE:
                return
            
            # Force final display
            self._display_progress()
            print()  # New line
            
            # Summary
            if self.level >= MonitorLevel.DETAILED and self.metrics.start_time:
                elapsed = time.time() - self.metrics.start_time
                elapsed_str = str(timedelta(seconds=int(elapsed)))
                
                if self.metrics.total > 0:
                    avg_speed = self.metrics.total / elapsed
                    print(f"✅ Completed {self.metrics.total} {self.units} in {elapsed_str}")
                    print(f"   Average speed: {avg_speed:.1f} {self.units_per_second}")
                
                if message:
                    print(f"   {message}")
            
            # Clear current monitor
            if ProgressMonitor._current_monitor == self:
                ProgressMonitor._current_monitor = None
    
    def add_custom_stat(self, key: str, value: Any):
        """Add or update a custom statistic"""
        with self._lock:
            self.metrics.custom_stats[key] = value
    
    # Context manager support
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.finish()
        return False
    
    # Decorator pattern
    @classmethod
    def track(cls, 
              title: str = "Progress",
              level: MonitorLevel = MonitorLevel.DETAILED,
              **kwargs) -> Callable:
        """
        Decorator for tracking function progress
        
        Usage:
            @ProgressMonitor.track(title="Processing files")
            def process_files(files):
                for i, file in enumerate(files):
                    ProgressMonitor.update_current(i, len(files))
                    # Process file
        """
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **func_kwargs):
                # Try to determine total from first argument
                total = None
                if args and hasattr(args[0], '__len__'):
                    total = len(args[0])
                
                # Allow function to override
                total = func_kwargs.pop('_monitor_total', total) or 100
                
                with cls(total, title=title, level=level, **kwargs) as monitor:
                    return func(*args, **func_kwargs)
            
            return wrapper
        return decorator
    
    @classmethod
    def update_current(cls, current: int, total: Optional[int] = None, **stats):
        """Update the current monitor (for use within decorated functions)"""
        if cls._current_monitor:
            if total is not None:
                cls._current_monitor.metrics.total = total
            cls._current_monitor.update(current, **stats)
    
    @classmethod
    def get_current(cls) -> Optional['ProgressMonitor']:
        """Get the current active monitor"""
        return cls._current_monitor


# Convenience functions
def create_monitor(total: int, 
                  title: str = "Progress",
                  level: str = "detailed") -> ProgressMonitor:
    """
    Create a progress monitor with string-based level
    
    Args:
        total: Total items to process
        title: Display title
        level: Level as string ("none", "basic", "detailed", "debug")
    """
    level_map = {
        "none": MonitorLevel.NONE,
        "basic": MonitorLevel.BASIC,
        "detailed": MonitorLevel.DETAILED,
        "debug": MonitorLevel.DEBUG
    }
    
    monitor_level = level_map.get(level.lower(), MonitorLevel.DETAILED)
    return ProgressMonitor(total, title=title, level=monitor_level)


# Example specialized monitors
class VideoProgressMonitor(ProgressMonitor):
    """Specialized monitor for video processing"""
    
    def __init__(self, total_frames: int, fps: float = 30.0, **kwargs):
        super().__init__(
            total_frames,
            title=kwargs.pop('title', 'Rendering video'),
            units='frames',
            units_per_second='fps',
            **kwargs
        )
        self.target_fps = fps
        
    def update(self, frame_num: int, **stats):
        """Update with video-specific stats"""
        # Calculate actual vs target FPS
        if self.metrics.start_time:
            elapsed = time.time() - self.metrics.start_time
            if elapsed > 0:
                actual_fps = frame_num / elapsed
                speed_ratio = actual_fps / self.target_fps
                stats['speed'] = f"{speed_ratio:.1f}x"
        
        super().update(frame_num, **stats)


class FileProgressMonitor(ProgressMonitor):
    """Specialized monitor for file processing"""
    
    def __init__(self, files: list, **kwargs):
        super().__init__(
            len(files),
            title=kwargs.pop('title', 'Processing files'),
            units='files',
            **kwargs
        )
        self.files = files
        
    def update_file(self, index: int, file_path: str):
        """Update with current file info"""
        import os
        filename = os.path.basename(file_path)
        self.update(index, filename=filename)