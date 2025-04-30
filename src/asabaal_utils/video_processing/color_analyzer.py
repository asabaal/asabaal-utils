"""
Color analyzer module for video processing.

This module provides utilities for analyzing color themes and palettes in videos.
"""

import os
import logging
import tempfile
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union, Set
from dataclasses import dataclass, field
from collections import Counter
import math
import colorsys

import numpy as np
from tqdm import tqdm
# Also import as needed:
# from moviepy import fadein
from moviepy.video.io import VideoFileClip
from PIL import Image, ImageDraw
from sklearn.cluster import KMeans

logger = logging.getLogger(__name__)


@dataclass
class ColorSegment:
    """A segment of video with color information."""
    start_time: float
    end_time: float
    dominant_colors: List[Tuple[int, int, int]] = field(default_factory=list)
    color_names: List[str] = field(default_factory=list)
    color_hex: List[str] = field(default_factory=list)
    brightness: float = 0.0
    saturation: float = 0.0
    contrast: float = 0.0
    colorfulness: float = 0.0
    color_variance: float = 0.0
    
    @property
    def duration(self) -> float:
        """Get the duration of this segment."""
        return self.end_time - self.start_time


@dataclass
class ColorTheme:
    """Extracted color theme from a video."""
    dominant_colors: List[Tuple[int, int, int]] = field(default_factory=list)
    color_hex: List[str] = field(default_factory=list)
    color_names: List[str] = field(default_factory=list)
    color_percentages: List[float] = field(default_factory=list)
    complementary_colors: List[Tuple[int, int, int]] = field(default_factory=list)
    complementary_hex: List[str] = field(default_factory=list)
    color_palette_path: str = ""
    theme_type: str = ""
    brightness: float = 0.0
    saturation: float = 0.0
    contrast: float = 0.0
    color_variance: float = 0.0
    emotions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "dominant_colors": [list(c) for c in self.dominant_colors],
            "color_hex": self.color_hex,
            "color_names": self.color_names,
            "color_percentages": self.color_percentages,
            "complementary_colors": [list(c) for c in self.complementary_colors],
            "complementary_hex": self.complementary_hex,
            "color_palette_path": self.color_palette_path,
            "theme_type": self.theme_type,
            "brightness": self.brightness,
            "saturation": self.saturation,
            "contrast": self.contrast,
            "color_variance": self.color_variance,
            "emotions": self.emotions
        }


