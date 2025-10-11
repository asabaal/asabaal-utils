"""
Character detection system using computer vision techniques
"""

import cv2
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional


@dataclass
class DetectedCharacter:
    """Represents a detected character in an image"""
    x: int
    y: int
    width: int
    height: int
    center_x: float
    center_y: float
    confidence: float
    bounding_box: np.ndarray
    mask: Optional[np.ndarray] = None
    predicted_char: Optional[str] = None
    
    @property
    def aspect_ratio(self) -> float:
        """Width to height ratio"""
        return self.width / self.height if self.height > 0 else 0
    
    @property
    def is_narrow(self) -> bool:
        """Check if character is narrow (likely I, l, i, etc.)"""
        return self.aspect_ratio < 0.3 or self.width < 10
    
    @property
    def area(self) -> int:
        """Pixel area of the character"""
        return self.width * self.height


class CharacterDetector:
    """Detects individual characters in rendered text"""
    
    def __init__(self):
        pass
        
    def detect_characters(self, frame: np.ndarray, 
                         expected_text: Optional[str] = None,
                         threshold_value: int = 200) -> List[DetectedCharacter]:
        """
        Detect characters in a frame
        
        Args:
            frame: Input frame (BGR format)
            expected_text: Expected text for validation
            threshold_value: Threshold for binary conversion
            
        Returns:
            List of detected characters sorted by x position
        """
        # Start character detection
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply threshold to get binary image
        _, binary = cv2.threshold(gray, threshold_value, 255, cv2.THRESH_BINARY)
        
        # Morphological operations to clean up
        kernel = np.ones((2, 2), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, hierarchy = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Found contours: len(contours)
        
        characters = []
        for idx, contour in enumerate(contours):
            # Get bounding box
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter out noise
            if w < 2 or h < 5:
                continue
            
            # Calculate moments for centroid
            M = cv2.moments(contour)
            if M["m00"] > 0:
                cx = M["m10"] / M["m00"]
                cy = M["m01"] / M["m00"]
            else:
                cx = x + w / 2
                cy = y + h / 2
            
            # Extract character mask
            mask = np.zeros(gray.shape, dtype=np.uint8)
            cv2.drawContours(mask, [contour], -1, 255, -1)
            char_mask = mask[y:y+h, x:x+w]
            
            # Calculate confidence based on fill ratio
            fill_ratio = cv2.countNonZero(char_mask) / (w * h)
            confidence = min(fill_ratio * 1.5, 1.0)
            
            char = DetectedCharacter(
                x=x, y=y, width=w, height=h,
                center_x=cx, center_y=cy,
                confidence=confidence,
                bounding_box=contour,
                mask=char_mask
            )
            
            characters.append(char)
            
            # Character detected at position
        
        # Sort by x position
        characters.sort(key=lambda c: c.x)
        
        # Detection complete
        
        return characters
    
    def group_into_words(self, characters: List[DetectedCharacter], 
                        max_gap_ratio: float = 2.0) -> List[List[DetectedCharacter]]:
        """
        Group characters into words based on spacing
        
        Args:
            characters: List of detected characters
            max_gap_ratio: Maximum gap ratio to consider same word
            
        Returns:
            List of character groups (words)
        """
        if not characters:
            return []
        
        # Calculate average character spacing
        gaps = []
        for i in range(len(characters) - 1):
            gap = characters[i+1].x - (characters[i].x + characters[i].width)
            gaps.append(gap)
        
        if not gaps:
            return [characters]
        
        avg_gap = np.mean(gaps)
        threshold = avg_gap * max_gap_ratio
        
        # Group characters
        words = []
        current_word = [characters[0]]
        
        for i in range(len(gaps)):
            if gaps[i] > threshold:
                # Start new word
                words.append(current_word)
                current_word = [characters[i+1]]
            else:
                # Add to current word
                current_word.append(characters[i+1])
        
        if current_word:
            words.append(current_word)
        
        return words
    
    def extract_character_image(self, frame: np.ndarray, char: DetectedCharacter) -> np.ndarray:
        """Extract the character region from the frame"""
        return frame[char.y:char.y+char.height, char.x:char.x+char.width]