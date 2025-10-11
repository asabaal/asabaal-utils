# Claude Code Program Request: Biblical Visual Gap Analysis Generator

## 🎬 PROJECT OVERVIEW
Create a program that analyzes SRT subtitle files and generates visual concept recommendations with MidJourney prompts to fill timing gaps in video content. This is for a biblical narrative about the Tabernacle construction story.

## 📋 INPUT SPECIFICATIONS

### Primary Input: SRT File
```
Example format:
1
00:00:31,400 --> 00:00:32,666
the Lord has spoken to Moses

2  
00:00:32,666 --> 00:00:35,466
see I have called by name Bezaleel and Aholiab
```

### Visual Timing Input (Three Modes)

**Mode 1: Gap Analysis** - User provides time ranges WHERE VISUALS ARE MISSING
```python
input_mode = "gaps"
gap_times = [
    "36:19-41:15",  # Missing visual here
    "1:05:08-1:15:25",  # Missing visual here
    "2:19:01-2:25:09"   # Missing visual here
]
```

**Mode 2: Existing Visual Locations** - User provides time ranges WHERE VISUALS EXIST
```python
input_mode = "existing_visuals" 
existing_visuals = [
    "0:00-0:36:19",     # Have visuals here
    "0:41:15-1:05:08",  # Have visuals here  
    "1:15:25-2:19:01",  # Have visuals here
    "2:25:09-2:30:00"   # Have visuals here
]
# Program calculates gaps automatically
```

**Mode 3: Full Take** - Generate visuals for entire SRT duration
```python
input_mode = "full_take"
# Program segments entire SRT timeline into logical visual sequences
segment_length = 15  # seconds per concept (user configurable)
```

**Universal Settings:**
- Default MidJourney video length: 5.07 seconds
- Total video duration extracted from SRT end time

## 🎯 OUTPUT REQUIREMENTS

### Visual Concept Structure
For each gap, generate:
1. **Gap Analysis**
   - Time range and duration calculation
   - Narrative context from SRT content
   
2. **Visual Concept**
   - Thematic description based on biblical narrative
   - Scene composition recommendations
   
3. **MidJourney Prompts**
   - Text-to-image prompt (detailed, biblical style)
   - Image-to-video animation prompt
   
4. **Extension Strategy**
   - Math calculation for coverage needs
   - Serial extension prompts if duration > 5.07s
   - Clear extension workflow instructions

## 🔧 MODE-SPECIFIC PROCESSING REQUIREMENTS

### Mode 1: Gap Analysis
**Input Validation:**
- Verify gap times are within SRT duration
- Check for overlapping gaps
- Ensure proper time format (MM:SS or H:MM:SS)

**Processing Logic:**
- Direct gap-to-visual concept mapping
- Extract narrative context from surrounding SRT content
- Calculate exact coverage needs

### Mode 2: Existing Visual Locations  
**Input Validation:**
- Verify existing visual times don't overlap
- Check coverage against total SRT duration
- Validate time format consistency

**Processing Logic:**
- Calculate inverse of existing visuals to find gaps
- Handle edge cases (start/end of video)
- Merge adjacent small gaps (< 2 seconds) into larger concepts
- Ensure no gaps are too small to be meaningful

**Gap Calculation Algorithm:**
```python
def calculate_gaps_from_existing(existing_visuals: List[str], total_duration: float) -> List[str]:
    # Sort existing visuals by start time
    # Find spaces between existing coverage
    # Include beginning/end gaps if needed
    # Filter out gaps smaller than minimum threshold
```

### Mode 3: Full Take
**Input Validation:**
- Validate segment length is reasonable (5-30 seconds recommended)
- Ensure total duration allows for meaningful segmentation

**Processing Logic:**
- Intelligent narrative segmentation based on content themes
- Avoid breaking in middle of related concepts
- Balance segment lengths while respecting narrative flow
- Create thematic visual concepts for each segment

**Segmentation Strategy:**
```python
def intelligent_segmentation(srt_data: List, target_length: float) -> List[Segment]:
    # Analyze narrative flow and themes
    # Identify natural break points
    # Group related content together
    # Adjust segment boundaries for optimal visual concepts
```