class ColorNameMatcher:
    """Matches RGB colors to human-readable color names."""
    
    # Basic color dictionary with RGB values and names
    COLOR_MAP = {
        (0, 0, 0): "Black",
        (255, 255, 255): "White",
        (128, 128, 128): "Gray",
        (255, 0, 0): "Red",
        (0, 255, 0): "Green",
        (0, 0, 255): "Blue",
        (255, 255, 0): "Yellow",
        (255, 0, 255): "Magenta",
        (0, 255, 255): "Cyan",
        (128, 0, 0): "Maroon",
        (0, 128, 0): "Dark Green",
        (0, 0, 128): "Navy Blue",
        (128, 128, 0): "Olive",
        (128, 0, 128): "Purple",
        (0, 128, 128): "Teal",
        (255, 165, 0): "Orange",
        (210, 180, 140): "Tan",
        (165, 42, 42): "Brown",
        (250, 128, 114): "Salmon",
        (255, 192, 203): "Pink",
        (245, 222, 179): "Wheat",
        (220, 220, 220): "Light Gray",
        (240, 248, 255): "Alice Blue",
        (250, 235, 215): "Antique White",
        (127, 255, 212): "Aquamarine",
        (240, 255, 255): "Azure",
        (245, 245, 220): "Beige",
        (255, 228, 196): "Bisque",
        (255, 235, 205): "Blanched Almond",
        (138, 43, 226): "Blue Violet",
        (222, 184, 135): "Burlywood",
        (95, 158, 160): "Cadet Blue",
        (127, 255, 0): "Chartreuse",
        (210, 105, 30): "Chocolate",
        (255, 127, 80): "Coral",
        (100, 149, 237): "Cornflower Blue",
        (255, 248, 220): "Cornsilk",
        (220, 20, 60): "Crimson",
        (184, 134, 11): "Dark Goldenrod",
        (0, 100, 0): "Dark Green",
        (189, 183, 107): "Dark Khaki",
        (139, 0, 139): "Dark Magenta",
        (85, 107, 47): "Dark Olive Green",
        (255, 140, 0): "Dark Orange",
        (153, 50, 204): "Dark Orchid",
        (139, 0, 0): "Dark Red",
        (143, 188, 143): "Dark Sea Green",
        (72, 61, 139): "Dark Slate Blue",
        (47, 79, 79): "Dark Slate Gray",
        (0, 206, 209): "Dark Turquoise",
        (148, 0, 211): "Dark Violet",
        (255, 20, 147): "Deep Pink",
        (0, 191, 255): "Deep Sky Blue",
        (105, 105, 105): "Dim Gray",
        (30, 144, 255): "Dodger Blue",
        (178, 34, 34): "Firebrick",
        (255, 250, 240): "Floral White",
        (34, 139, 34): "Forest Green",
        (220, 220, 220): "Gainsboro",
        (248, 248, 255): "Ghost White",
        (255, 215, 0): "Gold",
        (218, 165, 32): "Goldenrod",
        (173, 255, 47): "Green Yellow",
        (240, 255, 240): "Honeydew",
        (255, 105, 180): "Hot Pink",
        (205, 92, 92): "Indian Red",
        (255, 255, 240): "Ivory",
        (240, 230, 140): "Khaki",
        (230, 230, 250): "Lavender",
        (255, 240, 245): "Lavender Blush",
        (124, 252, 0): "Lawn Green",
        (255, 250, 205): "Lemon Chiffon",
        (173, 216, 230): "Light Blue",
        (240, 128, 128): "Light Coral",
        (224, 255, 255): "Light Cyan",
        (250, 250, 210): "Light Goldenrod Yellow",
        (144, 238, 144): "Light Green",
        (211, 211, 211): "Light Gray",
        (255, 182, 193): "Light Pink",
        (255, 160, 122): "Light Salmon",
        (32, 178, 170): "Light Sea Green",
        (135, 206, 250): "Light Sky Blue",
        (119, 136, 153): "Light Slate Gray",
        (176, 196, 222): "Light Steel Blue",
        (255, 255, 224): "Light Yellow",
        (50, 205, 50): "Lime Green",
        (250, 240, 230): "Linen",
        (102, 205, 170): "Medium Aquamarine",
        (0, 0, 205): "Medium Blue",
        (186, 85, 211): "Medium Orchid",
        (147, 112, 219): "Medium Purple",
        (60, 179, 113): "Medium Sea Green",
        (123, 104, 238): "Medium Slate Blue",
        (0, 250, 154): "Medium Spring Green",
        (72, 209, 204): "Medium Turquoise",
        (199, 21, 133): "Medium Violet Red",
        (25, 25, 112): "Midnight Blue",
        (245, 255, 250): "Mint Cream",
        (255, 228, 225): "Misty Rose",
        (255, 228, 181): "Moccasin",
        (255, 222, 173): "Navajo White",
        (253, 245, 230): "Old Lace",
        (107, 142, 35): "Olive Drab",
        (255, 69, 0): "Orange Red",
        (218, 112, 214): "Orchid",
        (238, 232, 170): "Pale Goldenrod",
        (152, 251, 152): "Pale Green",
        (175, 238, 238): "Pale Turquoise",
        (219, 112, 147): "Pale Violet Red",
        (255, 239, 213): "Papaya Whip",
        (255, 218, 185): "Peach Puff",
        (205, 133, 63): "Peru",
        (221, 160, 221): "Plum",
        (176, 224, 230): "Powder Blue",
        (188, 143, 143): "Rosy Brown",
        (65, 105, 225): "Royal Blue",
        (139, 69, 19): "Saddle Brown",
        (250, 128, 114): "Salmon",
        (244, 164, 96): "Sandy Brown",
        (46, 139, 87): "Sea Green",
        (255, 245, 238): "Seashell",
        (160, 82, 45): "Sienna",
        (135, 206, 235): "Sky Blue",
        (106, 90, 205): "Slate Blue",
        (112, 128, 144): "Slate Gray",
        (255, 250, 250): "Snow",
        (0, 255, 127): "Spring Green",
        (70, 130, 180): "Steel Blue",
        (210, 180, 140): "Tan",
        (216, 191, 216): "Thistle",
        (255, 99, 71): "Tomato",
        (64, 224, 208): "Turquoise",
        (238, 130, 238): "Violet",
        (245, 222, 179): "Wheat",
        (245, 245, 245): "White Smoke",
        (154, 205, 50): "Yellow Green"
    }
    
    @classmethod
    def _color_distance(cls, color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> float:
        """Calculate distance between two RGB colors."""
        r1, g1, b1 = color1
        r2, g2, b2 = color2
        
        # Use weighted Euclidean distance for better perceptual matching
        # Human eyes are more sensitive to green, less to blue
        return math.sqrt((r1 - r2) ** 2 * 0.3 + (g1 - g2) ** 2 * 0.59 + (b1 - b2) ** 2 * 0.11)
    
    @classmethod
    def get_color_name(cls, rgb: Tuple[int, int, int]) -> str:
        """Get the closest color name for an RGB tuple."""
        min_distance = float('inf')
        closest_color = "Unknown"
        
        for known_rgb, color_name in cls.COLOR_MAP.items():
            distance = cls._color_distance(rgb, known_rgb)
            if distance < min_distance:
                min_distance = distance
                closest_color = color_name
        
        return closest_color
    
    @classmethod
    def get_emotion(cls, rgb: Tuple[int, int, int]) -> List[str]:
        """
        Get emotional associations for a color.
        Very simplified color psychology.
        """
        r, g, b = rgb
        emotions = []
        
        # Convert to HSV for easier analysis
        h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
        
        # Categorize by hue
        if 0.95 <= h <= 1.0 or 0.0 <= h < 0.05:  # Red
            emotions.extend(["Energy", "Passion", "Urgency"])
        elif 0.05 <= h < 0.1:  # Orange
            emotions.extend(["Warmth", "Enthusiasm", "Creativity"])
        elif 0.1 <= h < 0.2:  # Yellow
            emotions.extend(["Optimism", "Clarity", "Cheerfulness"])
        elif 0.2 <= h < 0.4:  # Green
            emotions.extend(["Growth", "Harmony", "Freshness"])
        elif 0.4 <= h < 0.6:  # Teal/Cyan
            emotions.extend(["Calm", "Trust", "Balance"])
        elif 0.6 <= h < 0.7:  # Blue
            emotions.extend(["Trust", "Serenity", "Reliability"])
        elif 0.7 <= h < 0.8:  # Purple
            emotions.extend(["Creativity", "Luxury", "Mystery"])
        elif 0.8 <= h < 0.95:  # Pink/Magenta
            emotions.extend(["Compassion", "Playfulness", "Romance"])
        
        # Categorize by saturation and value
        if s < 0.2:  # Low saturation (grayscale)
            if v < 0.3:  # Dark
                emotions.extend(["Sophistication", "Formality", "Mystery"])
            elif v > 0.7:  # Light
                emotions.extend(["Simplicity", "Clarity", "Minimalism"])
            else:  # Medium
                emotions.extend(["Neutrality", "Calmness", "Balance"])
        
        # High saturation and value (vibrant colors)
        if s > 0.7 and v > 0.7:
            emotions.extend(["Energy", "Vibrancy", "Attention"])
        
        # Return unique emotions
        return list(set(emotions))


class ColorAnalyzer:
    """
    Analyzer for video color themes and palettes.
    
    This class extracts and analyzes color information from videos.
    """
    
    def __init__(
        self,
        palette_size: int = 5,
        frame_sample_rate: float = 1.0,  # Sample one frame per second by default
        segment_duration: float = 10.0,  # Segment length in seconds
        skip_start_percent: float = 0.05,
        skip_end_percent: float = 0.05,
        color_clustering_method: str = "kmeans",
    ):
        """
        Initialize the color analyzer.
        
        Args:
            palette_size: Number of colors to extract for the palette
            frame_sample_rate: How many frames per second to sample
            segment_duration: Duration of each color segment in seconds
            skip_start_percent: Percentage of video to skip from the start
            skip_end_percent: Percentage of video to skip from the end
            color_clustering_method: Method for color clustering ('kmeans' or 'dominant')
        """
        self.palette_size = palette_size
        self.frame_sample_rate = frame_sample_rate
        self.segment_duration = segment_duration
        self.skip_start_percent = skip_start_percent
        self.skip_end_percent = skip_end_percent
        self.color_clustering_method = color_clustering_method
    
    def _quantize_colors(self, image: np.ndarray, n_colors: int) -> Tuple[List[Tuple[int, int, int]], List[float]]:
        """
        Quantize colors in an image to a smaller palette.
        
        Args:
            image: Image as numpy array
            n_colors: Number of colors to extract
            
        Returns:
            List of (r,g,b) tuples and their occurrence percentages
        """
        # Reshape image for clustering
        pixels = image.reshape(-1, 3)
        
        if self.color_clustering_method == "kmeans":
            # Use K-means clustering to find dominant colors
            kmeans = KMeans(n_clusters=n_colors, random_state=0, n_init=10).fit(pixels)
            centers = kmeans.cluster_centers_.astype(int)
            
            # Calculate cluster sizes
            labels = kmeans.labels_
            counts = np.bincount(labels)
            total_pixels = len(pixels)
            percentages = [count / total_pixels for count in counts]
            
            colors = [tuple(center) for center in centers]
            
            # Sort by percentage
            colors_with_pct = sorted(zip(colors, percentages), key=lambda x: x[1], reverse=True)
            colors = [c for c, _ in colors_with_pct]
            percentages = [p for _, p in colors_with_pct]
            
        else:  # Simple dominant color method
            # Convert to PIL for quantization
            pil_img = Image.fromarray(image.astype('uint8'))
            
            # Quantize to a limited palette
            quantized = pil_img.quantize(colors=n_colors)
            palette = quantized.getpalette()
            
            # Count occurrences of each color
            color_counts = Counter(quantized.getdata())
            total_pixels = pil_img.width * pil_img.height
            
            # Extract dominant colors
            colors = []
            percentages = []
            
            for color_idx, count in color_counts.most_common(n_colors):
                if color_idx * 3 + 2 < len(palette):
                    r, g, b = palette[color_idx*3:color_idx*3+3]
                    colors.append((r, g, b))
                    percentages.append(count / total_pixels)
        
        return colors, percentages
    
    def _calculate_frame_metrics(self, frame: np.ndarray) -> Dict[str, float]:
        """
        Calculate color metrics for a frame.
        
        Args:
            frame: Frame as numpy array
            
        Returns:
            Dictionary of color metrics
        """
        # Convert to float for calculations
        frame_float = frame.astype(float)
        
        # Calculate brightness (mean of all pixels)
        brightness = np.mean(frame_float) / 255.0
        
        # Convert to HSV for saturation
        hsv = np.zeros_like(frame_float)
        # Vectorized RGB to HSV
        r, g, b = frame_float[:, :, 0] / 255.0, frame_float[:, :, 1] / 255.0, frame_float[:, :, 2] / 255.0
        maxc = np.maximum(np.maximum(r, g), b)
        minc = np.minimum(np.minimum(r, g), b)
        hsv[:, :, 2] = maxc
        delta = maxc - minc
        # Set saturation to 0 where maxc is 0 to avoid divide by zero
        hsv[:, :, 1] = np.divide(delta, maxc, out=np.zeros_like(delta), where=maxc!=0)
        
        # Calculate mean saturation
        saturation = np.mean(hsv[:, :, 1])
        
        # Calculate contrast (standard deviation of brightness)
        contrast = np.std(frame_float) / 255.0
        
        # Calculate color variance (mean of channel variances)
        r_var = np.var(frame[:, :, 0]) / 255.0
        g_var = np.var(frame[:, :, 1]) / 255.0
        b_var = np.var(frame[:, :, 2]) / 255.0
        color_variance = (r_var + g_var + b_var) / 3.0
        
        # Calculate colorfulness
        rg = frame_float[:, :, 0] - frame_float[:, :, 1]
        yb = 0.5 * (frame_float[:, :, 0] + frame_float[:, :, 1]) - frame_float[:, :, 2]
        rg_mean = np.mean(rg)
        yb_mean = np.mean(yb)
        rg_std = np.std(rg)
        yb_std = np.std(yb)
        colorfulness = np.sqrt(rg_std**2 + yb_std**2) + 0.3 * np.sqrt(rg_mean**2 + yb_mean**2)
        colorfulness = min(1.0, colorfulness / 100.0)  # Normalize
        
        return {
            "brightness": brightness,
            "saturation": saturation,
            "contrast": contrast,
            "color_variance": color_variance,
            "colorfulness": colorfulness
        }
    
    def _rgb_to_hex(self, rgb: Tuple[int, int, int]) -> str:
        """Convert RGB tuple to hex color code."""
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
    
    def _get_complementary_color(self, rgb: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """Get the complementary color for an RGB tuple."""
        r, g, b = rgb
        return (255 - r, 255 - g, 255 - b)
    
    def _determine_theme_type(self, colors: List[Tuple[int, int, int]], metrics: Dict[str, float]) -> str:
        """
        Determine the type of color theme.
        
        Args:
            colors: List of RGB color tuples
            metrics: Color metrics dictionary
            
        Returns:
            String describing the theme type
        """
        # Convert to HSV for analysis
        hsv_colors = [colorsys.rgb_to_hsv(r/255, g/255, b/255) for r, g, b in colors]
        
        # Calculate hue variance
        hues = [h for h, _, _ in hsv_colors]
        hue_var = np.var(hues)
        
        # Calculate saturation and value means
        sat_mean = np.mean([s for _, s, _ in hsv_colors])
        val_mean = np.mean([v for _, _, v in hsv_colors])
        
        # Determine theme type
        if sat_mean < 0.2:
            if val_mean < 0.3:
                return "Dark Monochromatic"
            elif val_mean > 0.7:
                return "Light Monochromatic"
            else:
                return "Grayscale"
        
        if hue_var < 0.01:
            return "Monochromatic"
        
        # Check for analogous colors (adjacent on color wheel)
        sorted_hues = sorted(hues)
        if sorted_hues[-1] - sorted_hues[0] < 0.25 or (sorted_hues[-1] > 0.75 and sorted_hues[0] < 0.25):
            return "Analogous"
        
        # Check for complementary (opposite on color wheel)
        for i, h1 in enumerate(hues):
            for h2 in hues[i+1:]:
                diff = abs(h1 - h2)
                if abs(diff - 0.5) < 0.1:
                    return "Complementary"
        
        # Check for triadic (three colors evenly spaced)
        if len(hues) >= 3:
            for i, h1 in enumerate(hues):
                for j, h2 in enumerate(hues[i+1:], i+1):
                    for h3 in hues[j+1:]:
                        diffs = [abs((h2 - h1) % 1), abs((h3 - h2) % 1), abs((h1 - h3) % 1)]
                        if all(abs(d - 0.33) < 0.1 for d in diffs):
                            return "Triadic"
        
        # Default
        return "Varied"
    
    def _create_color_palette_image(
        self, 
        colors: List[Tuple[int, int, int]], 
        percentages: List[float], 
        output_path: str,
        width: int = 800,
        height: int = 100
    ) -> str:
        """
        Create a color palette image.
        
        Args:
            colors: List of RGB color tuples
            percentages: List of color percentages
            output_path: Path to save the image
            width: Image width
            height: Image height
            
        Returns:
            Path to the saved image
        """
        # Create a new image
        img = Image.new('RGB', (width, height), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # Draw color blocks
        x_pos = 0
        for color, pct in zip(colors, percentages):
            block_width = int(width * pct)
            draw.rectangle([(x_pos, 0), (x_pos + block_width, height)], fill=color)
            x_pos += block_width
        
        # Save the image
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path)
        
        return output_path
    
    def analyze_video_colors(
        self, 
        video_path: Union[str, Path],
        output_dir: Optional[Union[str, Path]] = None,
        create_palette_image: bool = True,
        metadata_file: Optional[Union[str, Path]] = None,
        create_segments: bool = True,
        segment_palette_images: bool = False
    ) -> Tuple[ColorTheme, List[ColorSegment]]:
        """
        Analyze colors in a video.
        
        Args:
            video_path: Path to the video file
            output_dir: Directory to save output files (if None, creates a temp dir)
            create_palette_image: Whether to create a color palette image
            metadata_file: Optional path to save color metadata as JSON
            create_segments: Whether to analyze the video in segments
            segment_palette_images: Whether to create palette images for each segment
            
        Returns:
            Tuple of (ColorTheme, List[ColorSegment])
        """
        video_path = str(video_path)
        logger.info(f"Analyzing colors in {video_path}")
        
        # Create output directory if needed
        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="video_colors_")
            logger.info(f"Created temporary output directory: {output_dir}")
        else:
            output_dir = str(output_dir)
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"Saving color analysis to: {output_dir}")
        
        # Extract video basename without extension
        video_basename = os.path.splitext(os.path.basename(video_path))[0]
        
        segments = []
        all_colors = []
        all_percentages = []
        frame_metrics = []
        
        # Process the video
        with VideoFileClip(video_path) as video:
            # Calculate processing parameters
            duration = video.duration
            start_time = duration * self.skip_start_percent
            end_time = duration * (1.0 - self.skip_end_percent)
            effective_duration = end_time - start_time
            
            # Calculate frame sampling interval
            sampling_interval = 1.0 / self.frame_sample_rate
            
            # Process video in segments or as a whole
            if create_segments:
                # Define segments
                segment_starts = np.arange(start_time, end_time, self.segment_duration)
                
                logger.info(f"Analyzing video in {len(segment_starts)} segments")
                
                for i, seg_start in enumerate(segment_starts):
                    seg_end = min(seg_start + self.segment_duration, end_time)
                    
                    # Sample frames within this segment
                    segment_frames = []
                    segment_times = np.arange(seg_start, seg_end, sampling_interval)
                    
                    for time in tqdm(segment_times, desc=f"Analyzing segment {i+1}/{len(segment_starts)}"):
                        frame = video.get_frame(time)
                        segment_frames.append(frame)
                    
                    if not segment_frames:
                        continue
                    
                    # Combine frames for analysis
                    combined_frame = np.mean(segment_frames, axis=0).astype(np.uint8)
                    
                    # Extract colors
                    colors, percentages = self._quantize_colors(
                        combined_frame, 
                        self.palette_size
                    )
                    
                    # Calculate metrics
                    metrics = self._calculate_frame_metrics(combined_frame)
                    
                    # Create color names and hex values
                    color_names = [ColorNameMatcher.get_color_name(color) for color in colors]
                    color_hex = [self._rgb_to_hex(color) for color in colors]
                    
                    # Create segment
                    segment = ColorSegment(
                        start_time=seg_start,
                        end_time=seg_end,
                        dominant_colors=colors,
                        color_names=color_names,
                        color_hex=color_hex,
                        brightness=metrics["brightness"],
                        saturation=metrics["saturation"],
                        contrast=metrics["contrast"],
                        colorfulness=metrics["colorfulness"],
                        color_variance=metrics["color_variance"]
                    )
                    
                    segments.append(segment)
                    
                    # Add to overall analysis
                    all_colors.extend([(color, pct) for color, pct in zip(colors, percentages)])
                    frame_metrics.append(metrics)
                    
                    # Create segment palette image if requested
                    if segment_palette_images:
                        segment_palette_path = os.path.join(
                            output_dir, 
                            f"{video_basename}_segment_{i+1:02d}_palette.png"
                        )
                        self._create_color_palette_image(
                            colors, 
                            percentages, 
                            segment_palette_path
                        )
                
                # Combine all colors and re-quantize for overall palette
                all_colors.sort(key=lambda x: x[1], reverse=True)
                all_colors_resized = all_colors[:self.palette_size * 2]
                
                # We need to weight by both percentage and occurrence
                weighted_colors = []
                for color, pct in all_colors_resized:
                    # Add multiple instances based on percentage
                    count = max(1, int(pct * 100))
                    weighted_colors.extend([color] * count)
                
                weighted_colors_array = np.array(weighted_colors)
                colors, percentages = self._quantize_colors(
                    weighted_colors_array.reshape(-1, 3),
                    self.palette_size
                )
                
            else:
                # Sample frames throughout the video
                sample_times = np.arange(start_time, end_time, sampling_interval)
                frames = []
                
                for time in tqdm(sample_times, desc="Analyzing frames"):
                    frame = video.get_frame(time)
                    frames.append(frame)
                    frame_metrics.append(self._calculate_frame_metrics(frame))
                
                # Combine frames for analysis
                combined_frame = np.mean(frames, axis=0).astype(np.uint8)
                
                # Extract colors
                colors, percentages = self._quantize_colors(
                    combined_frame, 
                    self.palette_size
                )
        
        # Create color names and hex values
        color_names = [ColorNameMatcher.get_color_name(color) for color in colors]
        color_hex = [self._rgb_to_hex(color) for color in colors]
        
        # Generate complementary colors
        complementary_colors = [self._get_complementary_color(color) for color in colors]
        complementary_hex = [self._rgb_to_hex(color) for color in complementary_colors]
        
        # Calculate overall metrics
        overall_brightness = np.mean([m["brightness"] for m in frame_metrics])
        overall_saturation = np.mean([m["saturation"] for m in frame_metrics])
        overall_contrast = np.mean([m["contrast"] for m in frame_metrics])
        overall_variance = np.mean([m["color_variance"] for m in frame_metrics])
        
        # Determine theme type
        theme_type = self._determine_theme_type(colors, {
            "brightness": overall_brightness,
            "saturation": overall_saturation,
            "contrast": overall_contrast,
            "variance": overall_variance
        })
        
        # Get emotional associations
        emotions = []
        for color in colors:
            emotions.extend(ColorNameMatcher.get_emotion(color))
        emotions = list(set(emotions))
        
        # Create palette image
        palette_path = ""
        if create_palette_image:
            palette_path = os.path.join(output_dir, f"{video_basename}_palette.png")
            self._create_color_palette_image(colors, percentages, palette_path)
        
        # Create color theme
        theme = ColorTheme(
            dominant_colors=colors,
            color_hex=color_hex,
            color_names=color_names,
            color_percentages=percentages,
            complementary_colors=complementary_colors,
            complementary_hex=complementary_hex,
            color_palette_path=palette_path,
            theme_type=theme_type,
            brightness=overall_brightness,
            saturation=overall_saturation,
            contrast=overall_contrast,
            color_variance=overall_variance,
            emotions=emotions
        )
        
        # Save metadata if requested
        if metadata_file:
            metadata = {
                "video_file": video_path,
                "theme": theme.to_dict(),
                "segments": [
                    {
                        "start_time": segment.start_time,
                        "end_time": segment.end_time,
                        "dominant_colors": [list(c) for c in segment.dominant_colors],
                        "color_names": segment.color_names,
                        "color_hex": segment.color_hex,
                        "brightness": segment.brightness,
                        "saturation": segment.saturation,
                        "contrast": segment.contrast,
                        "colorfulness": segment.colorfulness,
                        "color_variance": segment.color_variance
                    }
                    for segment in segments
                ]
            }
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Saved color analysis metadata to {metadata_file}")
        
        return theme, segments


