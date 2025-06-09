"""
Church Service Video Analysis Pipeline

Comprehensive analysis of church service videos to automatically segment and classify
different parts of the service including music, announcements, sermons, slideshows, etc.
"""

import os
import json
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import tempfile
from datetime import datetime

import librosa
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
import cv2

try:
    from .silence_detector import SilenceDetector, AudioSegment
except ImportError:
    # Fallback if moviepy is not available
    @dataclass
    class AudioSegment:
        """Fallback AudioSegment class when moviepy is not available."""
        start: float
        end: float
        is_silence: bool
        rms_power: float = 0.0
        
        @property
        def duration(self) -> float:
            return self.end - self.start
    
    SilenceDetector = None

from .transcript_analyzer import TranscriptAnalyzer, TranscriptSegment
from .lyric_video.audio.analyzer import AudioAnalyzer
from .lyric_video.audio.features import AudioFeatures
from .frame_extractor import FrameExtractor
from .chunked_audio_analyzer import ChunkedAudioAnalyzer
from .church_audio_classifier import ChurchAudioClassifier

logger = logging.getLogger(__name__)


@dataclass
class ServiceSegment:
    """Represents a segment of the church service with classification."""
    start_time: float
    end_time: float
    segment_type: str  # 'music', 'sermon', 'announcement', 'slideshow', 'prayer', 'transition'
    confidence: float
    features: Dict[str, Any]
    transcript_segments: List[TranscriptSegment] = None
    
    @property
    def duration(self) -> float:
        return self.end_time - self.start_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        if self.transcript_segments:
            result['transcript_segments'] = [asdict(seg) for seg in self.transcript_segments]
        return result