## 🔧 TECHNICAL APPROACHES REQUESTED

## Approach 1: Traditional NLP Program

**Requirements:**
- Parse SRT files for timestamps and content
- Calculate gap durations and coverage needs
- Use text analysis to understand narrative context
- Generate prompts using template-based approach
- No GPU requirements - use CPU-only libraries

**Suggested Libraries:**
```python
import re
import datetime
from dataclasses import dataclass
import json
# Optional: spacy, nltk for text analysis
```

**Key Functions Needed:**
```python
def parse_srt_file(srt_content: str) -> List[Subtitle]
def get_total_video_duration(srt_data: List[Subtitle]) -> float
def detect_input_mode(user_input: dict) -> str

# Mode-specific functions
def process_gap_mode(gap_times: List[str], srt_data: List) -> List[Gap]
def process_existing_visuals_mode(existing_times: List[str], total_duration: float) -> List[Gap]  
def process_full_take_mode(total_duration: float, segment_length: float, srt_data: List) -> List[Gap]

# Universal functions
def calculate_gap_duration(start_time: str, end_time: str) -> float
def extract_narrative_context(srt_data: List, gap_time: tuple) -> str
def generate_visual_concept(narrative_context: str, biblical_theme: str) -> str
def create_midjourney_prompts(visual_concept: str) -> dict
def determine_extension_strategy(duration: float) -> dict
def segment_narrative_by_theme(srt_data: List, segment_length: float) -> List[Segment]
```

## Approach 2: Claude SDK Integration Program

**Requirements:**
- Use Claude SDK to make API calls during program execution
- Ask Claude to generate creative prompts based on context
- Leverage Claude's biblical knowledge and creativity
- Structure the conversation with Claude for optimal prompt generation

**Suggested Implementation:**
```python
import anthropic
from typing import List, Dict

class ClaudeVisualGenerator:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def process_input_mode(self, input_data: dict, srt_data: List) -> List[Gap]:
        # Detect mode and process accordingly
        
    def ask_claude_for_visual_concept(self, narrative_context: str, duration: float, mode: str) -> dict:
        # Craft mode-specific prompts for Claude
        
    def ask_claude_for_midjourney_prompts(self, visual_concept: str, biblical_context: str) -> dict:
        # Ask Claude to create specific MidJourney prompts
        
    def ask_claude_for_extension_strategy(self, base_concept: str, duration: float) -> list:
        # Get extension prompts for longer durations
        
    def ask_claude_for_narrative_segmentation(self, srt_content: str, segment_length: float) -> List[Segment]:
        # For full_take mode: ask Claude to intelligently segment narrative
```

## 📊 EXAMPLE EXPECTED OUTPUT

### Mode 1: Gap Analysis Output
```json
{
  "input_mode": "gaps",
  "total_duration": "2:30:00",
  "gaps_processed": 3,
  "results": {
    "gap_1": {
      "time_range": "0:36:19-0:41:15",
      "duration_seconds": 5.0,
      "narrative_context": "working together with divine skill and unified purpose",
      "visual_concept": "Multiple artisan workshops working in perfect coordination",
      "prompts": {
        "text_to_image": "Multiple Hebrew artisan workshops working in perfect synchronization...",
        "image_to_video": "Rhythmic coordinated movement across all workshops..."
      },
      "extension_strategy": {
        "type": "single_clip",
        "coverage": "perfect_fit",
        "extensions_needed": 0
      }
    }
  }
}
```

### Mode 2: Existing Visuals Output  
```json
{
  "input_mode": "existing_visuals",
  "total_duration": "2:30:00", 
  "existing_coverage": ["0:00-0:36:19", "0:41:15-1:05:08"],
  "calculated_gaps": ["0:36:19-0:41:15", "1:05:08-2:30:00"],
  "results": {
    "calculated_gap_1": {
      "time_range": "0:36:19-0:41:15",
      "source": "calculated_from_existing_visuals",
      // ... same structure as gap mode
    }
  }
}
```

