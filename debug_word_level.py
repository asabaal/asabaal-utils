#!/usr/bin/env python3
"""
Debug word-level rendering to understand why some words appear faint/invisible.
This focuses on the word-by-word animation and opacity calculations.
"""

import numpy as np
import cv2
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Set dark theme for matplotlib
plt.style.use('dark_background')

# Import our components
from src.asabaal_utils.video_processing.lyric_video.text.renderer import TextRenderer, TextStyle, AnimationConfig
from src.asabaal_utils.video_processing.lyric_video.lyrics.parser import LyricWord

class WordLevelDebugger:
    """Debug individual word rendering and animation timing."""
    
    def __init__(self, resolution=(1920, 1080)):
        self.resolution = resolution
        self.renderer = TextRenderer(resolution)
        self.debug_output_dir = Path("word_level_debug")
        self.debug_output_dir.mkdir(exist_ok=True)
        
    def debug_word_timing_issue(self):
        """Debug the specific word timing issue the user reported."""
        print("🔍 DEBUGGING WORD-LEVEL RENDERING TIMING")
        print("=" * 60)
        
        # Use the problematic text case
        text = "Can't you see you belong to me"
        font_size = 120
        
        print(f"Testing: '{text}' at {font_size}px")
        
        # Create style and animation config
        style = TextStyle(font_size=font_size, vertical_position="center")
        animation_config = self.renderer.animation_presets['subtle']
        
        print(f"Animation config: entrance={animation_config.entrance_type}, word_delay={animation_config.word_delay}")
        
        # Create words with timing
        words = []
        word_list = text.split()
        current_time = 0.0
        
        for i, word_text in enumerate(word_list):
            word_duration = 0.6  # 600ms per word
            start_time = current_time
            end_time = current_time + word_duration
            
            word = LyricWord(word_text, start_time, end_time)
            words.append(word)
            current_time = end_time
            
        line_start = 0.0
        line_end = current_time
        
        print(f"Created {len(words)} words:")
        for i, word in enumerate(words):
            print(f"  {i}: '{word.text}' - {word.start_time:.1f}s to {word.end_time:.1f}s (duration: {word.duration:.1f}s)")
        print(f"Line timing: {line_start:.1f}s to {line_end:.1f}s")
        
        # Test at different time points to see animation progression
        test_times = [
            line_end * 0.2,   # Early in line
            line_end * 0.4,   # Early-mid
            line_end * 0.6,   # Mid-late
            line_end * 0.8,   # Late
            line_end * 1.0,   # End
        ]
        
        results = []
        
        for i, test_time in enumerate(test_times):
            print(f"\n--- TESTING AT TIME {test_time:.1f}s ({test_time/line_end*100:.0f}% through line) ---")
            
            # Calculate which words should be visible at this time
            word_states = []
            for j, word in enumerate(words):
                if test_time < word.start_time:
                    word_progress = 0.0
                    state = "not started"
                elif test_time > word.end_time:
                    word_progress = 1.0
                    state = "complete"
                else:
                    if word.duration > 0:
                        word_progress = (test_time - word.start_time) / word.duration
                    else:
                        word_progress = 1.0
                    state = f"active ({word_progress*100:.0f}%)"
                    
                # Apply word delay for staggered animations
                if animation_config.word_delay > 0:
                    line_progress = (test_time - line_start) / (line_end - line_start)
                    delay_offset = j * animation_config.word_delay
                    adjusted_progress = max(0, min(1, line_progress - delay_offset))
                    adjusted_state = f"delayed ({adjusted_progress*100:.0f}%)"
                else:
                    adjusted_progress = word_progress
                    adjusted_state = state
                    
                word_states.append({
                    "word": word.text,
                    "raw_progress": word_progress,
                    "adjusted_progress": adjusted_progress,
                    "state": state,
                    "adjusted_state": adjusted_state
                })
                
                print(f"  Word {j} '{word.text}': {state} → {adjusted_state}")
                
            # Render at this time point
            try:
                rendered_frame = self.renderer.render_lyric_line(
                    words=words,
                    current_time=test_time,
                    style=style,
                    animation_config=animation_config,
                    line_start=line_start,
                    line_end=line_end,
                    audio_features=None,
                    effects_config=None
                )
                
                # Analyze the render
                alpha_channel = rendered_frame[:, :, 3]
                rows_with_text = np.where(alpha_channel.any(axis=1))[0]
                cols_with_text = np.where(alpha_channel.any(axis=0))[0]
                
                if len(rows_with_text) > 0:
                    # Calculate overall opacity/intensity
                    text_pixels = alpha_channel[alpha_channel > 0]
                    avg_opacity = np.mean(text_pixels) / 255.0
                    max_opacity = np.max(text_pixels) / 255.0
                    text_pixel_count = len(text_pixels)
                    
                    print(f"  Render result: {text_pixel_count} text pixels, avg opacity: {avg_opacity:.2f}, max opacity: {max_opacity:.2f}")
                else:
                    avg_opacity = max_opacity = text_pixel_count = 0
                    print(f"  Render result: NO TEXT DETECTED")
                    
                results.append({
                    "time": test_time,
                    "frame": rendered_frame,
                    "word_states": word_states,
                    "opacity_stats": {
                        "avg": avg_opacity,
                        "max": max_opacity,
                        "pixel_count": text_pixel_count
                    }
                })
                
            except Exception as e:
                print(f"  Render FAILED: {e}")
                results.append({
                    "time": test_time,
                    "frame": None,
                    "word_states": word_states,
                    "error": str(e)
                })
                
        # Create comprehensive visualization
        self.create_word_timing_visualization(text, words, results, animation_config)
        
    def create_word_timing_visualization(self, text, words, results, animation_config):
        """Create visualization showing word timing progression."""
        
        num_time_points = len(results)
        fig, axes = plt.subplots(num_time_points + 1, 2, figsize=(16, 4 * (num_time_points + 1)))
        fig.suptitle(f"Word-Level Animation Debug: '{text}'", fontsize=16, color='white')
        
        # Top row: Word timing diagram
        ax_timing = axes[0, :]
        if len(ax_timing.shape) == 1:
            ax_timing = [ax_timing[0], ax_timing[1]]
        else:
            ax_timing = [axes[0, 0], axes[0, 1]]
            
        # Timeline visualization
        ax_timing[0].set_title("Word Timing Timeline", color='white', fontsize=14)
        
        for i, word in enumerate(words):
            y_pos = len(words) - i - 1
            # Draw word duration bar
            ax_timing[0].barh(y_pos, word.duration, left=word.start_time, height=0.8, 
                             alpha=0.7, color=f'C{i % 10}', label=word.text)
            # Add word delay effect
            if animation_config.word_delay > 0:
                delay_start = word.start_time + i * animation_config.word_delay
                ax_timing[0].axvline(x=delay_start, ymin=y_pos/len(words), ymax=(y_pos+1)/len(words), 
                                   color='red', linewidth=2, alpha=0.7)
                
        # Mark test time points
        for result in results:
            ax_timing[0].axvline(x=result["time"], color='yellow', linewidth=1, alpha=0.8)
            
        ax_timing[0].set_xlabel("Time (seconds)")
        ax_timing[0].set_yticks(range(len(words)))
        ax_timing[0].set_yticklabels([word.text for word in reversed(words)])
        ax_timing[0].grid(True, alpha=0.3)
        
        # Animation config info
        ax_timing[1].set_title("Animation Configuration", color='white', fontsize=14)
        ax_timing[1].axis('off')
        
        config_text = f"""
Animation Type: {animation_config.entrance_type}
Word Delay: {animation_config.word_delay}s
Duration: {animation_config.duration}s
Easing: {animation_config.easing}

ANALYSIS:
Word delay of {animation_config.word_delay}s means each word 
starts animating {animation_config.word_delay}s after the previous.

With {len(words)} words, the last word won't start 
appearing until {(len(words)-1) * animation_config.word_delay:.1f}s into the line.
        """
        
        ax_timing[1].text(0.05, 0.95, config_text, fontsize=11, fontfamily='monospace',
                         transform=ax_timing[1].transAxes, color='white', va='top',
                         bbox=dict(boxstyle="round,pad=0.5", facecolor="#333333", alpha=0.8))
        
        # Show each time point
        for i, result in enumerate(results):
            row = i + 1
            
            # Left: Rendered frame
            if result.get("frame") is not None:
                axes[row, 0].set_title(f"Time: {result['time']:.1f}s", color='white')
                axes[row, 0].imshow(result["frame"], aspect='auto')
                
                # Add opacity info
                opacity_text = f"Avg: {result['opacity_stats']['avg']:.2f}, Max: {result['opacity_stats']['max']:.2f}"
                axes[row, 0].text(0.02, 0.98, opacity_text, transform=axes[row, 0].transAxes,
                                 fontsize=10, color='white', va='top',
                                 bbox=dict(boxstyle="round,pad=0.3", facecolor="black", alpha=0.7))
            else:
                axes[row, 0].set_title(f"Time: {result['time']:.1f}s - RENDER FAILED", color='red')
                axes[row, 0].text(0.5, 0.5, f"Error: {result.get('error', 'Unknown')}", 
                                 ha='center', va='center', transform=axes[row, 0].transAxes,
                                 fontsize=12, color='red')
                axes[row, 0].axis('off')
                
            # Right: Word state analysis
            axes[row, 1].set_title(f"Word States at {result['time']:.1f}s", color='white')
            axes[row, 1].axis('off')
            
            state_text = f"Time: {result['time']:.1f}s\\n\\n"
            for j, word_state in enumerate(result["word_states"]):
                visibility = "VISIBLE" if word_state["adjusted_progress"] > 0.1 else "HIDDEN"
                state_text += f"Word {j}: '{word_state['word']}'\\n"
                state_text += f"  Progress: {word_state['adjusted_progress']*100:.0f}% - {visibility}\\n"
                state_text += f"  State: {word_state['adjusted_state']}\\n\\n"
                
            axes[row, 1].text(0.05, 0.95, state_text, fontsize=9, fontfamily='monospace',
                             transform=axes[row, 1].transAxes, color='white', va='top',
                             bbox=dict(boxstyle="round,pad=0.5", facecolor="#2a2a4a", alpha=0.8))
        
        # Save visualization
        plt.tight_layout()
        fig.savefig(self.debug_output_dir / "word_timing_analysis.png", 
                   dpi=150, bbox_inches='tight', facecolor='#1a1a1a')
        plt.close(fig)
        
        print(f"\n📊 Word timing visualization saved: {self.debug_output_dir / 'word_timing_analysis.png'}")
        
        # Summary analysis
        print("\n🔍 WORD TIMING ANALYSIS SUMMARY:")
        print("=" * 50)
        
        total_line_duration = words[-1].end_time - words[0].start_time
        total_delay_time = (len(words) - 1) * animation_config.word_delay
        
        print(f"Line duration: {total_line_duration:.1f}s")
        print(f"Total word delay spread: {total_delay_time:.1f}s")
        print(f"Word delay per word: {animation_config.word_delay}s")
        
        if total_delay_time > total_line_duration * 0.5:
            print("⚠️  WARNING: Word delay time is more than 50% of line duration!")
            print("   This means later words may not have time to fully appear.")
            
        # Check if last words get enough time
        last_word = words[-1]
        last_word_delay_start = last_word.start_time + (len(words) - 1) * animation_config.word_delay
        last_word_available_time = last_word.end_time - last_word_delay_start
        
        print(f"Last word ('{last_word.text}') analysis:")
        print(f"  Scheduled start: {last_word.start_time:.1f}s")
        print(f"  Delayed start: {last_word_delay_start:.1f}s")
        print(f"  Scheduled end: {last_word.end_time:.1f}s")
        print(f"  Available time for animation: {last_word_available_time:.1f}s")
        
        if last_word_available_time < animation_config.duration:
            print(f"⚠️  PROBLEM IDENTIFIED: Last word only has {last_word_available_time:.1f}s but animation needs {animation_config.duration}s!")
            print("   SOLUTION: Reduce word_delay or increase individual word durations.")


if __name__ == "__main__":
    debugger = WordLevelDebugger()
    debugger.debug_word_timing_issue()
    print(f"\n✅ Word-level debugging complete! Check {debugger.debug_output_dir} for results.")