def analyze_video_colors(
    video_path: Union[str, Path],
    output_dir: Optional[Union[str, Path]] = None,
    palette_size: int = 5,
    frame_sample_rate: float = 1.0,
    segment_duration: float = 10.0,
    create_palette_image: bool = True,
    create_segments: bool = True,
    segment_palette_images: bool = False,
    metadata_file: Optional[Union[str, Path]] = None
) -> Dict[str, Any]:
    """
    Analyze colors in a video.
    
    Args:
        video_path: Path to the video file
        output_dir: Directory to save output files (if None, creates a temp dir)
        palette_size: Number of colors to extract for the palette
        frame_sample_rate: How many frames per second to sample
        segment_duration: Duration of each color segment in seconds
        create_palette_image: Whether to create a color palette image
        create_segments: Whether to analyze the video in segments
        segment_palette_images: Whether to create palette images for each segment
        metadata_file: Optional path to save color metadata as JSON
        
    Returns:
        Dictionary with color analysis results
    """
    # Create the analyzer with the specified parameters
    analyzer = ColorAnalyzer(
        palette_size=palette_size,
        frame_sample_rate=frame_sample_rate,
        segment_duration=segment_duration,
    )
    
    # Analyze the video
    theme, segments = analyzer.analyze_video_colors(
        video_path=video_path,
        output_dir=output_dir,
        create_palette_image=create_palette_image,
        metadata_file=metadata_file,
        create_segments=create_segments,
        segment_palette_images=segment_palette_images
    )
    
    # Convert to dictionary for return
    result = {
        "theme": {
            "dominant_colors": [list(c) for c in theme.dominant_colors],
            "color_hex": theme.color_hex,
            "color_names": theme.color_names,
            "color_percentages": [round(p, 3) for p in theme.color_percentages],
            "complementary_colors": [list(c) for c in theme.complementary_colors],
            "complementary_hex": theme.complementary_hex,
            "theme_type": theme.theme_type,
            "color_palette_path": theme.color_palette_path,
            "metrics": {
                "brightness": round(theme.brightness, 3),
                "saturation": round(theme.saturation, 3),
                "contrast": round(theme.contrast, 3),
                "color_variance": round(theme.color_variance, 3)
            },
            "emotions": theme.emotions
        },
        "segments": []
    }
    
    # Add segment data if available
    if segments:
        for i, segment in enumerate(segments):
            segment_data = {
                "index": i + 1,
                "start_time": segment.start_time,
                "end_time": segment.end_time,
                "duration": segment.duration,
                "colors": [
                    {
                        "rgb": list(color),
                        "hex": hex_code,
                        "name": name
                    }
                    for color, hex_code, name in zip(
                        segment.dominant_colors, 
                        segment.color_hex, 
                        segment.color_names
                    )
                ],
                "metrics": {
                    "brightness": round(segment.brightness, 3),
                    "saturation": round(segment.saturation, 3),
                    "contrast": round(segment.contrast, 3),
                    "colorfulness": round(segment.colorfulness, 3),
                    "color_variance": round(segment.color_variance, 3)
                }
            }
            result["segments"].append(segment_data)
    
    return result