### Mode 3: Full Take Output
```json
{
  "input_mode": "full_take",
  "total_duration": "2:30:00",
  "segment_length": 15,
  "segments_created": 10,
  "results": {
    "segment_1": {
      "time_range": "0:00-0:15",
      "narrative_theme": "divine_commissioning", 
      "key_content": "the Lord has spoken to Moses, called Bezaleel and Aholiab",
      "visual_concept": "Divine light streaming down on Moses calling craftsmen",
      // ... same prompt structure
    }
  }
}
```

## 🎨 BIBLICAL VISUAL THEMES TO INCORPORATE

**Core Themes:**
- Divine calling and inspiration
- Community collaboration
- Sacred craftsmanship
- Abundant generosity
- Divine presence manifestation

**Visual Style Keywords:**
- "biblical epic cinematography"
- "ancient Hebrew craftsmanship" 
- "divine golden lighting"
- "sacred workshop atmosphere"
- "desert setting with mountain backdrop"

## 🔄 EXTENSION LOGIC REQUIREMENTS

**Coverage Math:**
- 5.07s default clip length
- Calculate extensions needed: `(gap_duration - 5.07) / 5.07`
- Always recommend SERIAL extensions (same clip extended)
- Provide specific continuation prompts for extensions

**Extension Categories:**
- **Perfect Fit:** Duration ≤ 5.07s → Single clip
- **Short Extension:** 5.07s < Duration ≤ 10.14s → Base + 1 extension  
- **Long Extension:** Duration > 10.14s → Base + multiple extensions

## 🚀 EXECUTION PREFERENCES

### For Traditional Approach:
- Focus on robust SRT parsing and time calculation
- Create comprehensive prompt templates for each mode
- Include biblical knowledge database/keywords
- Generate consistent, high-quality prompts
- **Mode-specific optimization:** Efficient gap calculation algorithms

### For Claude SDK Approach:
- Design conversation flows with Claude for each mode
- Include context management for API calls
- Implement rate limiting and error handling
- Leverage Claude's creativity while maintaining consistency
- **Mode-specific optimization:** Dynamic prompt crafting based on narrative analysis

### Universal Requirements:
- **Flexible input parsing** - Auto-detect mode or explicit mode selection
- **Robust time handling** - Support multiple time formats (MM:SS, H:MM:SS, seconds)
- **Edge case management** - Handle video start/end, overlaps, tiny gaps
- **Output customization** - Allow different output formats (JSON, HTML, CSV)

## 📋 DELIVERABLES REQUESTED

1. **Complete working program** for both approaches
2. **Documentation** explaining usage and setup
3. **Example outputs** using the provided SRT content
4. **Comparison analysis** of both approaches' strengths/weaknesses
5. **Installation/setup instructions** for dependencies

## 🎯 SUCCESS CRITERIA

### Core Functionality:
- **Multi-mode processing** - Seamlessly handles gaps, existing visuals, or full take modes
- **Accurate time parsing** - Correctly processes SRT timing and content for all modes
- **Intelligent gap calculation** - Properly derives missing visuals from existing coverage
- **Smart segmentation** - Creates logical narrative segments for full take mode

### Output Quality:
- **Biblically appropriate visual concepts** - Maintains thematic consistency
- **Detailed MidJourney prompts** - Ready for immediate use, optimized for biblical content
- **Precise extension strategies** - Accurate math and clear workflow instructions
- **Structured professional output** - Clean, organized results for any mode

### Technical Robustness:
- **Edge case handling** - Manages overlaps, tiny gaps, video boundaries
- **Input validation** - Catches and reports format errors gracefully  
- **Performance optimization** - Efficient processing for long videos/many gaps
- **Error recovery** - Continues processing when individual segments fail

### Usability:
- **Mode auto-detection** - Intelligent input parsing
- **Clear documentation** - Easy setup and usage instructions
- **Flexible output formats** - Supports different workflow needs
- **Production-ready reliability** - Consistent results for ongoing content creation

---

**Priority:** This tool will be used for ongoing biblical video content creation, so reliability and ease of use are critical. Both approaches should be production-ready and well-documented.