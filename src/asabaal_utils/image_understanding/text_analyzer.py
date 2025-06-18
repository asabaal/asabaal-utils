"""
Text analysis for character alignment and spacing
"""

import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from .character_detector import DetectedCharacter


class TextAlignment(Enum):
    """Text alignment types"""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    JUSTIFIED = "justified"


@dataclass
class SpacingAnalysis:
    """Analysis of character spacing"""
    characters: List[DetectedCharacter]
    gaps: List[float]
    center_distances: List[float]
    avg_gap: float
    std_gap: float
    avg_center_dist: float
    std_center_dist: float
    
    def get_outliers(self, threshold: float = 2.0) -> List[Tuple[int, float]]:
        """Get spacing outliers (index, deviation)"""
        outliers = []
        for i, gap in enumerate(self.gaps):
            deviation = abs(gap - self.avg_gap) / self.std_gap if self.std_gap > 0 else 0
            if deviation > threshold:
                outliers.append((i, deviation))
        return outliers


class TextAnalyzer:
    """Analyzes text positioning and alignment"""
    
    def __init__(self):
        pass
    
    def analyze_spacing(self, characters: List[DetectedCharacter]) -> SpacingAnalysis:
        """
        Analyze character spacing
        
        Args:
            characters: List of characters (should be from same line/word)
            
        Returns:
            SpacingAnalysis object
        """
        if len(characters) < 2:
            return SpacingAnalysis(
                characters=characters,
                gaps=[], center_distances=[],
                avg_gap=0, std_gap=0,
                avg_center_dist=0, std_center_dist=0
            )
        
        gaps = []
        center_distances = []
        
        for i in range(len(characters) - 1):
            # Gap between characters
            gap = characters[i+1].x - (characters[i].x + characters[i].width)
            gaps.append(gap)
            
            # Center-to-center distance
            center_dist = characters[i+1].center_x - characters[i].center_x
            center_distances.append(center_dist)
        
        return SpacingAnalysis(
            characters=characters,
            gaps=gaps,
            center_distances=center_distances,
            avg_gap=np.mean(gaps) if gaps else 0,
            std_gap=np.std(gaps) if gaps else 0,
            avg_center_dist=np.mean(center_distances) if center_distances else 0,
            std_center_dist=np.std(center_distances) if center_distances else 0
        )
    
    def detect_alignment(self, characters: List[DetectedCharacter]) -> TextAlignment:
        """
        Detect text alignment based on character positions
        
        Args:
            characters: List of characters
            
        Returns:
            Detected alignment type
        """
        if not characters:
            return TextAlignment.LEFT
        
        # Analyze horizontal variance
        x_positions = [c.center_x for c in characters]
        x_variance = np.var(x_positions)
        
        # Analyze gaps
        spacing = self.analyze_spacing(characters)
        
        # High variance in gaps suggests left/right alignment
        # Low variance suggests center/justified
        if spacing.std_gap < spacing.avg_gap * 0.1:
            # Very uniform spacing - likely center or justified
            return TextAlignment.CENTER
        else:
            # Check if characters are left-aligned
            left_edges = [c.x for c in characters]
            if np.std(left_edges) < 5:
                return TextAlignment.LEFT
            else:
                return TextAlignment.CENTER
    
    def find_baseline(self, characters: List[DetectedCharacter]) -> float:
        """
        Find the text baseline
        
        Args:
            characters: List of characters
            
        Returns:
            Y-coordinate of baseline
        """
        if not characters:
            return 0
        
        # Use bottom of characters to estimate baseline
        bottoms = [c.y + c.height for c in characters]
        
        # Filter out potential descenders (g, j, p, q, y)
        # These tend to be outliers below the main baseline
        sorted_bottoms = sorted(bottoms)
        
        # Use median to be robust to outliers
        baseline = np.median(sorted_bottoms)
        
        # Refine by only considering characters near the median
        refined_bottoms = [b for b in bottoms if abs(b - baseline) < 5]
        if refined_bottoms:
            baseline = np.mean(refined_bottoms)
        
        return baseline
    
    def calculate_alignment_score(self, characters: List[DetectedCharacter], 
                                expected_text: Optional[str] = None) -> float:
        """
        Calculate how well-aligned the text is (0-1, higher is better)
        
        Args:
            characters: Detected characters
            expected_text: Expected text for comparison
            
        Returns:
            Alignment score
        """
        if not characters:
            return 0.0
        
        score = 1.0
        
        # Check baseline alignment
        baseline = self.find_baseline(characters)
        baseline_deviations = [abs((c.y + c.height) - baseline) for c in characters]
        avg_baseline_dev = np.mean(baseline_deviations)
        
        # Penalize baseline deviation
        score *= max(0, 1 - avg_baseline_dev / 10)
        
        # Check spacing consistency
        spacing = self.analyze_spacing(characters)
        if spacing.avg_gap > 0:
            spacing_consistency = 1 - (spacing.std_gap / spacing.avg_gap)
            score *= max(0, spacing_consistency)
        
        # Check for outliers
        outliers = spacing.get_outliers()
        score *= max(0, 1 - len(outliers) / max(1, len(characters) - 1))
        
        # Check character count if expected text provided
        if expected_text and len(characters) != len(expected_text):
            count_penalty = abs(len(characters) - len(expected_text)) / len(expected_text)
            score *= max(0, 1 - count_penalty)
        
        return score
    
    def identify_problem_characters(self, characters: List[DetectedCharacter], 
                                  expected_text: Optional[str] = None) -> List[Tuple[int, str]]:
        """
        Identify characters with positioning problems
        
        Args:
            characters: Detected characters
            expected_text: Expected text
            
        Returns:
            List of (index, problem_description) tuples
        """
        problems = []
        
        if not characters:
            return problems
        
        # Check spacing
        spacing = self.analyze_spacing(characters)
        outliers = spacing.get_outliers()
        
        for idx, deviation in outliers:
            if idx < len(characters) - 1:
                char_info = f"between index {idx} and {idx+1}"
                if expected_text and idx < len(expected_text) - 1:
                    char_info = f"between '{expected_text[idx]}' and '{expected_text[idx+1]}'"
                problems.append((idx, f"Unusual spacing {char_info} (deviation: {deviation:.1f}σ)"))
        
        # Check baseline alignment
        baseline = self.find_baseline(characters)
        for i, char in enumerate(characters):
            deviation = abs((char.y + char.height) - baseline)
            if deviation > 5:
                char_info = f"at index {i}"
                if expected_text and i < len(expected_text):
                    char_info = f"'{expected_text[i]}'"
                problems.append((i, f"Character {char_info} is {deviation:.1f}px off baseline"))
        
        # Check for narrow characters that might be misaligned
        for i, char in enumerate(characters):
            if char.is_narrow:
                # Check if narrow character has different spacing pattern
                if i > 0 and i < len(characters) - 1:
                    left_gap = char.x - (characters[i-1].x + characters[i-1].width)
                    right_gap = characters[i+1].x - (char.x + char.width)
                    
                    if abs(left_gap - right_gap) > spacing.avg_gap * 0.5:
                        char_info = f"at index {i}"
                        if expected_text and i < len(expected_text):
                            char_info = f"'{expected_text[i]}'"
                        problems.append((i, f"Narrow character {char_info} has asymmetric spacing"))
        
        return problems