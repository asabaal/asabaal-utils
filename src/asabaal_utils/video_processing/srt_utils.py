import logging

logger = logging.getLogger(__name__)

def enhance_srt_with_timestamp_mapping(input_file, processors=None):
    """
    Enhance an SRT transcript while preserving timestamp mappings.
    
    Returns:
        dict: With 'enhanced_entries', 'original_entries', and 'position_map'
    """
    import re
    from .transcript_processors import TranscriptEnhancementPipeline
    
    # Define SRT entry pattern
    srt_pattern = re.compile(r'(\d+)\s*?\n(\d{2}:\d{2}:\d{2},\d{3})\s*?-->\s*?(\d{2}:\d{2}:\d{2},\d{3})\s*?\n([\s\S]*?)(?=\n\s*\n\d+\s*\n|$)', re.MULTILINE)
    
    # Read original SRT
    with open(input_file, 'r', encoding='utf-8') as f:
        srt_content = f.read()
    
    # Find all SRT entries
    original_entries = []
    for match in srt_pattern.finditer(srt_content):
        entry_num = match.group(1)
        start_time = match.group(2)
        end_time = match.group(3)
        text = match.group(4).strip()
        
        # Convert timestamp to seconds for easier handling
        start_seconds = convert_timestamp_to_seconds(start_time)
        end_seconds = convert_timestamp_to_seconds(end_time)
        
        original_entries.append({
            'number': entry_num,
            'start_time': start_time,
            'end_time': end_time,
            'start_seconds': start_seconds,
            'end_seconds': end_seconds,
            'text': text,
            'char_start': match.start(4),  # Position in original file
            'char_end': match.end(4)       # Position in original file
        })
    
    # Apply enhancement to text portions
    pipeline = TranscriptEnhancementPipeline(processors=processors)
    
    # Combine all text for enhancement while tracking original positions
    combined_text = ""
    position_map = {}  # Maps positions in combined text to original entry indices
    
    for i, entry in enumerate(original_entries):
        # Add padding between entries to ensure they're separated
        if i > 0:
            combined_text += "\n\n"
        
        # Record mapping of each character
        start_pos = len(combined_text)
        for char_pos in range(start_pos, start_pos + len(entry['text'])):
            position_map[char_pos] = {
                'entry_index': i,
                'relative_pos': char_pos - start_pos,
                'timestamp': entry['start_seconds'] + (entry['end_seconds'] - entry['start_seconds']) * 
                            ((char_pos - start_pos) / len(entry['text']))
            }
        
        combined_text += entry['text']
    
    # Process the combined text
    enhanced_text = pipeline.process(combined_text)
    
    # Create enhanced entries with updated text but original timestamps
    enhanced_entries = []
    current_pos = 0
    
    # This is a simplified approach - a more robust solution would use
    # difflib or other algorithms to track exactly how the text changed
    for i, original in enumerate(original_entries):
        # Find the corresponding enhanced text
        # This is imperfect but a starting point
        try:
            # Extract the portion of enhanced text corresponding to this entry
            # This is approximate and would need refinement
            start_search = max(0, current_pos - 20)
            # Look for unique text from the original entry
            search_snippet = original['text'][:20].replace('\n', ' ').strip()
            if len(search_snippet) < 10 and len(original['text']) > 20:
                search_snippet = original['text'][20:40].replace('\n', ' ').strip()
            
            search_pos = enhanced_text.find(search_snippet, start_search)
            if search_pos >= 0:
                # Find likely end of this entry
                end_search_start = search_pos + len(search_snippet)
                next_entry_start = len(enhanced_text)
                if i < len(original_entries) - 1:
                    next_snippet = original_entries[i+1]['text'][:20].replace('\n', ' ').strip()
                    next_pos = enhanced_text.find(next_snippet, end_search_start)
                    if next_pos >= 0:
                        next_entry_start = next_pos
                
                enhanced_text_portion = enhanced_text[search_pos:next_entry_start].strip()
                current_pos = next_entry_start
            else:
                # Fallback - just use original text
                enhanced_text_portion = original['text']
        except Exception as e:
            logger.warning(f"Error finding enhanced text for entry {i+1}: {e}")
            enhanced_text_portion = original['text']
        
        enhanced_entries.append({
            'number': original['number'],
            'start_time': original['start_time'],
            'end_time': original['end_time'],
            'start_seconds': original['start_seconds'],
            'end_seconds': original['end_seconds'],
            'text': enhanced_text_portion,
            'original_text': original['text']
        })
    
    return {
        'enhanced_entries': enhanced_entries,
        'original_entries': original_entries,
        'enhanced_text': enhanced_text,
        'original_text': combined_text,
        'position_map': position_map
    }

def convert_timestamp_to_seconds(timestamp):
    """Convert SRT timestamp to seconds."""
    hours, minutes, seconds = timestamp.replace(',', '.').split(':')
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def create_analysis_json_from_enhanced_srt(enhanced_srt_data, output_file):
    """
    Create a JSON file suitable for clip analysis from enhanced SRT data.
    
    Args:
        enhanced_srt_data: The output from enhance_srt_with_timestamp_mapping
        output_file: Where to save the analysis-ready JSON
    """
    import json
    
    # Create a structure the analyzer can understand
    analysis_data = {
        "transcript": enhanced_srt_data['enhanced_text'],
        "segments": []
    }
    
    # Add enhanced entries as segments with timestamps
    for entry in enhanced_srt_data['enhanced_entries']:
        analysis_data["segments"].append({
            "text": entry['text'],
            "start_time": entry['start_seconds'],
            "end_time": entry['end_seconds'],
            "original_text": entry['original_text']
        })
    
    # Add metadata about the enhancement
    analysis_data["metadata"] = {
        "format": "enhanced_srt",
        "entries_count": len(enhanced_srt_data['enhanced_entries']),
        "enhanced": True
    }
    
    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_data, f, indent=2)
    
    return analysis_data
