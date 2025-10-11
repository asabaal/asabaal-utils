"""
Consolidated AI-powered duplicate detection for video transcripts.

This module provides:
- AI and simple text-based duplicate detection
- Interactive HTML report generation with paragraph-style transcript
- CLI interface for easy usage
- Editable duplicate groups functionality
"""

import json
import requests
import time
import argparse
import logging
import sys
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from difflib import SequenceMatcher
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class TranscriptSegment:
    """Represents a segment of transcript with timing."""
    text: str
    start_time: float
    end_time: float
    segment_id: str
    confidence: Optional[float] = None
    words: Optional[List[Dict[str, Any]]] = None


@dataclass
class DuplicateGroup:
    """Represents a group of duplicate segments."""
    group_id: str
    segments: List[TranscriptSegment]
    similarity_score: float
    ai_analysis: str
    ranking: List[Dict[str, Any]]
    recommended_segment: str


@dataclass
class DuplicateDetectionResult:
    """Complete duplicate detection result."""
    video_file: str
    total_segments: int
    duplicate_groups: List[DuplicateGroup]
    processing_time: float
    model_used: str


class DuplicateDetector:
    """Main duplicate detection class."""
    
    def __init__(self, model: str = "llama3.1:8b", use_ai: bool = True):
        self.model = model
        self.use_ai = use_ai
        
    def detect_duplicates(self, transcript_file: Path, similarity_threshold: float = 0.75) -> DuplicateDetectionResult:
        """Detect duplicates in transcript file."""
        start_time = time.time()
        
        # Load transcript
        with open(transcript_file, 'r', encoding='utf-8') as f:
            transcript_data = json.load(f)
        
        # Extract segments
        segments = self._extract_segments(transcript_data)
        
        if self.use_ai:
            duplicate_groups = self._detect_ai_duplicates(segments, similarity_threshold)
            model_used = self.model
        else:
            duplicate_groups = self._detect_simple_duplicates(segments, similarity_threshold)
            model_used = "simple_text_similarity"
        
        processing_time = time.time() - start_time
        
        return DuplicateDetectionResult(
            video_file=str(transcript_file),
            total_segments=len(segments),
            duplicate_groups=duplicate_groups,
            processing_time=processing_time,
            model_used=model_used
        )
    
    def _extract_segments(self, transcript_data: Dict) -> List[TranscriptSegment]:
        """Extract segments from transcript data."""
        segments = []
        
        if 'segments' in transcript_data:
            for i, seg in enumerate(transcript_data['segments']):
                segments.append(TranscriptSegment(
                    text=seg['text'],
                    start_time=seg['start'],
                    end_time=seg['end'],
                    segment_id=seg.get('segment_id', seg.get('id', f'seg_{i}')),
                    words=seg.get('words', [])
                ))
        elif isinstance(transcript_data, list):
            for i, seg in enumerate(transcript_data):
                segments.append(TranscriptSegment(
                    text=seg['text'],
                    start_time=seg['start'],
                    end_time=seg['end'],
                    segment_id=seg.get('segment_id', seg.get('id', f'seg_{i}')),
                    words=seg.get('words', [])
                ))
        
        return segments
    
    def _detect_simple_duplicates(self, segments: List[TranscriptSegment], threshold: float) -> List[DuplicateGroup]:
        """Detect duplicates using improved text similarity for finding multiple takes."""
        duplicate_groups = []
        processed = set()
        
        def normalize_text(text: str) -> str:
            """Normalize text for better duplicate detection."""
            import re
            # Remove extra whitespace, punctuation, and convert to lowercase
            text = re.sub(r'[^\w\s]', '', text.lower())
            text = re.sub(r'\s+', ' ', text.strip())
            return text
        
        def calculate_similarity(text1: str, text2: str) -> float:
            """Calculate similarity with multiple factors."""
            norm1 = normalize_text(text1)
            norm2 = normalize_text(text2)
            
            # Basic sequence similarity
            seq_sim = SequenceMatcher(None, norm1, norm2).ratio()
            
            # Word-level similarity
            words1 = set(norm1.split())
            words2 = set(norm2.split())
            if not words1 or not words2:
                word_sim = 0
            else:
                word_sim = len(words1 & words2) / len(words1 | words2)
            
            # Length similarity (penalize very different lengths)
            len_sim = 1 - abs(len(norm1) - len(norm2)) / max(len(norm1), len(norm2))
            
            # Weighted combination
            return (seq_sim * 0.5 + word_sim * 0.3 + len_sim * 0.2)
        
        for i, seg1 in enumerate(segments):
            if i in processed:
                continue
                
            similar_segments = [seg1]
            similarities = []
            
            for j, seg2 in enumerate(segments[i+1:], i+1):
                if j in processed:
                    continue
                    
                similarity = calculate_similarity(seg1.text, seg2.text)
                
                # Only consider as duplicate if similarity is high AND texts are substantial
                if similarity >= threshold and len(seg1.text.strip()) > 10 and len(seg2.text.strip()) > 10:
                    similar_segments.append(seg2)
                    similarities.append(similarity)
                    processed.add(j)
            
            if len(similar_segments) > 1:
                group_id = f"group_{len(duplicate_groups) + 1}"
                avg_similarity = sum(similarities) / len(similarities) if similarities else 0
                
                # Rank segments by quality (longer, more complete segments get higher scores)
                scored_segments = []
                for seg in similar_segments:
                    # Score based on length and completeness
                    word_count = len(seg.text.split())
                    completeness = min(1.0, word_count / 10)  # Assume 10+ words is complete
                    score = completeness * 0.7 + (1 - abs(seg.end_time - seg.start_time - 5) / 10) * 0.3  # Prefer 5-second segments
                    scored_segments.append({
                        "segment_id": seg.segment_id, 
                        "score": score,
                        "word_count": word_count
                    })
                
                # Sort by score and pick the best as recommended
                scored_segments.sort(key=lambda x: x["score"], reverse=True)
                
                duplicate_groups.append(DuplicateGroup(
                    group_id=group_id,
                    segments=similar_segments,
                    similarity_score=avg_similarity,
                    ai_analysis=f"Found {len(similar_segments)} similar takes (avg similarity: {avg_similarity:.1%})",
                    ranking=scored_segments,
                    recommended_segment=scored_segments[0]["segment_id"]
                ))
                processed.add(i)
        
        return duplicate_groups
    
    def _detect_ai_duplicates(self, segments: List[TranscriptSegment], threshold: float) -> List[DuplicateGroup]:
        """Detect duplicates using AI (placeholder for now)."""
        # For now, fall back to simple detection
        logger.warning("AI detection not fully implemented, using simple text similarity")
        return self._detect_simple_duplicates(segments, threshold)