@dataclass
class ServiceAnalysisResult:
    """Complete analysis result for a church service video."""
    video_path: str
    total_duration: float
    segments: List[ServiceSegment]
    metadata: Dict[str, Any]
    analysis_timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'video_path': self.video_path,
            'total_duration': self.total_duration,
            'segments': [seg.to_dict() for seg in self.segments],
            'metadata': self.metadata,
            'analysis_timestamp': self.analysis_timestamp
        }
    
    def save_to_json(self, output_path: Union[str, Path]) -> None:
        """Save analysis result to JSON file."""
        with open(output_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


class ChurchServiceAnalyzer:
    """
    Main analyzer for church service videos.
    
    Combines audio analysis, visual analysis, and transcript analysis to automatically
    segment and classify different parts of a church service.
    """
    
    def __init__(self, 
                 silence_threshold: float = -40.0,
                 min_segment_duration: float = 30.0,
                 frame_sample_rate: float = 1.0,
                 use_chunked_processing: bool = True,
                 chunk_duration: float = 60.0):
        """
        Initialize the church service analyzer.
        
        Args:
            silence_threshold: RMS threshold for silence detection (dB)
            min_segment_duration: Minimum duration for a segment (seconds)
            frame_sample_rate: Rate to sample frames for visual analysis (fps)
            use_chunked_processing: Use memory-efficient chunked processing
            chunk_duration: Duration of audio chunks for processing (seconds)
        """
        self.silence_threshold = silence_threshold
        self.min_segment_duration = min_segment_duration
        self.frame_sample_rate = frame_sample_rate
        self.use_chunked_processing = use_chunked_processing
        self.chunk_duration = chunk_duration
        
        # Initialize components
        if SilenceDetector is not None:
            self.silence_detector = SilenceDetector(
                threshold_db=silence_threshold,
                min_silence_duration=2.0
            )
        else:
            self.silence_detector = None
            logger.warning("SilenceDetector not available (moviepy not installed)")
        
        self.audio_analyzer = AudioAnalyzer()
        self.transcript_analyzer = TranscriptAnalyzer()
        self.frame_extractor = FrameExtractor()
        
        # Initialize chunked analyzer for large files
        self.chunked_analyzer = ChunkedAudioAnalyzer(
            chunk_duration=chunk_duration,
            sample_rate=22050
        )
        
        # Initialize church audio classifier
        self.audio_classifier = ChurchAudioClassifier()
        
        # Classification model (will be trained/loaded)
        self.classifier = None
        self._initialize_classifier()
    
    def _initialize_classifier(self):
        """Initialize or load the segment classifier."""
        # For now, use a simple rule-based classifier
        # In the future, this could be a trained ML model
        self.classifier = RandomForestClassifier(n_estimators=100, random_state=42)
    
    def analyze_service(self, 
                       video_path: Union[str, Path],
                       transcript_path: Optional[Union[str, Path]] = None,
                       output_dir: Optional[Union[str, Path]] = None) -> ServiceAnalysisResult:
        """
        Perform comprehensive analysis of a church service video.
        
        Args:
            video_path: Path to the video file
            transcript_path: Optional path to transcript/SRT file
            output_dir: Optional output directory for intermediate files
            
        Returns:
            ServiceAnalysisResult with complete analysis
        """
        video_path = Path(video_path)
        logger.info(f"Starting analysis of {video_path}")
        
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # Step 1: Extract basic metadata
        logger.info("Extracting video metadata...")
        metadata = self.chunked_analyzer.extract_audio_metadata(video_path)
        total_duration = metadata['duration']
        
        # Step 2: Process audio (chunked or regular)
        if self.use_chunked_processing:
            logger.info("Using chunked audio processing for large file...")
            service_segments = self._process_audio_chunked(video_path)
            # Skip regular audio processing for chunked mode
            audio_features = None
            audio_segments = []
        else:
            logger.info("Extracting audio features...")
            audio_features = self._extract_audio_features(video_path)
            logger.info("Detecting silence and speech segments...")
            audio_segments = self._detect_audio_segments(video_path)
            service_segments = []
        
        # Step 3: Analyze visual content
        logger.info("Analyzing visual content...")
        visual_features = self._extract_visual_features(video_path)
        
        # Step 4: Process transcript if available
        transcript_segments = []
        if transcript_path:
            logger.info("Processing transcript...")
            transcript_segments = self._process_transcript(transcript_path)
        
        # Step 5: Combine features and classify segments
        if not self.use_chunked_processing:
            logger.info("Classifying service segments...")
            service_segments = self._classify_segments(
                audio_features, audio_segments, visual_features, transcript_segments
            )
        
        # Step 6: Post-process and merge segments
        logger.info("Post-processing segments...")
        final_segments = self._post_process_segments(service_segments)
        
        # Create analysis result
        result = ServiceAnalysisResult(
            video_path=str(video_path),
            total_duration=total_duration,
            segments=final_segments,
            metadata={
                'analysis_version': '1.0',
                'audio_sample_rate': metadata.get('sample_rate', 22050),
                'total_segments': len(final_segments),
                'segment_types': list(set(seg.segment_type for seg in final_segments)),
                'chunked_processing': self.use_chunked_processing
            },
            analysis_timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"Analysis complete. Found {len(final_segments)} segments.")
        return result
    
    def _extract_audio_features(self, video_path: Path) -> AudioFeatures:
        """Extract comprehensive audio features from the video."""
        return self.audio_analyzer.analyze_audio(video_path)
    
    def _process_audio_chunked(self, video_path: Path) -> List[ServiceSegment]:
        """Process audio in chunks to handle large files efficiently."""
        all_segments = []
        
        def analyze_chunk(audio_path: str, start_time: float, end_time: float) -> Dict[str, Any]:
            """Analyze a single audio chunk."""
            # Use the church audio classifier
            chunk_results = self.audio_classifier.analyze_audio_file(
                audio_path,
                segment_length=10.0,  # 10 second sub-segments
                overlap=2.0
            )
            
            # Convert to service segments
            segments = []
            for result in chunk_results:
                # Adjust times to be relative to full video
                adjusted_start = start_time + result.start_time
                adjusted_end = start_time + result.end_time
                
                # Map audio classification to service segment type
                segment_type_map = {
                    'music': 'music',
                    'speech': 'sermon',  # Will be refined later
                    'singing': 'music',
                    'mixed': 'transition',
                    'silence': 'transition'
                }
                
                segment = ServiceSegment(
                    start_time=adjusted_start,
                    end_time=adjusted_end,
                    segment_type=segment_type_map.get(result.classification, 'transition'),
                    confidence=result.confidence,
                    features=result.features
                )
                segments.append(segment)
            
            return {
                'segments': segments,
                'start_time': start_time,
                'end_time': end_time
            }
        
        # Process video in chunks
        chunk_results = self.chunked_analyzer.analyze_video_in_chunks(
            video_path,
            analyze_chunk,
            overlap=5.0
        )
        
        # Merge all segments
        for chunk in chunk_results:
            if 'segments' in chunk:
                all_segments.extend(chunk['segments'])
        
        # Merge overlapping segments
        return self._merge_chunked_segments(all_segments)
    
    def _detect_audio_segments(self, video_path: Path) -> List[AudioSegment]:
        """Detect speech and silence segments in the audio."""
        if self.silence_detector is None:
            # Return a single segment covering the whole video if silence detector not available
            # This is a fallback - actual duration will be determined from audio features
            return [AudioSegment(start=0.0, end=0.0, is_silence=False, rms_power=0.0)]
        return self.silence_detector.detect_silence_segments(str(video_path))
    
    def _extract_visual_features(self, video_path: Path) -> Dict[str, Any]:
        """Extract visual features for scene classification."""
        features = {
            'scene_changes': [],
            'slideshow_probability': [],
            'color_profiles': [],
            'motion_levels': []
        }
        
        try:
            # Sample frames at regular intervals
            cap = cv2.VideoCapture(str(video_path))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps
            
            sample_interval = int(fps / self.frame_sample_rate)
            prev_frame = None
            
            for frame_idx in range(0, frame_count, sample_interval):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if not ret:
                    break
                
                timestamp = frame_idx / fps
                
                # Detect scene changes
                if prev_frame is not None:
                    scene_change_score = self._calculate_scene_change(prev_frame, frame)
                    features['scene_changes'].append((timestamp, scene_change_score))
                
                # Detect slideshow characteristics
                slideshow_prob = self._detect_slideshow_frame(frame)
                features['slideshow_probability'].append((timestamp, slideshow_prob))
                
                # Color profile analysis
                color_profile = self._analyze_color_profile(frame)
                features['color_profiles'].append((timestamp, color_profile))
                
                # Motion analysis
                if prev_frame is not None:
                    motion_level = self._calculate_motion_level(prev_frame, frame)
                    features['motion_levels'].append((timestamp, motion_level))
                
                prev_frame = frame
            
            cap.release()
            
        except Exception as e:
            logger.error(f"Error extracting visual features: {e}")
        
        return features
    
    def _calculate_scene_change(self, frame1: np.ndarray, frame2: np.ndarray) -> float:
        """Calculate scene change score between two frames."""
        # Convert to grayscale and compute histogram difference
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        
        hist1 = cv2.calcHist([gray1], [0], None, [256], [0, 256])
        hist2 = cv2.calcHist([gray2], [0], None, [256], [0, 256])
        
        return cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
    
    def _detect_slideshow_frame(self, frame: np.ndarray) -> float:
        """Detect if a frame likely contains a slideshow/presentation."""
        # Look for text regions, high contrast, geometric shapes
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Text detection using edge density in horizontal regions
        edges = cv2.Canny(gray, 50, 150)
        horizontal_edges = np.sum(edges, axis=1)
        text_score = np.std(horizontal_edges) / (np.mean(horizontal_edges) + 1)
        
        # High contrast regions (typical of slides)
        contrast_score = np.std(gray) / 255.0
        
        # Combine scores
        slideshow_probability = min(1.0, (text_score * 0.7 + contrast_score * 0.3) / 100)
        return slideshow_probability
    
    def _analyze_color_profile(self, frame: np.ndarray) -> Dict[str, float]:
        """Analyze color characteristics of a frame."""
        # Convert to HSV for better color analysis
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        return {
            'brightness': np.mean(hsv[:, :, 2]) / 255.0,
            'saturation': np.mean(hsv[:, :, 1]) / 255.0,
            'hue_variance': np.std(hsv[:, :, 0]) / 180.0
        }
    
    def _calculate_motion_level(self, frame1: np.ndarray, frame2: np.ndarray) -> float:
        """Calculate motion level between two frames."""
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        
        # Calculate optical flow
        flow = cv2.calcOpticalFlowPyrLK(gray1, gray2, None, None)
        if flow[0] is not None:
            motion = np.mean(np.sqrt(flow[0][:, :, 0]**2 + flow[0][:, :, 1]**2))
        else:
            # Fallback: frame difference
            diff = cv2.absdiff(gray1, gray2)
            motion = np.mean(diff) / 255.0
        
        return motion
    
    def _process_transcript(self, transcript_path: Path) -> List[TranscriptSegment]:
        """Process transcript file to extract segments."""
        return self.transcript_analyzer.load_transcript(str(transcript_path))
    
    def _classify_segments(self, 
                          audio_features: AudioFeatures,
                          audio_segments: List[AudioSegment],
                          visual_features: Dict[str, Any],
                          transcript_segments: List[TranscriptSegment]) -> List[ServiceSegment]:
        """Classify segments based on combined audio-visual features."""
        segments = []
        
        # Combine audio segments with visual analysis
        for audio_seg in audio_segments:
            if audio_seg.is_silence or audio_seg.duration < self.min_segment_duration:
                continue
            
            # Extract features for this time range
            features = self._extract_segment_features(
                audio_seg, audio_features, visual_features, transcript_segments
            )
            
            # Classify segment type
            segment_type, confidence = self._classify_segment_type(features)
            
            # Find relevant transcript segments
            relevant_transcript = [
                ts for ts in transcript_segments
                if ts.start_time >= audio_seg.start and ts.end_time <= audio_seg.end
            ]
            
            segment = ServiceSegment(
                start_time=audio_seg.start,
                end_time=audio_seg.end,
                segment_type=segment_type,
                confidence=confidence,
                features=features,
                transcript_segments=relevant_transcript
            )
            segments.append(segment)
        
        return segments
    
    def _extract_segment_features(self, 
                                 audio_seg: AudioSegment,
                                 audio_features: AudioFeatures,
                                 visual_features: Dict[str, Any],
                                 transcript_segments: List[TranscriptSegment]) -> Dict[str, Any]:
        """Extract features for a specific segment."""
        features = {
            'duration': audio_seg.duration,
            'rms_power': audio_seg.rms_power,
            'audio_energy': 0.0,
            'spectral_centroid': 0.0,
            'zero_crossing_rate': 0.0,
            'slideshow_probability': 0.0,
            'scene_changes': 0,
            'motion_level': 0.0,
            'speech_ratio': 0.0,
            'word_count': 0
        }
        
        # Audio features (simplified - would need frame-level analysis)
        if hasattr(audio_features, 'tempo'):
            features['tempo'] = audio_features.tempo
        
        # Visual features in this time range
        for timestamp, slideshow_prob in visual_features.get('slideshow_probability', []):
            if audio_seg.start <= timestamp <= audio_seg.end:
                features['slideshow_probability'] = max(
                    features['slideshow_probability'], slideshow_prob
                )
        
        # Scene changes in this time range
        scene_change_count = 0
        for timestamp, scene_change in visual_features.get('scene_changes', []):
            if audio_seg.start <= timestamp <= audio_seg.end and scene_change < 0.8:
                scene_change_count += 1
        features['scene_changes'] = scene_change_count
        
        # Motion level
        motion_levels = [
            motion for timestamp, motion in visual_features.get('motion_levels', [])
            if audio_seg.start <= timestamp <= audio_seg.end
        ]
        if motion_levels:
            features['motion_level'] = np.mean(motion_levels)
        
        # Transcript features
        segment_transcript = [
            ts for ts in transcript_segments
            if ts.start_time >= audio_seg.start and ts.end_time <= audio_seg.end
        ]
        
        if segment_transcript:
            total_words = sum(len(ts.text.split()) for ts in segment_transcript)
            speech_duration = sum(ts.duration for ts in segment_transcript)
            features['word_count'] = total_words
            features['speech_ratio'] = speech_duration / audio_seg.duration
        
        return features
    
    def _classify_segment_type(self, features: Dict[str, Any]) -> Tuple[str, float]:
        """Classify segment type based on features using rule-based approach."""
        # Rule-based classification (can be replaced with ML model)
        
        # High slideshow probability = slideshow
        if features['slideshow_probability'] > 0.6:
            return 'slideshow', features['slideshow_probability']
        
        # Low speech ratio + high motion = music
        if features['speech_ratio'] < 0.3 and features['motion_level'] > 0.1:
            return 'music', 0.8
        
        # High speech ratio + long duration = sermon
        if features['speech_ratio'] > 0.7 and features['duration'] > 300:  # 5+ minutes
            return 'sermon', 0.9
        
        # Medium speech ratio + shorter duration = announcement
        if features['speech_ratio'] > 0.5 and features['duration'] < 300:
            return 'announcement', 0.7
        
        # Low speech ratio + low motion = prayer/quiet time
        if features['speech_ratio'] < 0.4 and features['motion_level'] < 0.05:
            return 'prayer', 0.6
        
        # Default to transition
        return 'transition', 0.5
    
    def _post_process_segments(self, segments: List[ServiceSegment]) -> List[ServiceSegment]:
        """Post-process segments to merge similar adjacent segments and clean up."""
        if not segments:
            return []
        
        # Sort by start time
        segments.sort(key=lambda x: x.start_time)
        
        # Merge similar adjacent segments
        merged_segments = [segments[0]]
        
        for current_seg in segments[1:]:
            last_seg = merged_segments[-1]
            
            # Check if segments should be merged
            if (current_seg.segment_type == last_seg.segment_type and
                current_seg.start_time - last_seg.end_time < 60 and  # Gap < 1 minute
                abs(current_seg.confidence - last_seg.confidence) < 0.3):
                
                # Merge segments
                merged_seg = ServiceSegment(
                    start_time=last_seg.start_time,
                    end_time=current_seg.end_time,
                    segment_type=last_seg.segment_type,
                    confidence=(last_seg.confidence + current_seg.confidence) / 2,
                    features=last_seg.features,  # Keep first segment's features
                    transcript_segments=(last_seg.transcript_segments or []) + 
                                      (current_seg.transcript_segments or [])
                )
                merged_segments[-1] = merged_seg
            else:
                merged_segments.append(current_seg)
        
        return merged_segments
    
    def _merge_chunked_segments(self, segments: List[ServiceSegment]) -> List[ServiceSegment]:
        """Merge segments from chunked processing."""
        if not segments:
            return []
        
        # Sort by start time
        segments.sort(key=lambda x: x.start_time)
        
        merged = [segments[0]]
        
        for current in segments[1:]:
            last = merged[-1]
            
            # Check if segments should be merged (same type and close in time)
            time_gap = current.start_time - last.end_time
            
            if (current.segment_type == last.segment_type and 
                time_gap < 5.0 and  # Less than 5 second gap
                abs(current.confidence - last.confidence) < 0.3):
                
                # Extend the last segment
                last.end_time = current.end_time
                last.confidence = (last.confidence + current.confidence) / 2
            else:
                merged.append(current)
        
        # Filter out very short segments
        filtered = [seg for seg in merged if seg.duration >= 5.0]
        
        return filtered


def analyze_church_service_cli(video_path: str, 
                              transcript_path: str = None,
                              output_path: str = None) -> None:
    """CLI function for church service analysis."""
    analyzer = ChurchServiceAnalyzer()
    
    result = analyzer.analyze_service(
        video_path=video_path,
        transcript_path=transcript_path
    )
    
    # Print summary
    print(f"\nChurch Service Analysis Results")
    print(f"Video: {result.video_path}")
    print(f"Total Duration: {result.total_duration:.1f} seconds")
    print(f"Segments Found: {len(result.segments)}")
    print("\nSegment Breakdown:")
    
    for i, segment in enumerate(result.segments):
        print(f"{i+1}. {segment.segment_type.title()} "
              f"({segment.start_time:.1f}s - {segment.end_time:.1f}s) "
              f"[{segment.duration:.1f}s] (confidence: {segment.confidence:.2f})")
    
    # Save to file if requested
    if output_path:
        result.save_to_json(output_path)
        print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze church service video")
    parser.add_argument("video_path", help="Path to video file")
    parser.add_argument("--transcript", help="Path to transcript/SRT file")
    parser.add_argument("--output", help="Output JSON file path")
    
    args = parser.parse_args()
    
    analyze_church_service_cli(args.video_path, args.transcript, args.output)