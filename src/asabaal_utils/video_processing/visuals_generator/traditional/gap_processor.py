from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import json

from srt_parser import (
    Subtitle, Gap, parse_time_range, parse_user_time, 
    get_narrative_context, format_time
)
from biblical_themes import (
    identify_themes, get_visual_elements, get_animation_style,
    enhance_prompt_with_biblical_style
)


@dataclass
class VisualConcept:
    gap: Gap
    themes: List[str]
    visual_elements: Dict[str, List[str]]
    concept_description: str
    text_to_image_prompt: str
    image_to_video_prompt: str
    animation_style: str
    extension_strategy: Dict


class GapProcessor:
    def __init__(self, midjourney_duration: float = 5.07):
        self.midjourney_duration = midjourney_duration
    
    def process_gaps_mode(self, gap_times: List[str], subtitles: List[Subtitle], 
                         total_duration: float) -> List[VisualConcept]:
        """Process user-provided gap times."""
        visual_concepts = []
        
        for gap_time in gap_times:
            start, end = parse_time_range(gap_time)
            duration = end - start
            
            narrative_context, surrounding = get_narrative_context(subtitles, start, end)
            
            gap = Gap(
                start_time=start,
                end_time=end,
                duration=duration,
                narrative_context=narrative_context,
                surrounding_subtitles=surrounding
            )
            
            concept = self._create_visual_concept(gap)
            visual_concepts.append(concept)
        
        return visual_concepts
    
    def process_existing_visuals_mode(self, existing_times: List[str], 
                                    subtitles: List[Subtitle], 
                                    total_duration: float) -> List[VisualConcept]:
        """Calculate gaps from existing visual locations."""
        # Parse existing visual ranges
        existing_ranges = []
        for time_range in existing_times:
            start, end = parse_time_range(time_range)
            existing_ranges.append((start, end))
        
        # Sort by start time
        existing_ranges.sort(key=lambda x: x[0])
        
        # Find gaps
        gaps = []
        
        # Check for gap at beginning
        if existing_ranges[0][0] > 0:
            gaps.append((0, existing_ranges[0][0]))
        
        # Check for gaps between existing visuals
        for i in range(len(existing_ranges) - 1):
            gap_start = existing_ranges[i][1]
            gap_end = existing_ranges[i + 1][0]
            
            if gap_end > gap_start:  # There's a gap
                gaps.append((gap_start, gap_end))
        
        # Check for gap at end
        if existing_ranges[-1][1] < total_duration:
            gaps.append((existing_ranges[-1][1], total_duration))
        
        # Filter out tiny gaps (< 2 seconds)
        meaningful_gaps = [(start, end) for start, end in gaps if end - start >= 2.0]
        
        # Create visual concepts for gaps
        visual_concepts = []
        for start, end in meaningful_gaps:
            duration = end - start
            narrative_context, surrounding = get_narrative_context(subtitles, start, end)
            
            gap = Gap(
                start_time=start,
                end_time=end,
                duration=duration,
                narrative_context=narrative_context,
                surrounding_subtitles=surrounding
            )
            
            concept = self._create_visual_concept(gap)
            visual_concepts.append(concept)
        
        return visual_concepts
    
    def process_full_take_mode(self, subtitles: List[Subtitle], 
                             total_duration: float, 
                             segment_length: float = 15.0) -> List[VisualConcept]:
        """Segment entire video into visual concepts."""
        visual_concepts = []
        
        # Intelligent segmentation based on narrative flow
        segments = self._create_narrative_segments(subtitles, segment_length)
        
        for segment_start, segment_end, segment_subs in segments:
            duration = segment_end - segment_start
            
            # Build narrative context from segment subtitles
            narrative_text = ' '.join([s.text for s in segment_subs])
            
            gap = Gap(
                start_time=segment_start,
                end_time=segment_end,
                duration=duration,
                narrative_context=narrative_text,
                surrounding_subtitles=segment_subs
            )
            
            concept = self._create_visual_concept(gap)
            visual_concepts.append(concept)
        
        return visual_concepts
    
    def _create_narrative_segments(self, subtitles: List[Subtitle], 
                                 target_length: float) -> List[Tuple[float, float, List[Subtitle]]]:
        """Create intelligent narrative segments."""
        if not subtitles:
            return []
        
        segments = []
        current_segment = []
        segment_start = 0
        
        for i, sub in enumerate(subtitles):
            current_segment.append(sub)
            
            # Check if we should end this segment
            segment_duration = sub.end_time - segment_start
            
            # Reasons to end segment:
            # 1. Reached target length
            # 2. Natural break (period at end of subtitle)
            # 3. Theme change detected
            should_break = (
                segment_duration >= target_length or
                sub.text.rstrip().endswith('.') and segment_duration >= target_length * 0.7 or
                i == len(subtitles) - 1
            )
            
            if should_break and current_segment:
                segment_end = sub.end_time
                segments.append((segment_start, segment_end, current_segment.copy()))
                
                # Start new segment
                current_segment = []
                segment_start = segment_end
        
        return segments
    
    def _create_visual_concept(self, gap: Gap) -> VisualConcept:
        """Create a complete visual concept for a gap."""
        # Identify themes
        themes = identify_themes(gap.narrative_context)
        
        # Get visual elements
        visual_elements = get_visual_elements(themes)
        
        # Create concept description
        concept_description = self._generate_concept_description(themes, visual_elements, gap)
        
        # Generate prompts
        text_prompt = self._generate_text_to_image_prompt(concept_description, visual_elements)
        video_prompt = self._generate_image_to_video_prompt(concept_description, themes, gap.duration)
        
        # Determine animation style
        animation_style = get_animation_style(themes, gap.duration)
        
        # Calculate extension strategy
        extension_strategy = self._calculate_extension_strategy(gap.duration)
        
        return VisualConcept(
            gap=gap,
            themes=themes,
            visual_elements=visual_elements,
            concept_description=concept_description,
            text_to_image_prompt=enhance_prompt_with_biblical_style(text_prompt),
            image_to_video_prompt=video_prompt,
            animation_style=animation_style,
            extension_strategy=extension_strategy
        )
    
    def _generate_concept_description(self, themes: List[str], 
                                    visual_elements: Dict[str, List[str]], 
                                    gap: Gap) -> str:
        """Generate a conceptual description of the visual."""
        primary_theme = themes[0] if themes else "craftsmanship"
        
        descriptions = {
            "divine_calling": f"A moment of divine commissioning showing {visual_elements['primary_elements'][0]}",
            "craftsmanship": f"Skilled artisans demonstrating {visual_elements['primary_elements'][0]}",
            "community": f"The Hebrew community united in {visual_elements['primary_elements'][0]}",
            "worship": f"A sacred moment of worship featuring {visual_elements['primary_elements'][0]}",
            "divine_presence": f"The manifestation of God's presence through {visual_elements['primary_elements'][0]}",
            "generosity": f"The people's generous response shown through {visual_elements['primary_elements'][0]}",
            "wisdom": f"Divine wisdom revealed through {visual_elements['primary_elements'][0]}"
        }
        
        base_description = descriptions.get(primary_theme, "A biblical scene")
        atmosphere = visual_elements['atmosphere'][0] if visual_elements['atmosphere'] else "reverent"
        
        return f"{base_description} with {atmosphere} atmosphere"
    
    def _generate_text_to_image_prompt(self, concept: str, visual_elements: Dict) -> str:
        """Generate MidJourney text-to-image prompt."""
        elements = []
        
        # Add concept
        elements.append(concept)
        
        # Add primary visual elements
        if visual_elements['primary_elements']:
            elements.extend(visual_elements['primary_elements'][:2])
        
        # Add style descriptors
        if visual_elements['style_descriptors']:
            elements.extend(visual_elements['style_descriptors'])
        
        # Add setting
        elements.append("ancient Hebrew tabernacle construction site")
        elements.append("desert wilderness with Mount Sinai in background")
        
        return ", ".join(elements)
    
    def _generate_image_to_video_prompt(self, concept: str, themes: List[str], duration: float) -> str:
        """Generate MidJourney image-to-video animation prompt."""
        animation_style = get_animation_style(themes, duration)
        
        if "craftsmanship" in themes:
            motion = f"{animation_style}, hands working with purpose, tools in synchronized motion"
        elif "divine_presence" in themes:
            motion = f"{animation_style}, divine light pulsing gently, ethereal particles ascending"
        elif "community" in themes:
            motion = f"{animation_style}, unified movement across the scene, coordinated workflow"
        else:
            motion = f"{animation_style}, subtle environmental movement, living atmosphere"
        
        return f"{motion}, maintain compositional integrity, cinematic camera drift"
    
    def _calculate_extension_strategy(self, duration: float) -> Dict:
        """Calculate video extension strategy."""
        clips_needed = duration / self.midjourney_duration
        
        if duration <= self.midjourney_duration:
            return {
                "type": "single_clip",
                "coverage": "perfect_fit",
                "extensions_needed": 0,
                "total_clips": 1,
                "instructions": "Single 5.07s clip covers the entire gap"
            }
        
        extensions = int(clips_needed) - 1
        remainder = duration - (int(clips_needed) * self.midjourney_duration)
        
        strategy = {
            "type": "serial_extension",
            "coverage": f"{int(clips_needed)} full clips",
            "extensions_needed": extensions,
            "total_clips": int(clips_needed),
            "exact_coverage": f"{int(clips_needed) * self.midjourney_duration:.2f}s of {duration:.2f}s",
            "remainder": f"{remainder:.2f}s uncovered" if remainder > 0 else "perfect coverage"
        }
        
        # Add extension instructions
        if extensions == 1:
            strategy["instructions"] = "Create base clip, then extend once with same seed"
        else:
            strategy["instructions"] = f"Create base clip, then extend {extensions} times serially"
        
        return strategy