class DuplicateReportGenerator:
    """Generate interactive HTML reports."""
    
    def __init__(self):
        pass
    
    def generate_report(self, result: DuplicateDetectionResult, video_file: str, 
                       output_file: Path, transcript_segments: Optional[List[TranscriptSegment]] = None):
        """Generate interactive HTML report with paragraph-style transcript."""
        
        # Load original transcript data to get word-level timings
        original_transcript_data = None
        try:
            with open('/home/asabaal/episode3_combined/combined_transcript.json', 'r') as f:
                original_transcript_data = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load original transcript for word data: {e}")
            original_transcript_data = {'segments': []}
        
        def format_time(seconds: float) -> str:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes:02d}:{secs:02d}"
        
        def generate_transcript_html(segments, duplicate_groups):
            """Generate continuous paragraph transcript with inline editing and timestamps."""
            # Use original transcript data for consistency with JavaScript
            original_segments = original_transcript_data.get('segments', [])
            
            if not original_segments:
                return ""
            
            # Create mapping of segment IDs to duplicate groups
            segment_to_group = {}
            for i, group in enumerate(duplicate_groups):
                for segment in group.segments:
                    segment_to_group[segment.segment_id] = i + 1
            
            html_parts = ['<div class="transcript-section">']
            html_parts.append('<h2>📝 Interactive Transcript</h2>')
            html_parts.append('<p>Click any highlighted segment to play or edit. Duplicate segments are color-coded and can be grouped/ungrouped.</p>')
            html_parts.append('<div class="transcript-controls">')
            html_parts.append('<button class="create-group-button" onclick="createNewGroup()">➕ Create New Group</button>')
            html_parts.append('<button class="edit-groups-button" onclick="openGroupEditor()">📝 Edit Groups</button>')
            html_parts.append('<button class="toggle-edit-mode" onclick="toggleEditMode()">✏️ Toggle Edit Mode</button>')
            html_parts.append('<button class="save-transcript-button" onclick="saveTranscript()" id="saveButton" style="display:none;">💾 Save Transcript</button>')
            html_parts.append('<button class="download-transcript-button" onclick="downloadTranscript()">📥 Download</button>')
            html_parts.append('<div class="save-status" id="saveStatus"></div>')
            html_parts.append('</div>')
            html_parts.append('<div class="edit-indicator" id="editIndicator">')
            html_parts.append('✏️ <strong>Edit Mode Active</strong> - Click any segment to edit. Changes are auto-saved to browser storage.')
            html_parts.append('<span class="word-count" id="wordCount">0 words</span>')
            html_parts.append('</div>')
            html_parts.append('<div class="transcript-paragraph">')
            
            for i, segment in enumerate(original_segments):
                segment_id = segment.get('segment_id', segment.get('id', f'seg_{i}'))
                group_class = ""
                group_info = ""
                is_duplicate = segment_id in segment_to_group
                
                if is_duplicate:
                    group_num = segment_to_group[segment_id]
                    group_class = f"duplicate-highlight duplicate-group-{group_num}"
                    group_info = f'data-group="{group_num}" data-segment-id="{segment_id}"'
                
                # Segment with line break, timestamp, and full controls
                segment_html = f'''
                <div class="transcript-line" data-segment-id="{segment_id}">
                    <div class="segment-controls">
                        <button class="segment-group-btn" onclick="openSegmentGroupMenu('{segment_id}', event)" title="Assign to group">📋</button>
                        <button class="segment-play-btn" onclick="playSegment({segment['start']}, {segment['end']})" title="Play segment">▶️</button>
                        <button class="segment-edit-btn" onclick="enableInlineEdit('{segment_id}', event)" title="Edit text">✏️</button>
                        <button class="segment-merge-previous-btn" onclick="mergeWithPrevious('{segment_id}', event)" title="Merge with previous">⬅️</button>
                        <button class="segment-merge-next-btn" onclick="mergeWithNext('{segment_id}', event)" title="Merge with next">➡️</button>
                    </div>
                    <span class="transcript-segment {group_class}" 
                          {group_info}
                          data-start="{segment['start']}" 
                          data-end="{segment['end']}"
                          data-segment-id="{segment_id}"
                          data-words-count="{len(segment.get('words', []))}"
                          title="{format_time(segment['start'])} - {format_time(segment['end'])}"
                          onclick="handleSegmentClick(this, {segment['start']}, {segment['end']}, '{segment_id}')"
                          contenteditable="false">{segment['text']}</span>
                    <div class="segment-timestamp">{format_time(segment['start'])}</div>
                </div>'''
                
                html_parts.append(segment_html)
            
            html_parts.append('</div>')
            html_parts.append('</div>')
            return ''.join(html_parts)
        
        def generate_duplicate_groups_html(duplicate_groups):
            """Generate HTML for duplicate groups with editing capabilities."""
            if not duplicate_groups:
                return ""
            
            groups_html = ""
            for group in duplicate_groups:
                segments_html = ""
                for segment in group.segments:
                    is_recommended = segment.segment_id == group.recommended_segment
                    recommended_badge = '<span class="recommended-badge">⭐ RECOMMENDED</span>' if is_recommended else ''
                    
                    segments_html += f'''
                    <div class="segment-card {'recommended' if is_recommended else ''}" 
                         data-segment-id="{segment.segment_id}"
                         onclick="playSegment({segment.start_time}, {segment.end_time})">
                        <div class="segment-header">
                            <span class="segment-time">⏰ {format_time(segment.start_time)} - {format_time(segment.end_time)}</span>
                            <div>
                                {recommended_badge}
                                <button class="play-button" onclick="event.stopPropagation(); playSegment({segment.start_time}, {segment.end_time})">▶ Play</button>
                                <button class="edit-button" onclick="event.stopPropagation(); toggleSegmentEdit('{segment.segment_id}')">✏️ Edit</button>
                            </div>
                        </div>
                        <div class="segment-text" id="text-{segment.segment_id}">{segment.text}</div>
                        <input type="text" class="segment-edit-input" id="edit-{segment.segment_id}" 
                               value="{segment.text}" style="display:none;" 
                               onblur="saveSegmentEdit('{segment.segment_id}')">
                    </div>'''
                
                groups_html += f'''
                <div class="duplicate-group" data-group-id="{group.group_id}">
                    <div class="group-header">
                        <div>
                            <div class="group-title">🔄 Duplicate Group {group.group_id.split('_')[1]}</div>
                            <p style="color: #718096; margin-top: 5px;">{group.ai_analysis}</p>
                        </div>
                        <div>
                            <div class="similarity-badge">{group.similarity_score:.1%} Similar</div>
                            <button class="edit-group-button" onclick="toggleGroupEdit('{group.group_id}')">📝 Edit Group</button>
                        </div>
                    </div>
                    <div class="segments-grid">
                        {segments_html}
                    </div>
                    <div class="group-edit-controls" id="group-edit-{group.group_id}" style="display:none;">
                        <button class="add-segment-button" onclick="showAddSegmentDialog('{group.group_id}')">➕ Add Segment</button>
                        <button class="remove-group-button" onclick="removeGroup('{group.group_id}')">🗑️ Remove Group</button>
                    </div>
                </div>'''
            
            return groups_html
        
        # Generate complete HTML
        html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interactive Duplicate Analysis Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }}
        
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        
        .header {{
            background: white; border-radius: 16px; padding: 30px;
            margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            text-align: center;
        }}
        
        .header h1 {{ font-size: 2.5rem; color: #2d3748; margin-bottom: 10px; }}
        .header p {{ color: #718096; font-size: 1.1rem; }}
        
        .summary-cards {{
            display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px; margin-bottom: 30px;
        }}
        
        .summary-card {{
            background: white; border-radius: 12px; padding: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center;
            transition: transform 0.2s;
        }}
        
        .summary-card:hover {{ transform: translateY(-2px); }}
        .summary-card h3 {{ font-size: 2.5rem; margin-bottom: 5px; font-weight: bold; }}
        .summary-card.primary h3 {{ color: #667eea; }}
        .summary-card.warning h3 {{ color: #f6ad55; }}
        .summary-card.success h3 {{ color: #48bb78; }}
        .summary-card.info h3 {{ color: #4299e1; }}
        .summary-card p {{ color: #718096; font-size: 0.95rem; }}
        
        .transcript-section {{
            background: white; border-radius: 16px; padding: 30px;
            margin-bottom: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        
        .transcript-section h2 {{
            color: #2d3748; margin-bottom: 20px; font-size: 1.8rem;
            border-bottom: 2px solid #e2e8f0; padding-bottom: 10px;
        }}
        
        .transcript-controls {{
            margin-bottom: 15px; padding: 10px; background: #f7fafc;
            border-radius: 8px; display: flex; gap: 10px; flex-wrap: wrap;
        }}
        
        .create-group-button, .edit-groups-button, .toggle-edit-mode, .save-transcript-button, .download-transcript-button {{
            background: #4299e1; color: white; border: none; padding: 10px 16px;
            border-radius: 6px; cursor: pointer; font-size: 0.9rem;
            transition: background 0.2s; margin-right: 8px;
        }}
        
        .edit-groups-button {{
            background: #9f7aea;
        }}
        
        .edit-groups-button:hover {{
            background: #805ad5;
        }}
        
        .create-group-button:hover, .toggle-edit-mode:hover, .save-transcript-button:hover, .download-transcript-button:hover {{
            background: #3182ce;
        }}
        
        .save-transcript-button {{
            background: #48bb78;
        }}
        
        .save-transcript-button:hover {{
            background: #38a169;
        }}
        
        .download-transcript-button {{
            background: #ed8936;
        }}
        
        .download-transcript-button:hover {{
            background: #dd6b20;
        }}
        
        .save-status {{
            margin-left: auto; padding: 6px 12px; border-radius: 4px;
            font-size: 0.85rem; font-weight: 500; opacity: 0;
            transition: opacity 0.3s;
        }}
        
        .save-status.success {{
            background: #c6f6d5; color: #22543d;
            opacity: 1;
        }}
        
        .save-status.error {{
            background: #fed7d7; color: #742a2a;
            opacity: 1;
        }}
        
        .edit-indicator {{
            background: #fef5e7; border: 1px solid #f6ad55;
            padding: 8px 12px; border-radius: 6px; margin-bottom: 15px;
            color: #744210; font-size: 0.9rem; display: none;
            align-items: center; gap: 8px;
        }}
        
        .edit-indicator.show {{
            display: flex;
        }}
        
        .word-count {{
            margin-left: auto; font-size: 0.8rem; color: #718096;
            background: #edf2f7; padding: 4px 8px; border-radius: 4px;
        }}
        
        .transcript-paragraph {{
            font-size: 1.1rem; line-height: 1.6; color: #2d3748;
            padding: 25px; background: #f8f9fa; border-radius: 12px;
            position: relative; min-height: 200px;
        }}
        
        .transcript-line {{
            margin-bottom: 12px; position: relative; padding: 8px 0;
            border-bottom: 1px solid #e2e8f0; transition: background-color 0.2s;
            display: flex; align-items: flex-start; gap: 8px;
        }}
        
        .segment-controls {{
            display: flex; gap: 4px; opacity: 0; transition: opacity 0.2s;
            flex-shrink: 0; margin-top: 2px;
        }}
        
        .transcript-line:hover .segment-controls {{
            opacity: 1;
        }}
        
        .segment-group-btn, .segment-play-btn, .segment-edit-btn, .segment-merge-previous-btn, .segment-merge-next-btn {{
            background: #edf2f7; border: 1px solid #cbd5e0; border-radius: 4px;
            padding: 2px 6px; cursor: pointer; font-size: 0.8rem;
            transition: all 0.2s; line-height: 1;
        }}
        
        .segment-group-btn:hover, .segment-play-btn:hover {{
            background: #4299e1; color: white; border-color: #4299e1;
        }}
        
        .segment-edit-btn {{
            background: #fef3c7; border-color: #fcd34d;
        }}
        
        .segment-edit-btn:hover {{
            background: #fbbf24; color: #78350f; border-color: #f59e0b;
        }}
        
        .segment-merge-previous-btn {{
            background: #e0e7ff; border-color: #c7d2fe;
        }}
        
        .segment-merge-previous-btn:hover {{
            background: #818cf8; color: white; border-color: #818cf8;
        }}
        
        .segment-merge-next-btn {{
            background: #dcfce7; border-color: #bbf7d0;
        }}
        
        .segment-merge-next-btn:hover {{
            background: #22c55e; color: white; border-color: #22c55e;
        }}
        
        // Old merge selection styles removed
        
        .transcript-line:hover {{
            background-color: rgba(66, 153, 225, 0.05);
            border-radius: 6px;
        }}
        
        .transcript-segment {{
            cursor: pointer; padding: 3px 6px; border-radius: 4px;
            transition: all 0.2s ease; display: inline; position: relative;
            border-bottom: 1px solid transparent; font-size: 1.05rem;
            line-height: 1.5;
        }}
        
        .transcript-segment:hover {{
            background: rgba(66, 153, 225, 0.1); border-bottom-color: #4299e1;
        }}
        
        .transcript-segment[contenteditable="true"] {{
            background: white; border: 1px solid #4299e1;
            padding: 4px 8px; border-radius: 4px; outline: none;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1); font-size: 1.05rem;
        }}
        
        .segment-timestamp {{
            font-size: 0.75rem; color: #718096; margin-top: 6px;
            font-weight: 500; opacity: 0.7; font-family: 'Monaco', 'Menlo', monospace;
            background: #edf2f7; padding: 2px 6px; border-radius: 3px;
            display: inline-block;
        }}
        
        .duplicate-highlight {{
            font-weight: 600; border-radius: 4px; padding: 3px 8px;
            position: relative; border-bottom: 2px solid;
        }}
        
        .duplicate-highlight:hover {{
            transform: translateY(-2px); box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }}
        
        .duplicate-highlight.duplicate-group-1 {{
            background: #fed7d7; color: #c53030; border-bottom-color: #f56565;
        }}
        .duplicate-highlight.duplicate-group-1:hover {{ background: #fc8181; color: white; }}
        
        .duplicate-highlight.duplicate-group-2 {{
            background: #feebc8; color: #c05621; border-bottom-color: #ed8936;
        }}
        .duplicate-highlight.duplicate-group-2:hover {{ background: #f6ad55; color: white; }}
        
        .duplicate-highlight.duplicate-group-3 {{
            background: #b2f5ea; color: #2c7a7b; border-bottom-color: #38b2ac;
        }}
        .duplicate-highlight.duplicate-group-3:hover {{ background: #4fd1c5; color: white; }}
        
        .video-section {{
            background: white; border-radius: 16px; padding: 30px;
            margin-bottom: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        
        .video-section h2 {{ color: #2d3748; margin-bottom: 20px; font-size: 1.5rem; }}
        
        .grid-controls {{
            background: #f7fafc; padding: 15px; border-radius: 8px; margin-bottom: 20px;
            display: flex; flex-wrap: wrap; gap: 15px; align-items: center;
        }}
        
        .grid-size-control, .group-selector {{
            display: flex; align-items: center; gap: 10px;
        }}
        
        .grid-size-control label, .group-selector label {{
            font-weight: 500; color: #4a5568;
        }}
        
        .grid-size-control select, .group-selector select {{
            padding: 6px 10px; border: 1px solid #cbd5e0; border-radius: 4px;
            background: white; color: #2d3748; min-width: 120px;
        }}
        
        .grid-info {{
            margin-left: auto; padding: 8px 12px; background: #edf2f7;
            border-radius: 6px; font-size: 0.9rem; color: #4a5568;
        }}
        
        .video-grid {{
            display: grid; gap: 15px; margin-bottom: 20px;
            grid-template-columns: repeat(2, 1fr); /* Default 2 videos */
            min-height: 400px; max-width: 100%;
        }}
        
        .video-grid.size-1 {{ grid-template-columns: repeat(1, 1fr); }}
        .video-grid.size-2 {{ grid-template-columns: repeat(2, 1fr); }}
        .video-grid.size-4 {{ 
            grid-template-columns: repeat(2, 1fr); 
            grid-template-rows: repeat(2, 1fr);
        }}
        
        .grid-placeholder {{
            grid-column: 1 / -1; display: flex; flex-direction: column; align-items: center;
            justify-content: center; padding: 60px 20px; color: #718096;
            background: #f8f9fa; border-radius: 12px; border: 2px dashed #cbd5e0;
        }}
        
        .placeholder-icon {{
            font-size: 3rem; margin-bottom: 15px;
        }}
        
        .video-item {{
            background: white; border-radius: 8px; overflow: hidden;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1); transition: all 0.2s;
            border: 2px solid transparent;
        }}
        
        .video-item:hover {{
            transform: translateY(-2px); box-shadow: 0 8px 20px rgba(0,0,0,0.15);
            border-color: #4299e1;
        }}
        
        .video-item.active {{
            border-color: #48bb78; box-shadow: 0 0 0 3px rgba(72, 187, 120, 0.2);
        }}
        
        .video-header {{
            background: linear-gradient(135deg, #667eea, #764ba2); color: white;
            padding: 10px 12px; font-size: 0.9rem; font-weight: 600;
        }}
        
        .video-content {{
            position: relative; background: #000; width: 100%; height: 100%;
            min-height: 200px; display: flex; align-items: center; justify-content: center;
        }}
        
        .video-item video {{
            width: 100%; height: 100%; object-fit: contain; /* Use 'contain' to maintain aspect ratio */
            max-width: 100%; max-height: 100%;
        }}
        
        .video-overlay {{
            position: absolute; bottom: 0; left: 0; right: 0;
            background: linear-gradient(transparent, rgba(0,0,0,0.8));
            color: white; padding: 8px 12px; font-size: 0.8rem;
        }}
        
        .video-time {{
            font-family: monospace; opacity: 0.9;
        }}
        
        .video-text {{
            margin-top: 4px; line-height: 1.3; max-height: 2.6em;
            overflow: hidden; text-overflow: ellipsis;
        }}
        
        .video-controls-panel {{
            background: #f7fafc; padding: 15px; border-radius: 8px;
            display: flex; justify-content: space-between; align-items: center;
            flex-wrap: wrap; gap: 15px;
        }}
        
        .clip-controls {{
            display: flex; gap: 15px; align-items: center;
        }}
        
        .clip-controls label {{
            display: flex; align-items: center; gap: 5px; cursor: pointer;
            font-size: 0.9rem; color: #4a5568;
        }}
        
        .grid-info-text {{
            margin-left: auto; padding: 8px 12px; background: #edf2f7;
            border-radius: 6px; font-size: 0.9rem; color: #4a5568;
        }}
        
        /* Group Management UI */
        .segment-group-menu {{
            position: fixed; background: white; border: 1px solid #cbd5e0;
            border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            z-index: 1000; min-width: 200px; display: none;
        }}
        
        .group-menu-header {{
            padding: 12px 16px; font-weight: 600; color: #2d3748;
            border-bottom: 1px solid #e2e8f0; background: #f7fafc;
            border-radius: 8px 8px 0 0;
        }}
        
        .group-menu-item {{
            padding: 10px 16px; cursor: pointer; transition: background 0.2s;
            border-bottom: 1px solid #f7fafc; font-size: 0.9rem;
        }}
        
        .group-menu-item:hover {{
            background: #edf2f7;
        }}
        
        .group-menu-item.selected {{
            background: #4299e1; color: white;
        }}
        
        .group-menu-divider {{
            height: 1px; background: #e2e8f0; margin: 4px 0;
        }}
        
        .group-editor-overlay {{
            position: fixed; top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.5); z-index: 2000; display: flex;
            align-items: center; justify-content: center; padding: 20px;
        }}
        
        .group-editor {{
            background: white; border-radius: 12px; max-width: 800px;
            max-height: 80vh; width: 100%; overflow: hidden;
            box-shadow: 0 20px 40px rgba(0,0,0,0.2);
        }}
        
        .group-editor-header {{
            display: flex; justify-content: space-between; align-items: center;
            padding: 20px 24px; border-bottom: 1px solid #e2e8f0;
            background: #f8f9fa;
        }}
        
        .group-editor-header h3 {{
            margin: 0; color: #2d3748; font-size: 1.3rem;
        }}
        
        .close-btn {{
            background: none; border: none; font-size: 1.5rem; cursor: pointer;
            color: #718096; padding: 4px; border-radius: 4px; transition: all 0.2s;
        }}
        
        .close-btn:hover {{
            background: #fed7d7; color: #c53030;
        }}
        
        .group-editor-content {{
            padding: 24px; overflow-y: auto; max-height: calc(80vh - 80px);
        }}
        
        .no-groups-message {{
            text-align: center; padding: 40px; color: #718096;
        }}
        
        .group-editor-group {{
            margin-bottom: 32px; border: 1px solid #e2e8f0; border-radius: 8px;
            overflow: hidden;
        }}
        
        .group-editor-group-header {{
            display: flex; justify-content: space-between; align-items: center;
            padding: 16px 20px; background: #f7fafc; border-bottom: 1px solid #e2e8f0;
        }}
        
        .group-editor-group-header h4 {{
            margin: 0; color: #2d3748; font-size: 1.1rem;
        }}
        
        .group-actions {{
            display: flex; gap: 8px;
        }}
        
        .group-action-btn {{
            background: #4299e1; color: white; border: none; padding: 6px 12px;
            border-radius: 4px; cursor: pointer; font-size: 0.8rem;
            transition: background 0.2s;
        }}
        
        .group-action-btn:hover {{
            background: #3182ce;
        }}
        
        .group-action-btn.delete {{
            background: #e53e3e;
        }}
        
        .group-action-btn.delete:hover {{
            background: #c53030;
        }}
        
        .group-segments {{
            padding: 16px 20px;
        }}
        
        .group-segment-item {{
            display: flex; align-items: flex-start; gap: 12px; padding: 12px;
            border: 1px solid #e2e8f0; border-radius: 6px; margin-bottom: 8px;
            transition: background 0.2s; position: relative;
        }}
        
        .group-segment-item:hover {{
            background: #f7fafc;
        }}
        
        .segment-info {{
            display: flex; align-items: center; gap: 8px; flex-shrink: 0;
            font-size: 0.85rem; color: #4a5568;
        }}
        
        .segment-index {{
            font-weight: 600; color: #2d3748;
        }}
        
        .segment-play-small {{
            background: #48bb78; color: white; border: none; padding: 2px 6px;
            border-radius: 3px; cursor: pointer; font-size: 0.7rem;
        }}
        
        .segment-text {{
            flex: 1; line-height: 1.4; color: #2d3748; font-size: 0.9rem;
        }}
        
        .remove-segment-btn {{
            background: #fed7d7; color: #c53030; border: none; padding: 4px 8px;
            border-radius: 4px; cursor: pointer; font-size: 0.8rem; opacity: 0;
            transition: opacity 0.2s;
        }}
        
        .group-segment-item:hover .remove-segment-btn {{
            opacity: 1;
        }}
        
        /* Split Dialog Styles */
        .split-dialog-overlay {{
            position: fixed; top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.5); z-index: 3000; display: flex;
            align-items: center; justify-content: center; padding: 20px;
        }}
        
        .split-dialog {{
            background: white; border-radius: 12px; max-width: 600px;
            width: 100%; max-height: 80vh; overflow: hidden;
            box-shadow: 0 20px 40px rgba(0,0,0,0.2);
        }}
        
        .split-dialog-header {{
            display: flex; justify-content: space-between; align-items: center;
            padding: 20px 24px; border-bottom: 1px solid #e2e8f0;
            background: #f8f9fa;
        }}
        
        .split-dialog-header h3 {{
            margin: 0; color: #2d3748; font-size: 1.3rem;
        }}
        
        .split-dialog-content {{
            padding: 24px; overflow-y: auto; max-height: calc(80vh - 80px);
        }}
        
        .words-container {{
            margin: 20px 0; padding: 16px; background: #f7fafc;
            border-radius: 8px; font-size: 1.1rem; line-height: 1.6;
        }}
        
        .word-item {{
            cursor: pointer; padding: 2px 4px; border-radius: 3px;
            transition: background 0.2s; margin: 0 2px;
        }}
        
        .word-item:hover {{
            background: #edf2f7;
        }}
        
        .word-item.part1 {{
            background: rgba(66, 153, 225, 0.2); color: #2c5282;
        }}
        
        .word-item.part2 {{
            background: rgba(237, 137, 54, 0.2); color: #c05621;
        }}
        
        .split-preview {{
            margin: 20px 0; padding: 16px; background: #edf2f7;
            border-radius: 8px;
        }}
        
        .preview-part {{
            margin-bottom: 12px; padding: 12px; background: white;
            border-radius: 6px; border-left: 4px solid #4299e1;
        }}
        
        .preview-part:last-child {{
            border-left-color: #ed8936;
            margin-bottom: 0;
        }}
        
        .split-dialog-actions {{
            display: flex; gap: 12px; justify-content: flex-end;
            margin-top: 24px;
        }}
        
        .cancel-btn {{
            background: #e2e8f0; color: #4a5568; border: none;
            padding: 10px 20px; border-radius: 6px; cursor: pointer;
            font-size: 0.9rem; transition: background 0.2s;
        }}
        
        .cancel-btn:hover {{
            background: #cbd5e0;
        }}
        
        .split-confirm-btn {{
            background: #4299e1; color: white; border: none;
            padding: 10px 20px; border-radius: 6px; cursor: pointer;
            font-size: 0.9rem; transition: background 0.2s;
        }}
        
        .split-confirm-btn:hover {{
            background: #3182ce;
        }}
        
        .split-confirm-btn:disabled {{
            background: #cbd5e0; cursor: not-allowed;
        }}
        
        /* Old merge instructions removed - now using specific merge buttons */
        
        .master-pause-btn {{ background: #ed8936; }}
        .master-reset-btn {{ background: #718096; }}
        
        .master-play-btn:hover {{ background: #3182ce; }}
        .master-pause-btn:hover {{ background: #dd6b20; }}
        .master-reset-btn:hover {{ background: #4a5568; }}
        
        .grid-pagination {{
            display: flex; justify-content: center; align-items: center;
            gap: 15px; margin-bottom: 20px; padding: 10px;
            background: #f7fafc; border-radius: 8px;
        }}
        
        .pagination-btn {{
            background: #4299e1; color: white; border: none; padding: 8px 16px;
            border-radius: 6px; cursor: pointer; font-size: 0.9rem;
            transition: background 0.2s;
        }}
        
        .pagination-btn:hover:not(:disabled) {{ background: #3182ce; }}
        .pagination-btn:disabled {{ background: #cbd5e0; cursor: not-allowed; }}
        
        .page-info {{
            font-weight: 500; color: #4a5568; font-size: 0.9rem;
        }}
        
        .duplicates-section {{
            background: white; border-radius: 16px; padding: 30px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        
        .duplicates-section h2 {{ color: #2d3748; margin-bottom: 25px; font-size: 1.5rem; }}
        
        .duplicate-group {{
            background: #f7fafc; border-radius: 12px; padding: 25px;
            margin-bottom: 25px; border-left: 5px solid #667eea;
        }}
        
        .group-header {{
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 20px; flex-wrap: wrap; gap: 15px;
        }}
        
        .group-title {{ font-size: 1.3rem; color: #2d3748; font-weight: 600; }}
        
        .similarity-badge {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white; padding: 8px 16px; border-radius: 20px;
            font-weight: bold; font-size: 0.9rem;
        }}
        
        .edit-group-button, .add-segment-button, .remove-group-button {{
            background: #4299e1; color: white; border: none; padding: 6px 12px;
            border-radius: 6px; cursor: pointer; font-size: 0.8rem; margin-left: 8px;
        }}
        
        .remove-group-button {{ background: #e53e3e; }}
        
        .segments-grid {{ display: grid; gap: 15px; }}
        
        .segment-card {{
            background: white; border-radius: 8px; padding: 20px;
            border: 2px solid #e2e8f0; transition: all 0.2s; cursor: pointer;
        }}
        
        .segment-card:hover {{ border-color: #667eea; box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1); }}
        
        .segment-card.recommended {{ border-color: #48bb78; background: linear-gradient(135deg, #f0fff4, #ffffff); }}
        
        .segment-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }}
        
        .segment-time {{
            background: #edf2f7; color: #4a5568; padding: 4px 10px;
            border-radius: 6px; font-size: 0.85rem; font-weight: 600;
        }}
        
        .segment-text {{ color: #2d3748; line-height: 1.6; font-size: 1rem; }}
        
        .segment-edit-input {{
            width: 100%; padding: 8px; border: 1px solid #cbd5e0;
            border-radius: 4px; font-size: 1rem; margin-top: 8px;
        }}
        
        .play-button, .edit-button {{
            background: #667eea; color: white; border: none; padding: 8px 16px;
            border-radius: 6px; cursor: pointer; font-size: 0.85rem; margin-left: 8px;
        }}
        
        .edit-button {{ background: #ed8936; }}
        
        .group-edit-controls {{
            margin-top: 15px; padding-top: 15px; border-top: 1px solid #e2e8f0;
        }}
        
        .no-duplicates {{
            text-align: center; padding: 60px 20px; color: #718096;
        }}
        
        .footer {{ text-align: center; margin-top: 40px; padding: 20px; color: white; font-size: 0.9rem; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎬 Interactive Duplicate Analysis</h1>
            <p>Edit and manage duplicate groups with real-time updates</p>
        </div>

        <div class="summary-cards">
            <div class="summary-card primary">
                <h3>{result.total_segments}</h3>
                <p>Total Segments</p>
            </div>
            <div class="summary-card warning">
                <h3>{len(result.duplicate_groups)}</h3>
                <p>Duplicate Groups</p>
            </div>
            <div class="summary-card success">
                <h3>{result.processing_time:.1f}s</h3>
                <p>Processing Time</p>
            </div>
            <div class="summary-card info">
                <h3>{result.model_used}</h3>
                <p>AI Model</p>
            </div>
        </div>

        {generate_transcript_html(transcript_segments, result.duplicate_groups)}

        <div class="video-section">
            <h2>🎬 Video Grid Comparison</h2>
            <div class="grid-controls">
            <div class="grid-size-control">
                <label for="gridSize">Grid Size:</label>
                <select id="gridSize">
                    <option value="1">1 (Single)</option>
                    <option value="2" selected>2 (Side-by-side)</option>
                    <option value="4">4 (2x2 Grid)</option>
                </select>
            </div>
                <div class="group-selector">
                    <label for="groupSelect">Select Group:</label>
                    <select id="groupSelect">
                        <option value="">Choose a group...</option>
                    </select>
                </div>
                <div class="grid-info">
                    <span id="gridStatus">Select a group to compare segments</span>
                </div>
            </div>
            <div class="video-grid" id="videoGrid">
                <div class="grid-placeholder">
                    <div class="placeholder-icon">🎬</div>
                    <p>Select a duplicate group to view side-by-side comparison</p>
                </div>
            </div>
            <div class="grid-pagination" id="gridPagination" style="display: none;">
                <button class="pagination-btn" id="prevPage" onclick="changeGridPage(-1)">← Previous</button>
                <span class="page-info" id="pageInfo">Page 1 of 1</span>
                <button class="pagination-btn" id="nextPage" onclick="changeGridPage(1)">Next →</button>
            </div>
            <div class="grid-controls-panel">
                <div class="clip-controls">
                    <label>
                        <input type="checkbox" id="loopClips" checked> Loop Clips
                    </label>
                </div>
                <div class="grid-info-text">
                    <span>📹 Use individual video controls for each segment</span>
                </div>
            </div>
        </div>



        <div class="footer">
            <p>Interactive duplicate detection with editing capabilities • Processing time: {result.processing_time:.1f} seconds</p>
        </div>
    </div>

    <script>
        let editMode = false;
        let selectedSegments = [];
        let groupCounter = {len(result.duplicate_groups) + 1};
        
        // Video Grid Variables
        let currentGroup = null;
        let currentPage = 0;
        let gridSize = 2;
        let gridVideos = [];
        let loopClips = true;
        
        // Use original transcript data to get word-level timings
        let originalTranscript = {json.dumps(original_transcript_data.get('segments', []))};
        
        // Convert to our format with word data
        let transcriptSegments = originalTranscript.map(seg => ({{
            'segment_id': seg.segment_id || seg.id || 'unknown',
            'text': seg.text,
            'start': seg.start,
            'end': seg.end,
            'words': seg.words || []
        }}));
        
        // Debug: Check if we have word data now
        console.log('First segment words count:', transcriptSegments[0] ? transcriptSegments[0].words.length : 0);
        console.log('Sample word data:', transcriptSegments[0] ? transcriptSegments[0].words.slice(0, 2) : []);
        
        // No merge mode state needed anymore
        
        function formatTime(seconds) {{
            const minutes = Math.floor(seconds / 60);
            const secs = Math.floor(seconds % 60);
            return `${{minutes.toString().padStart(2, '0')}}:${{secs.toString().padStart(2, '0')}}`;
        }}
        
        function initializeVideoGrid() {{
            const groupSelect = document.getElementById('groupSelect');
            const gridSizeSelect = document.getElementById('gridSize');
            
            // Populate group selector
            const groups = new Set();
            document.querySelectorAll('[data-group]').forEach(segment => {{
                const groupId = segment.getAttribute('data-group');
                if (groupId) groups.add(groupId);
            }});
            
            groups.forEach(groupId => {{
                const option = document.createElement('option');
                option.value = groupId;
                option.textContent = `Group ${{groupId}} (${{document.querySelectorAll(`[data-group="${{groupId}}"]`).length}} segments)`;
                groupSelect.appendChild(option);
            }});
            
            // Event listeners
            groupSelect.addEventListener('change', (e) => {{
                if (e.target.value) {{
                    loadGroupToGrid(e.target.value);
                }} else {{
                    clearGrid();
                }}
            }});
            
            gridSizeSelect.addEventListener('change', (e) => {{
                gridSize = parseInt(e.target.value);
                updateGridSize();
                if (currentGroup) {{
                    loadGroupToGrid(currentGroup);
                }}
            }});
            
            document.getElementById('loopClips').addEventListener('change', (e) => {{
                loopClips = e.target.checked;
            }});
        }}
        
        function loadGroupToGrid(groupId) {{
            currentGroup = groupId;
            currentPage = 0;
            
            const segments = document.querySelectorAll(`[data-group="${{groupId}}"]`);
            const segmentData = [];
            
            segments.forEach(segment => {{
                segmentData.push({{
                    id: segment.getAttribute('data-segment-id'),
                    text: segment.textContent,
                    start: parseFloat(segment.getAttribute('data-start')),
                    end: parseFloat(segment.getAttribute('data-end')),
                    element: segment
                }});
            }});
            
            // Sort by start time
            segmentData.sort((a, b) => a.start - b.start);
            
            gridVideos = segmentData;
            renderGridPage();
            updateGridStatus();
        }}
        
        function renderGridPage() {{
            const grid = document.getElementById('videoGrid');
            const videosPerPage = gridSize; // Simplified: 1, 2, or 4 videos
            const startIndex = currentPage * videosPerPage;
            const endIndex = Math.min(startIndex + videosPerPage, gridVideos.length);
            const pageVideos = gridVideos.slice(startIndex, endIndex);
            
            // Clear grid
            grid.innerHTML = '';
            
            if (pageVideos.length === 0) {{
                grid.innerHTML = `
                    <div class="grid-placeholder">
                        <div class="placeholder-icon">🎬</div>
                        <p>No videos in this group</p>
                    </div>
                `;
                return;
            }}
            
            // Create video items
            pageVideos.forEach((videoData, index) => {{
                const videoItem = createVideoItem(videoData, startIndex + index);
                grid.appendChild(videoItem);
            }});
            
            updatePagination();
        }}
        
        function createVideoItem(videoData, index) {{
            const item = document.createElement('div');
            item.className = 'video-item';
            item.innerHTML = `
                <div class="video-header">
                    Segment ${{index + 1}} • ${{formatTime(videoData.start)}} - ${{formatTime(videoData.end)}}
                </div>
                <div class="video-content">
                    <video id="grid-video-${{index}}" 
                           data-start="${{videoData.start}}" 
                           data-end="${{videoData.end}}"
                           controls
                           preload="metadata">
                        <source src="{video_file}" type="video/mp4">
                    </video>
                    <div class="video-overlay">
                        <div class="video-time">${{formatTime(videoData.start)}} - ${{formatTime(videoData.end)}}</div>
                        <div class="video-text">${{videoData.text}}</div>
                    </div>
                </div>
            `;
            
            // Setup video behavior for individual controls
            const video = item.querySelector('video');
            video.addEventListener('loadedmetadata', () => {{
                video.currentTime = videoData.start;
            }});
            
            video.addEventListener('timeupdate', () => {{
                // Respect clip boundaries even with individual controls
                if (video.currentTime >= videoData.end - 0.1) {{
                    if (loopClips) {{
                        video.currentTime = videoData.start;
                    }} else {{
                        video.pause();
                        video.currentTime = videoData.start; // Reset to beginning
                    }}
                }}
                
                // Prevent seeking outside clip boundaries
                if (video.currentTime < videoData.start) {{
                    video.currentTime = videoData.start;
                }}
            }});
            
            video.addEventListener('seeking', () => {{
                // Keep within clip boundaries
                if (video.currentTime < videoData.start) {{
                    video.currentTime = videoData.start;
                }} else if (video.currentTime > videoData.end) {{
                    video.currentTime = videoData.end;
                }}
            }});
            
            video.addEventListener('play', () => {{
                document.querySelectorAll('.video-item').forEach(v => v.classList.remove('active'));
                item.classList.add('active');
            }});
            
            return item;
        }}
        

        
        function updateGridSize() {{
            const grid = document.getElementById('videoGrid');
            grid.className = `video-grid size-${{gridSize}}`;
        }}
        
        function updatePagination() {{
            const videosPerPage = gridSize; // Simplified: 1, 2, or 4 videos
            const totalPages = Math.ceil(gridVideos.length / videosPerPage);
            const pagination = document.getElementById('gridPagination');
            
            if (totalPages <= 1) {{
                pagination.style.display = 'none';
                return;
            }}
            
            pagination.style.display = 'flex';
            document.getElementById('prevPage').disabled = currentPage === 0;
            document.getElementById('nextPage').disabled = currentPage === totalPages - 1;
            document.getElementById('pageInfo').textContent = `Page ${{currentPage + 1}} of ${{totalPages}}`;
        }}
        
        function changeGridPage(direction) {{
            const videosPerPage = gridSize; // Simplified: 1, 2, or 4 videos
            const totalPages = Math.ceil(gridVideos.length / videosPerPage);
            const newPage = currentPage + direction;
            
            if (newPage >= 0 && newPage < totalPages) {{
                currentPage = newPage;
                renderGridPage();
            }}
        }}
        
        function updateGridStatus() {{
            const status = document.getElementById('gridStatus');
            if (currentGroup && gridVideos.length > 0) {{
                status.textContent = `Group ${{currentGroup}}: ${{gridVideos.length}} segments loaded`;
            }} else {{
                status.textContent = 'Select a group to compare segments';
            }}
        }}
        
        function clearGrid() {{
            currentGroup = null;
            gridVideos = [];
            currentPage = 0;
            const grid = document.getElementById('videoGrid');
            grid.innerHTML = `
                <div class="grid-placeholder">
                    <div class="placeholder-icon">🎬</div>
                    <p>Select a duplicate group to view side-by-side comparison</p>
                </div>
            `;
            document.getElementById('gridPagination').style.display = 'none';
            updateGridStatus();
        }}
        

        
        function handleSegmentClick(element, startTime, endTime, segmentId) {{
            if (editMode) {{
                toggleSegmentEdit(element);
            }} else {{
                if (event.shiftKey && selectedSegments.length > 0) {{
                    // Shift+click for multi-selection
                    selectSegment(element, segmentId);
                }} else if (event.ctrlKey || event.metaKey) {{
                    // Ctrl/Cmd+click for toggle selection
                    toggleSegmentSelection(element, segmentId);
                }} else {{
                    // Normal click - load group to grid if segment is in a group
                    const groupId = element.getAttribute('data-group');
                    if (groupId) {{
                        document.getElementById('groupSelect').value = groupId;
                        loadGroupToGrid(groupId);
                        
                        // Scroll to video grid
                        document.getElementById('videoGrid').scrollIntoView({{ behavior: 'smooth' }});
                    }}
                }}
            }}
        }}
        
        function toggleEditMode() {{
            editMode = !editMode;
            const button = document.querySelector('.toggle-edit-mode');
            const saveButton = document.getElementById('saveButton');
            const editIndicator = document.getElementById('editIndicator');
            
            button.textContent = editMode ? '🔒 Lock Editing' : '✏️ Toggle Edit Mode';
            
            if (editMode) {{
                saveButton.style.display = 'inline-block';
                editIndicator.classList.add('show');
            }} else {{
                saveButton.style.display = 'none';
                editIndicator.classList.remove('show');
            }}
            
            // Make all segments editable/non-editable
            document.querySelectorAll('.transcript-segment').forEach(segment => {{
                segment.contentEditable = editMode;
                if (editMode) {{
                    segment.style.backgroundColor = 'rgba(66, 153, 225, 0.05)';
                    segment.addEventListener('input', handleSegmentEdit);
                }} else {{
                    segment.style.backgroundColor = '';
                    segment.removeEventListener('input', handleSegmentEdit);
                }}
            }});
            
            updateWordCount();
        }}
        
        function handleSegmentEdit(event) {{
            updateWordCount();
            // Auto-save to browser storage every 2 seconds of inactivity
            clearTimeout(window.autoSaveTimer);
            window.autoSaveTimer = setTimeout(() => {{
                autoSaveToStorage();
            }}, 2000);
        }}
        
        function updateWordCount() {{
            const segments = document.querySelectorAll('.transcript-segment');
            let wordCount = 0;
            segments.forEach(segment => {{
                wordCount += segment.textContent.trim().split(/\\s+/).length;
            }});
            document.getElementById('wordCount').textContent = `${{wordCount}} words`;
        }}
        
        function autoSaveToStorage() {{
            const transcriptData = getTranscriptData();
            localStorage.setItem('transcriptDraft', JSON.stringify(transcriptData));
            console.log('Auto-saved to browser storage');
        }}
        
        function getTranscriptData() {{
            const segments = [];
            document.querySelectorAll('.transcript-segment').forEach(segment => {{
                segments.push({{
                    segment_id: segment.getAttribute('data-segment-id') || '',
                    text: segment.textContent,
                    start: parseFloat(segment.getAttribute('data-start')),
                    end: parseFloat(segment.getAttribute('data-end')),
                    group: segment.getAttribute('data-group') || null
                }});
            }});
            return {{
                segments: segments,
                total_segments: segments.length,
                last_edited: new Date().toISOString()
            }};
        }}
        
        function saveTranscript() {{
            try {{
                const transcriptData = getTranscriptData();
                const jsonData = JSON.stringify(transcriptData, null, 2);
                const blob = new Blob([jsonData], {{ type: 'application/json' }});
                const url = URL.createObjectURL(blob);
                
                const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
                const filename = `edited_transcript_${{timestamp}}.json`;
                
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
                
                // Show success message
                showSaveStatus('Transcript saved successfully!', 'success');
                
                // Clear browser storage
                localStorage.removeItem('transcriptDraft');
                
            }} catch (error) {{
                showSaveStatus('Error saving transcript: ' + error.message, 'error');
            }}
        }}
        
        function downloadTranscript() {{
            const transcriptData = getTranscriptData();
            
            // Create different format options
            const format = prompt('Choose format:\\n1. JSON (with timestamps)\\n2. Plain text\\n3. SRT subtitles\\nEnter choice (1-3):', '1');
            
            let content, filename, mimeType;
            
            switch(format) {{
                case '2':
                    // Plain text
                    content = transcriptData.segments.map(seg => seg.text).join(' ');
                    filename = `transcript_text_${{new Date().toISOString().slice(0, 10)}}.txt`;
                    mimeType = 'text/plain';
                    break;
                    
                case '3':
                    // SRT format
                    content = generateSRT(transcriptData.segments);
                    filename = `transcript_${{new Date().toISOString().slice(0, 10)}}.srt`;
                    mimeType = 'text/plain';
                    break;
                    
                default:
                    // JSON format
                    content = JSON.stringify(transcriptData, null, 2);
                    filename = `transcript_${{new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)}}.json`;
                    mimeType = 'application/json';
            }}
            
            const blob = new Blob([content], {{ type: mimeType }});
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            showSaveStatus(`Downloaded ${{filename}}`, 'success');
        }}
        
        function generateSRT(segments) {{
            return segments.map((seg, index) => {{
                const startTime = formatSRTTime(seg.start);
                const endTime = formatSRTTime(seg.end);
                return `${{index + 1}}\\n${{startTime}} --> ${{endTime}}\\n${{seg.text}}\\n`;
            }}).join('\\n');
        }}
        
        function formatSRTTime(seconds) {{
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            const secs = Math.floor(seconds % 60);
            const ms = Math.floor((seconds % 1) * 1000);
            return `${{hours.toString().padStart(2, '0')}}:${{minutes.toString().padStart(2, '0')}}:${{secs.toString().padStart(2, '0')}},${{ms.toString().padStart(3, '0')}}`;
        }}
        
        function showSaveStatus(message, type) {{
            const statusElement = document.getElementById('saveStatus');
            statusElement.textContent = message;
            statusElement.className = `save-status ${{type}}`;
            
            setTimeout(() => {{
                statusElement.className = 'save-status';
            }}, 3000);
        }}
        
        function loadDraftFromStorage() {{
            try {{
                const draft = localStorage.getItem('transcriptDraft');
                if (draft) {{
                    const transcriptData = JSON.parse(draft);
                    const lastEdited = new Date(transcriptData.last_edited);
                    const timeDiff = Date.now() - lastEdited.getTime();
                    const hoursDiff = timeDiff / (1000 * 60 * 60);
                    
                    if (hoursDiff < 24 && confirm(`Found unsaved draft from ${{lastEdited.toLocaleString()}}. Load it?`)) {{
                        // Apply draft changes
                        transcriptData.segments.forEach(draftSeg => {{
                            const segment = document.querySelector(`[data-segment-id="${{draftSeg.segment_id}}"]`);
                            if (segment) {{
                                segment.textContent = draftSeg.text;
                            }}
                        }});
                        showSaveStatus('Draft loaded successfully', 'success');
                    }}
                }}
            }} catch (error) {{
                console.error('Error loading draft:', error);
            }}
        }}
        
        function toggleSegmentEdit(element) {{
            if (element.contentEditable === 'true') {{
                element.contentEditable = 'false';
                element.style.backgroundColor = '';
                // Save changes here if needed
                console.log('Saved:', element.textContent);
            }} else {{
                element.contentEditable = 'true';
                element.style.backgroundColor = 'white';
                element.focus();
                
                // Select all text
                const range = document.createRange();
                range.selectNodeContents(element);
                const selection = window.getSelection();
                selection.removeAllRanges();
                selection.addRange(range);
            }}
        }}
        
        function selectSegment(element, segmentId) {{
            if (!selectedSegments.find(s => s.id === segmentId)) {{
                selectedSegments.push({{element, id: segmentId}});
                element.style.outline = '2px solid #4299e1';
                element.style.outlineOffset = '2px';
            }}
        }}
        
        function toggleSegmentSelection(element, segmentId) {{
            const index = selectedSegments.findIndex(s => s.id === segmentId);
            if (index > -1) {{
                selectedSegments.splice(index, 1);
                element.style.outline = '';
                element.style.outlineOffset = '';
            }} else {{
                selectSegment(element, segmentId);
            }}
        }}
        
        function createNewGroup() {{
            if (selectedSegments.length < 2) {{
                alert('Please select at least 2 segments to create a group. Use Ctrl+click to select multiple segments.');
                return;
            }}
            
            const groupNum = groupCounter++;
            const groupColor = getGroupColor(groupNum);
            
            selectedSegments.forEach(({{element}}) => {{
                element.classList.add('duplicate-highlight', `duplicate-group-${{groupNum}}`);
                element.setAttribute('data-group', groupNum);
                element.style.outline = '';
                element.style.outlineOffset = '';
            }});
            
            // Clear selection
            selectedSegments = [];
            
            alert(`Created duplicate group ${{groupNum}} with ${{selectedSegments.length}} segments.`);
        }}
        
        function getGroupColor(groupNum) {{
            const colors = [
                {{bg: '#fed7d7', hover: '#fc8181', border: '#f56565'}},
                {{bg: '#feebc8', hover: '#f6ad55', border: '#ed8936'}},
                {{bg: '#b2f5ea', hover: '#4fd1c5', border: '#38b2ac'}},
                {{bg: '#e9d8fd', hover: '#b794f4', border: '#805ad5'}},
                {{bg: '#faf089', hover: '#f6e05e', border: '#d69e2e'}}
            ];
            return colors[(groupNum - 1) % colors.length];
        }}
        
        function removeFromGroup(element) {{
            const groupNum = element.getAttribute('data-group');
            if (groupNum) {{
                element.classList.remove('duplicate-highlight', `duplicate-group-${{groupNum}}`);
                element.removeAttribute('data-group');
            }}
        }}
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {{
            if (e.key === ' ' && e.target.tagName !== 'INPUT' && e.target.contentEditable !== 'true') {{
                e.preventDefault();
                const video = document.getElementById('videoPlayer');
                if (video.paused) {{
                    video.play();
                }} else {{
                    video.pause();
                }}
            }}
            
            if (e.key === 'Escape') {{
                // Clear selections
                selectedSegments.forEach(({{element}}) => {{
                    element.style.outline = '';
                    element.style.outlineOffset = '';
                }});
                selectedSegments = [];
            }}
            
            if (e.key === 'Delete' && selectedSegments.length > 0) {{
                // Remove selected segments from their groups
                selectedSegments.forEach(({{element}}) => {{
                    removeFromGroup(element);
                }});
                selectedSegments = [];
            }}
        }});
        
        // Add right-click context menu for segments
        document.addEventListener('contextmenu', (e) => {{
            if (e.target.classList.contains('transcript-segment')) {{
                e.preventDefault();
                // Could add context menu here
                console.log('Right-click on segment:', e.target.textContent);
            }}
        }});
        
        // Initialize editor and playback mode listeners
        document.addEventListener('DOMContentLoaded', () => {{
            // Load any unsaved draft
            loadDraftFromStorage();
            
            // Initialize word count
            updateWordCount();
            
            // Initialize video grid
            initializeVideoGrid();
            
            // Populate group selector
            const groups = new Set();
            document.querySelectorAll('[data-group]').forEach(segment => {{
                const groupId = segment.getAttribute('data-group');
                if (groupId) groups.add(groupId);
            }});
            
            groups.forEach(groupId => {{
                const option = document.createElement('option');
                option.value = groupId;
                option.textContent = `Group ${{groupId}}`;
                groupSelect.appendChild(option);
            }});
            
            // Handle playback mode changes
            playbackModes.forEach(radio => {{
                radio.addEventListener('change', (e) => {{
                    if (e.target.value === 'group') {{
                        groupSelector.style.display = 'flex';
                    }} else {{
                        groupSelector.style.display = 'none';
                        clipQueue = [];
                        currentClipIndex = 0;
                        isPlayingQueue = false;
                        updatePlaylistDisplay();
                    }}
                }});
            }});
            
            // Handle group selection
            groupSelect.addEventListener('change', (e) => {{
                if (e.target.value) {{
                    playGroupClips(e.target.value);
                }}
            }});
            
            // Initialize playlist display
            updatePlaylistDisplay();
        }});
        
        // Group Management Functions
        
        function openSegmentGroupMenu(segmentId, event) {{
            event.stopPropagation();
            
            // Create or get the group menu
            let menu = document.getElementById('segmentGroupMenu');
            if (!menu) {{
                menu = document.createElement('div');
                menu.id = 'segmentGroupMenu';
                menu.className = 'segment-group-menu';
                document.body.appendChild(menu);
            }}
            
            // Get current groups
            const currentGroups = new Set();
            document.querySelectorAll('.transcript-segment[data-group]').forEach(seg => {{
                currentGroups.add(seg.getAttribute('data-group'));
            }});
            
            // Get current segment's group
            const segment = document.querySelector(`[data-segment-id="${{segmentId}}"]`);
            const currentGroup = segment ? segment.getAttribute('data-group') : null;
            
            // Build menu HTML
            let menuHTML = `
                <div class="group-menu-header">Assign to Group:</div>
                <div class="group-menu-item" onclick="assignSegmentToGroup('${{segmentId}}', null)">
                    🚫 Remove from Group
                </div>
                <div class="group-menu-divider"></div>
                <div class="group-menu-item" onclick="createNewGroupForSegment('${{segmentId}}')">
                    ➕ Create New Group
                </div>
                <div class="group-menu-divider"></div>
            `;
            
            // Add existing groups
            Array.from(currentGroups).sort((a, b) => parseInt(a) - parseInt(b)).forEach(groupId => {{
                const isSelected = currentGroup === groupId;
                menuHTML += `
                    <div class="group-menu-item ${{isSelected ? 'selected' : ''}}" 
                         onclick="assignSegmentToGroup('${{segmentId}}', '${{groupId}}')">
                        📁 Group ${{groupId}} ${{isSelected ? '✓' : ''}}
                    </div>
                `;
            }});
            
            menu.innerHTML = menuHTML;
            
            // Position menu
            const rect = event.target.getBoundingClientRect();
            menu.style.left = rect.left + 'px';
            menu.style.top = (rect.bottom + 5) + 'px';
            
            // Show menu
            menu.style.display = 'block';
            
            // Hide menu when clicking elsewhere
            setTimeout(() => {{
                document.addEventListener('click', hideSegmentGroupMenu, {{ once: true }});
            }}, 100);
        }}
        
        function hideSegmentGroupMenu() {{
            const menu = document.getElementById('segmentGroupMenu');
            if (menu) {{
                menu.style.display = 'none';
            }}
        }}
        
        function assignSegmentToGroup(segmentId, groupId) {{
            const segment = document.querySelector(`[data-segment-id="${{segmentId}}"]`);
            if (!segment) return;
            
            // Remove existing group classes
            segment.className = segment.className.replace(/duplicate-group-\d+/g, '').replace(/duplicate-highlight/g, '').trim();
            
            if (groupId) {{
                // Assign to group
                segment.setAttribute('data-group', groupId);
                segment.classList.add('duplicate-highlight', `duplicate-group-${{groupId}}`);
            }} else {{
                // Remove from group
                segment.removeAttribute('data-group');
            }}
            
            // Update video grid if needed
            updateVideoGridOptions();
            
            // Auto-save
            autoSaveToStorage();
            
            hideSegmentGroupMenu();
        }}
        
        function createNewGroupForSegment(segmentId) {{
            const newGroupId = prompt('Enter new group number (or leave empty for auto-assignment):');
            if (newGroupId === null) return; // User cancelled
            
            let groupId = newGroupId.trim();
            if (!groupId) {{
                // Auto-assign next available group number
                const existingGroups = new Set();
                document.querySelectorAll('.transcript-segment[data-group]').forEach(seg => {{
                    existingGroups.add(parseInt(seg.getAttribute('data-group')));
                }});
                
                groupId = '1';
                while (existingGroups.has(parseInt(groupId))) {{
                    groupId = (parseInt(groupId) + 1).toString();
                }}
            }}
            
            assignSegmentToGroup(segmentId, groupId);
        }}
        
        function openGroupEditor() {{
            // Get all segments grouped by group
            const groups = {{}};
            document.querySelectorAll('.transcript-segment[data-group]').forEach(seg => {{
                const groupId = seg.getAttribute('data-group');
                if (!groups[groupId]) groups[groupId] = [];
                groups[groupId].push(seg);
            }});
            
            // Build editor HTML
            let editorHTML = `
                <div class="group-editor-overlay">
                    <div class="group-editor">
                        <div class="group-editor-header">
                            <h3>📝 Group Editor</h3>
                            <button class="close-btn" onclick="closeGroupEditor()">✕</button>
                        </div>
                        <div class="group-editor-content">
            `;
            
            if (Object.keys(groups).length === 0) {{
                editorHTML += `
                    <div class="no-groups-message">
                        <p>No groups found. Use the 📋 button on transcript lines to create groups.</p>
                    </div>
                `;
            }} else {{
                Object.keys(groups).sort((a, b) => parseInt(a) - parseInt(b)).forEach(groupId => {{
                    editorHTML += `
                        <div class="group-editor-group" data-group="${{groupId}}">
                            <div class="group-editor-group-header">
                                <h4>📁 Group ${{groupId}} (${{groups[groupId].length}} segments)</h4>
                                <div class="group-actions">
                                    <button class="group-action-btn" onclick="renameGroup('${{groupId}}')">✏️ Rename</button>
                                    <button class="group-action-btn delete" onclick="deleteGroup('${{groupId}}')">🗑️ Delete</button>
                                    <button class="group-action-btn" onclick="loadGroupToGrid('${{groupId}}')">🎬 View in Grid</button>
                                </div>
                            </div>
                            <div class="group-segments">
                    `;
                    
                    groups[groupId].forEach((seg, index) => {{
                        const segmentId = seg.getAttribute('data-segment-id');
                        const startTime = seg.getAttribute('data-start');
                        const endTime = seg.getAttribute('data-end');
                        const text = seg.textContent.trim();
                        
                        editorHTML += `
                            <div class="group-segment-item" data-segment-id="${{segmentId}}">
                                <div class="segment-info">
                                    <span class="segment-index">${{index + 1}}.</span>
                                    <span class="segment-time">⏰ ${{formatTime(startTime)}} - ${{formatTime(endTime)}}</span>
                                    <button class="segment-play-small" onclick="playSegment(${{startTime}}, ${{endTime}})">▶️</button>
                                </div>
                                <div class="segment-text">${{text}}</div>
                                <button class="remove-segment-btn" onclick="removeSegmentFromGroup('${{segmentId}}', '${{groupId}}')">✕</button>
                            </div>
                        `;
                    }});
                    
                    editorHTML += `
                            </div>
                        </div>
                    `;
                }});
            }}
            
            editorHTML += `
                        </div>
                    </div>
                </div>
            `;
            
            // Create and show editor
            const editorOverlay = document.createElement('div');
            editorOverlay.innerHTML = editorHTML;
            document.body.appendChild(editorOverlay.firstElementChild);
        }}
        
        function closeGroupEditor() {{
            const editor = document.querySelector('.group-editor-overlay');
            if (editor) {{
                editor.remove();
            }}
        }}
        
        function renameGroup(oldGroupId) {{
            const newGroupId = prompt(`Enter new group number for Group ${{oldGroupId}}:`, oldGroupId);
            if (newGroupId && newGroupId !== oldGroupId) {{
                // Update all segments in this group
                document.querySelectorAll(`[data-group="${{oldGroupId}}"]`).forEach(seg => {{
                    seg.setAttribute('data-group', newGroupId);
                    seg.className = seg.className.replace(/duplicate-group-\d+/g, '').replace(/duplicate-highlight/g, '').trim();
                    seg.classList.add('duplicate-highlight', `duplicate-group-${{newGroupId}}`);
                }});
                
                updateVideoGridOptions();
                autoSaveToStorage();
                openGroupEditor(); // Refresh the editor
            }}
        }}
        
        function deleteGroup(groupId) {{
            if (confirm(`Are you sure you want to delete Group ${{groupId}}? This will remove all segments from the group.`)) {{
                document.querySelectorAll(`[data-group="${{groupId}}"]`).forEach(seg => {{
                    seg.removeAttribute('data-group');
                    seg.className = seg.className.replace(/duplicate-group-\d+/g, '').replace(/duplicate-highlight/g, '').trim();
                }});
                
                updateVideoGridOptions();
                autoSaveToStorage();
                openGroupEditor(); // Refresh the editor
            }}
        }}
        
        function removeSegmentFromGroup(segmentId, groupId) {{
            if (confirm(`Remove this segment from Group ${{groupId}}?`)) {{
                assignSegmentToGroup(segmentId, null);
                openGroupEditor(); // Refresh the editor
            }}
        }}
        
        function updateVideoGridOptions() {{
            // Update the group selector in video grid
            const groupSelect = document.getElementById('groupSelect');
            if (!groupSelect) return;
            
            const currentValue = groupSelect.value;
            groupSelect.innerHTML = '<option value="">Choose a group...</option>';
            
            const groups = new Set();
            document.querySelectorAll('.transcript-segment[data-group]').forEach(seg => {{
                groups.add(seg.getAttribute('data-group'));
            }});
            
            Array.from(groups).sort((a, b) => parseInt(a) - parseInt(b)).forEach(groupId => {{
                const option = document.createElement('option');
                option.value = groupId;
                option.textContent = `Group ${{groupId}}`;
                groupSelect.appendChild(option);
            }});
            
            // Restore previous selection if it still exists
            if (currentValue && groups.has(currentValue)) {{
                groupSelect.value = currentValue;
            }}
        }}
        
        // Playback Functions
        
        function playSegment(startTime, endTime) {{
            // Create a temporary video element if it doesn't exist
            let video = document.getElementById('tempVideoPlayer');
            if (!video) {{
                video = document.createElement('video');
                video.id = 'tempVideoPlayer';
                video.style.display = 'none';
                video.src = "{video_file}";
                document.body.appendChild(video);
            }}
            
            // Set video time and play
            video.currentTime = startTime;
            video.play();
            
            // Stop at end time
            const checkTime = () => {{
                if (video.currentTime >= endTime) {{
                    video.pause();
                    video.currentTime = startTime;
                }} else {{
                    requestAnimationFrame(checkTime);
                }}
            }};
            requestAnimationFrame(checkTime);
        }}
        
        // Playback Functions
        
        function playSegment(startTime, endTime) {{
            // Create a temporary video element if it doesn't exist
            let video = document.getElementById('tempVideoPlayer');
            if (!video) {{
                video = document.createElement('video');
                video.id = 'tempVideoPlayer';
                video.style.display = 'none';
                video.src = "{video_file}";
                document.body.appendChild(video);
            }}
            
            // Set video time and play
            video.currentTime = startTime;
            video.play();
            
            // Stop at end time
            const checkTime = () => {{
                if (video.currentTime >= endTime) {{
                    video.pause();
                    video.currentTime = startTime;
                }} else {{
                    requestAnimationFrame(checkTime);
                }}
            }};
            requestAnimationFrame(checkTime);
        }}
        
        // Split/Merge Functions
        
        function enableInlineEdit(segmentId, event) {{
            event.stopPropagation();
            
            const segmentElement = document.querySelector(`[data-segment-id="${{segmentId}}"] .transcript-segment`);
            if (!segmentElement) return;
            
            // Check if already editing
            if (segmentElement.contentEditable === 'true') {{
                // Finish editing
                finishInlineEdit(segmentId);
                return;
            }}
            
            // Store original content
            segmentElement.setAttribute('data-original-text', segmentElement.textContent);
            
            // Enable inline editing
            segmentElement.contentEditable = 'true';
            segmentElement.style.background = 'white';
            segmentElement.style.border = '2px solid #4299e1';
            segmentElement.style.padding = '4px 8px';
            segmentElement.style.borderRadius = '4px';
            segmentElement.style.outline = 'none';
            segmentElement.focus();
            
            // Select all text for easy editing
            const range = document.createRange();
            range.selectNodeContents(segmentElement);
            const selection = window.getSelection();
            selection.removeAllRanges();
            selection.addRange(range);
            
            // Add edit event listeners
            segmentElement.addEventListener('blur', () => finishInlineEdit(segmentId));
            segmentElement.addEventListener('keydown', (e) => {{
                if (e.key === 'Enter') {{
                    e.preventDefault();
                    // Check if cursor is in the middle (for splitting) or at end (for saving)
                    const selection = window.getSelection();
                    if (selection.rangeCount > 0) {{
                        const range = selection.getRangeAt(0);
                        const text = segmentElement.textContent;
                        const cursorPosition = range.startOffset;
                        
                        // If cursor is not at the end, split the segment
                        if (cursorPosition < text.length) {{
                            splitSegmentAtCursorPosition(segmentId, cursorPosition);
                        }} else {{
                            // At the end, just save the edit
                            finishInlineEdit(segmentId);
                        }}
                    }}
                }} else if (e.key === 'Escape') {{
                    cancelInlineEdit(segmentId);
                }}
            }});
        }}
        
        function finishInlineEdit(segmentId) {{
            const segmentElement = document.querySelector(`[data-segment-id="${{segmentId}}"] .transcript-segment`);
            if (!segmentElement || segmentElement.contentEditable !== 'true') return;
            
            const newText = segmentElement.textContent.trim();
            const originalText = segmentElement.getAttribute('data-original-text');
            
            if (newText !== originalText) {{
                // Update the segment with new text and redistribute timings
                updateSegmentWithNewText(segmentId, newText);
            }}
            
            // Reset editing state
            segmentElement.contentEditable = 'false';
            segmentElement.style.background = '';
            segmentElement.style.border = '';
            segmentElement.style.padding = '';
            segmentElement.removeAttribute('data-original-text');
            
            // Reset button
            const line = segmentElement.closest('.transcript-line');
            const splitBtn = line.querySelector('.segment-split-btn');
            if (splitBtn) {{
                splitBtn.textContent = '✂️';
                splitBtn.setAttribute('title', 'Edit text');
                splitBtn.onclick = (e) => enableInlineEdit(segmentId, e);
            }}
            
            // Auto-save
            autoSaveToStorage();
        }}
        
        function cancelInlineEdit(segmentId) {{
            const segmentElement = document.querySelector(`[data-segment-id="${{segmentId}}"] .transcript-segment`);
            if (!segmentElement) return;
            
            // Restore original text
            const originalText = segmentElement.getAttribute('data-original-text');
            if (originalText) {{
                segmentElement.textContent = originalText;
            }}
            
            finishInlineEdit(segmentId);
        }}
        
        function updateSegmentWithNewText(segmentId, newText) {{
            const segment = transcriptSegments.find(seg => seg.segment_id === segmentId);
            if (!segment) return;
            
            // Split new text into words
            const newWords = newText.trim().split(/\\s+/).filter(word => word.length > 0);
            
            if (newWords.length === 0) return;
            
            // Redistribute timing across new words
            const totalDuration = segment.end - segment.start;
            const wordDuration = totalDuration / newWords.length;
            
            const updatedWords = newWords.map((word, index) => ({{
                text: word,
                start: segment.start + (index * wordDuration),
                end: segment.start + ((index + 1) * wordDuration)
            }}));
            
            // Update segment data
            segment.text = newText;
            segment.words = updatedWords;
            
            // Update display
            segmentElement.textContent = newText;
            
            console.log('Updated segment:', segment);
        }}
        
        function splitSegmentAtCursorPosition(segmentId, cursorPosition) {{
            const segment = transcriptSegments.find(seg => seg.segment_id === segmentId);
            if (!segment) return;
            
            const text = segment.text;
            const beforeText = text.substring(0, cursorPosition).trim();
            const afterText = text.substring(cursorPosition).trim();
            
            if (!beforeText || !afterText) {{
                // Nothing to split, just save the edit
                finishInlineEdit(segmentId);
                return;
            }}
            
            // Calculate split timing based on character position
            const totalDuration = segment.end - segment.start;
            const splitRatio = cursorPosition / text.length;
            const splitTime = segment.start + (totalDuration * splitRatio);
            
            // Create two new segments
            const part1Segment = {{
                segment_id: `${{segmentId}}_part1_${{Date.now()}}`,
                text: beforeText,
                start: segment.start,
                end: splitTime,
                words: segment.words ? segment.words.filter(w => w.end <= splitTime) : []
            }};
            
            const part2Segment = {{
                segment_id: `${{segmentId}}_part2_${{Date.now()}}`,
                text: afterText,
                start: splitTime,
                end: segment.end,
                words: segment.words ? segment.words.filter(w => w.start >= splitTime) : []
            }};
            
            // Update transcript data
            const segmentIndex = transcriptSegments.findIndex(seg => seg.segment_id === segmentId);
            transcriptSegments.splice(segmentIndex, 1, part1Segment, part2Segment);
            
            // Update UI
            updateTranscriptDisplay();
            
            // Auto-save
            autoSaveToStorage();
        }}
        
        function mergeWithPrevious(segmentId, event) {{
            event.stopPropagation();
            
            const segmentIndex = transcriptSegments.findIndex(seg => seg.segment_id === segmentId);
            if (segmentIndex <= 0) {{
                alert('No previous segment to merge with.');
                return;
            }}
            
            const previousSegment = transcriptSegments[segmentIndex - 1];
            const currentSegment = transcriptSegments[segmentIndex];
            
            if (confirm(`Merge "${{previousSegment.text}}" with "${{currentSegment.text}}"?`)) {{
                const mergedSegment = mergeSegments([previousSegment, currentSegment]);
                
                // Replace both segments with merged one
                transcriptSegments.splice(segmentIndex - 1, 2, mergedSegment);
                
                // Update UI
                updateTranscriptDisplay();
                
                // Auto-save
                autoSaveToStorage();
            }}
        }}
        
        function mergeWithNext(segmentId, event) {{
            event.stopPropagation();
            
            const segmentIndex = transcriptSegments.findIndex(seg => seg.segment_id === segmentId);
            if (segmentIndex >= transcriptSegments.length - 1) {{
                alert('No next segment to merge with.');
                return;
            }}
            
            const currentSegment = transcriptSegments[segmentIndex];
            const nextSegment = transcriptSegments[segmentIndex + 1];
            
            if (confirm(`Merge "${{currentSegment.text}}" with "${{nextSegment.text}}"?`)) {{
                const mergedSegment = mergeSegments([currentSegment, nextSegment]);
                
                // Replace both segments with merged one
                transcriptSegments.splice(segmentIndex, 2, mergedSegment);
                
                // Update UI
                updateTranscriptDisplay();
                
                // Auto-save
                autoSaveToStorage();
            }}
        }}
        
        // Old merge mode functions removed - now using specific merge buttons
        
        function mergeSegments(segments) {{
            const allWords = segments.flatMap(seg => seg.words || []);
            const mergedText = segments.map(seg => seg.text).join(' ');
            
            return {{
                segment_id: `merged_${{Date.now()}}`,
                text: mergedText,
                start: segments[0].start,
                end: segments[segments.length - 1].end,
                words: allWords
            }};
        }}
        
        function updateTranscriptDisplay() {{
            // Dynamically update the transcript display without page reload
            const transcriptContainer = document.querySelector('.transcript-paragraph');
            if (!transcriptContainer) return;
            
            transcriptContainer.innerHTML = '';
            
            transcriptSegments.forEach((segment, index) => {{
                const segmentHtml = `
                    <div class="transcript-line" data-segment-id="${{segment.segment_id}}">
                        <div class="segment-controls">
                            <button class="segment-group-btn" onclick="openSegmentGroupMenu('${{segment.segment_id}}', event)" title="Assign to group">📋</button>
                            <button class="segment-play-btn" onclick="playSegment(${{segment.start}}, ${{segment.end}})" title="Play segment">▶️</button>
                            <button class="segment-edit-btn" onclick="enableInlineEdit('${{segment.segment_id}}', event)" title="Edit text">✏️</button>
                            <button class="segment-merge-previous-btn" onclick="mergeWithPrevious('${{segment.segment_id}}', event)" title="Merge with previous">⬅️</button>
                            <button class="segment-merge-next-btn" onclick="mergeWithNext('${{segment.segment_id}}', event)" title="Merge with next">➡️</button>
                        </div>
                        <span class="transcript-segment" 
                              data-start="${{segment.start}}" 
                              data-end="${{segment.end}}"
                              data-segment-id="${{segment.segment_id}}"
                              data-words-count="${{segment.words ? segment.words.length : 0}}"
                              title="${{formatTime(segment.start)}} - ${{formatTime(segment.end)}}. Press Enter in the middle of text to split, or at end to save."
                              onclick="handleSegmentClick(this, ${{segment.start}}, ${{segment.end}}, '${{segment.segment_id}}')"
                              contenteditable="false">${{segment.text}}</span>
                        <div class="segment-timestamp">${{formatTime(segment.start)}}</div>
                    </div>
                `;
                transcriptContainer.insertAdjacentHTML('beforeend', segmentHtml);
            }});
            
            // Update video grid options
            updateVideoGridOptions();
        }}
    </script>
</body>
</html>'''
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)


def main():
    """CLI entry point for duplicate detection."""
    parser = argparse.ArgumentParser(
        description="Detect and edit duplicates in video transcripts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic duplicate detection
  duplicate-detection transcript.json video.mp4
  
  # Custom threshold and simple mode
  duplicate-detection transcript.json video.mp4 --threshold 0.6 --no-ai
  
  # Generate interactive report
  duplicate-detection transcript.json video.mp4 --report report.html
        """
    )
    
    parser.add_argument("transcript_file", help="Path to transcript JSON file")
    parser.add_argument("video_file", help="Path to the corresponding video file")
    parser.add_argument("--output", "-o", help="Path to save detection results as JSON")
    parser.add_argument("--report", "-r", help="Path to save interactive HTML report")
    parser.add_argument("--model", default="llama3.1:8b", help="Ollama model to use for analysis")
    parser.add_argument("--threshold", type=float, default=0.75, help="Similarity threshold (0.0-1.0)")
    parser.add_argument("--no-ai", action="store_true", help="Use simple text similarity instead of AI")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    
    args = parser.parse_args()
    
    logging.basicConfig(level=getattr(logging, args.log_level))
    
    try:
        # Initialize detector
        detector = DuplicateDetector(model=args.model, use_ai=not args.no_ai)
        
        # Detect duplicates
        result = detector.detect_duplicates(Path(args.transcript_file), args.threshold)
        
        # Load transcript segments for report
        with open(args.transcript_file, 'r', encoding='utf-8') as f:
            transcript_data = json.load(f)
        
        segments = []
        if 'segments' in transcript_data:
            for i, seg in enumerate(transcript_data['segments']):
                segments.append(TranscriptSegment(
                    text=seg['text'],
                    start_time=seg['start'],
                    end_time=seg['end'],
                    segment_id=seg.get('id', f'seg_{i}')
                ))
        
        # Save results if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(asdict(result), f, indent=2)
        
        # Generate report if requested
        if args.report:
            report_generator = DuplicateReportGenerator()
            report_generator.generate_report(result, args.video_file, Path(args.report), segments)
        
        # Print summary
        print(f"✅ Duplicate detection complete!")
        print(f"📊 Total segments: {result.total_segments}")
        print(f"🔄 Duplicate groups: {len(result.duplicate_groups)}")
        print(f"⏱️ Processing time: {result.processing_time:.1f}s")
        print(f"🤖 Model: {result.model_used}")
        
        if args.report:
            print(f"🌐 Interactive report: {args.report}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())