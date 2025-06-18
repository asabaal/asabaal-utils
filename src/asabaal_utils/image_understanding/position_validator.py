"""
Position validation for detecting character alignment issues
"""

import cv2
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
from .character_detector import DetectedCharacter
from .text_analyzer import SpacingAnalysis


@dataclass 
class AlignmentIssue:
    """Represents a character alignment issue"""
    character_index: int
    character: Optional[str]
    issue_type: str
    severity: float  # 0-1, higher is worse
    expected_position: Optional[Tuple[float, float]]
    actual_position: Tuple[float, float]
    correction_needed: Tuple[float, float]
    
    def __str__(self):
        char_info = f"'{self.character}'" if self.character else f"index {self.character_index}"
        return f"{self.issue_type} for {char_info} (severity: {self.severity:.2f})"


class PositionValidator:
    """Validates character positions and detects alignment issues"""
    
    def __init__(self):
        pass
    
    def validate_positions(self, characters: List[DetectedCharacter], 
                         expected_text: Optional[str] = None) -> List[AlignmentIssue]:
        """
        Validate character positions and detect issues
        
        Args:
            characters: Detected characters
            expected_text: Expected text
            
        Returns:
            List of alignment issues
        """
        issues = []
        
        if len(characters) < 2:
            return issues
        
        # Calculate expected positions based on uniform spacing
        expected_positions = self._calculate_expected_positions(characters)
        
        # Check each character
        for i, char in enumerate(characters):
            char_str = expected_text[i] if expected_text and i < len(expected_text) else None
            
            # Check horizontal position
            expected_x = expected_positions[i][0]
            actual_x = char.center_x
            x_deviation = abs(actual_x - expected_x)
            
            # Determine severity based on deviation
            char_width = char.width
            relative_deviation = x_deviation / char_width if char_width > 0 else 0
            
            if relative_deviation > 0.3:  # More than 30% off
                issue = AlignmentIssue(
                    character_index=i,
                    character=char_str,
                    issue_type="Horizontal misalignment",
                    severity=min(1.0, relative_deviation),
                    expected_position=(expected_x, char.center_y),
                    actual_position=(actual_x, char.center_y),
                    correction_needed=(expected_x - actual_x, 0)
                )
                issues.append(issue)
                
                # Misalignment detected
            
            # Special check for narrow characters
            if char.is_narrow:
                issues.extend(self._check_narrow_character(i, char, characters, char_str))
        
        return issues
    
    def _calculate_expected_positions(self, characters: List[DetectedCharacter]) -> List[Tuple[float, float]]:
        """Calculate expected character positions assuming uniform spacing"""
        if not characters:
            return []
        
        # Find the text bounds
        min_x = min(c.x for c in characters)
        max_x = max(c.x + c.width for c in characters)
        total_width = max_x - min_x
        
        # Calculate total character width
        total_char_width = sum(c.width for c in characters)
        
        # Calculate uniform spacing
        total_gap_space = total_width - total_char_width
        num_gaps = max(1, len(characters) - 1)
        uniform_gap = total_gap_space / num_gaps if num_gaps > 0 else 0
        
        # Calculate expected positions
        expected = []
        current_x = min_x
        
        for char in characters:
            # Center of character
            center_x = current_x + char.width / 2
            expected.append((center_x, char.center_y))
            current_x += char.width + uniform_gap
        
        return expected
    
    def _check_narrow_character(self, index: int, char: DetectedCharacter, 
                              all_chars: List[DetectedCharacter], 
                              char_str: Optional[str]) -> List[AlignmentIssue]:
        """Special checks for narrow characters like 'I'"""
        issues = []
        
        # Check if narrow character appears left-aligned instead of centered
        if index > 0 and index < len(all_chars) - 1:
            # Get spacing to neighbors
            left_char = all_chars[index - 1]
            right_char = all_chars[index + 1]
            
            left_gap = char.x - (left_char.x + left_char.width)
            right_gap = right_char.x - (char.x + char.width)
            
            # For a centered character, gaps should be similar
            gap_ratio = left_gap / right_gap if right_gap > 0 else float('inf')
            
            if gap_ratio < 0.5 or gap_ratio > 2.0:
                # Significant asymmetry
                ideal_center = (left_char.x + left_char.width + right_char.x) / 2
                actual_center = char.x + char.width / 2
                correction = ideal_center - actual_center
                
                issue = AlignmentIssue(
                    character_index=index,
                    character=char_str,
                    issue_type="Narrow character asymmetric spacing",
                    severity=min(1.0, abs(1 - gap_ratio) / 2),
                    expected_position=(ideal_center, char.center_y),
                    actual_position=(actual_center, char.center_y),
                    correction_needed=(correction, 0)
                )
                issues.append(issue)
        
        return issues
    
    def create_diagnostic_visualization(self, frame: np.ndarray, 
                                      characters: List[DetectedCharacter],
                                      issues: List[AlignmentIssue],
                                      expected_text: Optional[str] = None) -> np.ndarray:
        """
        Create visualization showing detected issues
        
        Args:
            frame: Original frame
            characters: Detected characters
            issues: Detected issues
            expected_text: Expected text
            
        Returns:
            Annotated frame
        """
        result = frame.copy()
        
        # Draw character bounds
        for i, char in enumerate(characters):
            # Color based on whether character has issues
            has_issue = any(issue.character_index == i for issue in issues)
            color = (0, 0, 255) if has_issue else (0, 255, 0)  # Red if issue, green if OK
            
            # Draw bounding box
            cv2.rectangle(result, (char.x, char.y), 
                         (char.x + char.width, char.y + char.height), 
                         color, 2)
            
            # Draw center point
            cv2.circle(result, (int(char.center_x), int(char.center_y)), 
                      3, (255, 255, 0), -1)
            
            # Label
            label = expected_text[i] if expected_text and i < len(expected_text) else str(i)
            cv2.putText(result, label, (char.x, char.y - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Draw expected positions and corrections
        for issue in issues:
            if issue.expected_position:
                # Draw expected position
                exp_x, exp_y = issue.expected_position
                cv2.circle(result, (int(exp_x), int(exp_y)), 
                          5, (0, 255, 255), 2)  # Yellow circle
                
                # Draw arrow from actual to expected
                act_x, act_y = issue.actual_position
                cv2.arrowedLine(result, 
                              (int(act_x), int(act_y)),
                              (int(exp_x), int(exp_y)),
                              (255, 0, 255), 2)  # Magenta arrow
        
        # Add legend
        y_offset = 30
        cv2.putText(result, "Green: OK, Red: Issue", (10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(result, "Yellow: Expected position", (10, y_offset + 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        cv2.putText(result, "Magenta: Correction needed", (10, y_offset + 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)
        
        return result
    
    def generate_report(self, characters: List[DetectedCharacter],
                       issues: List[AlignmentIssue],
                       expected_text: Optional[str] = None) -> str:
        """Generate text report of findings"""
        report = []
        report.append("CHARACTER POSITION VALIDATION REPORT")
        report.append("=" * 50)
        
        if expected_text:
            report.append(f"Expected text: '{expected_text}'")
        report.append(f"Detected characters: {len(characters)}")
        report.append(f"Issues found: {len(issues)}")
        
        if issues:
            report.append("\nISSUES DETECTED:")
            report.append("-" * 30)
            
            # Group by severity
            severe_issues = [i for i in issues if i.severity > 0.7]
            moderate_issues = [i for i in issues if 0.3 < i.severity <= 0.7]
            minor_issues = [i for i in issues if i.severity <= 0.3]
            
            if severe_issues:
                report.append("\nSEVERE:")
                for issue in severe_issues:
                    report.append(f"  - {issue}")
                    if issue.correction_needed[0] != 0:
                        report.append(f"    Needs {issue.correction_needed[0]:.1f}px horizontal adjustment")
            
            if moderate_issues:
                report.append("\nMODERATE:")
                for issue in moderate_issues:
                    report.append(f"  - {issue}")
            
            if minor_issues:
                report.append("\nMINOR:")
                for issue in minor_issues:
                    report.append(f"  - {issue}")
        else:
            report.append("\nNo alignment issues detected!")
        
        return "\n".join(report)