"""Song structure detection and analysis module.

This module provides tools for analyzing song structure in two formats:
1. Time-based sections (intro at 0:00-0:30)
2. Bar-based sections (verse at bars 17-48)
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict, Union, Tuple
import json
import yaml
from pathlib import Path
import librosa
import numpy as np
import logging
from scipy import signal
from scipy.signal import convolve2d

logger = logging.getLogger(__name__)


class SectionType(Enum):
    """Song section types."""
    INTRO = "intro"
    VERSE = "verse"
    PRECHORUS = "prechorus"
    CHORUS = "chorus"
    BRIDGE = "bridge"
    INSTRUMENTAL = "instrumental"
    OUTRO = "outro"
    DROP = "drop"
    BUILDUP = "buildup"
    BREAKDOWN = "breakdown"
    HOOK = "hook"
    REFRAIN = "refrain"
    SOLO = "solo"
    INTERLUDE = "interlude"
    AD_LIB = "ad_lib"
    VAMP = "vamp"
    TAG = "tag"
    CODA = "coda"


@dataclass
class TimeSection:
    """Time-based section definition."""
    section_type: SectionType
    start_time: float
    end_time: float
    name: Optional[str] = None
    
    @property
    def duration(self) -> float:
        return self.end_time - self.start_time


@dataclass
class BarSection:
    """Bar-based section definition."""
    section_type: SectionType
    start_bar: int
    end_bar: int
    name: Optional[str] = None
    
    @property
    def bar_count(self) -> int:
        return self.end_bar - self.start_bar + 1
    
    def to_time_section(self, tempo: float, time_signature: Tuple[int, int] = (4, 4)) -> TimeSection:
        """Convert bar-based section to time-based using tempo."""
        beats_per_bar = time_signature[0]
        seconds_per_beat = 60.0 / tempo
        seconds_per_bar = beats_per_bar * seconds_per_beat
        
        start_time = (self.start_bar - 1) * seconds_per_bar
        end_time = self.end_bar * seconds_per_bar
        
        return TimeSection(
            section_type=self.section_type,
            start_time=start_time,
            end_time=end_time,
            name=self.name
        )


class SongStructureAnalyzer:
    """Analyzes and manages song structure."""
    
    def __init__(self):
        self.sections: List[Union[TimeSection, BarSection]] = []
        self.tempo: Optional[float] = None
        self.time_signature: Tuple[int, int] = (4, 4)
        
    def analyze_audio(self, audio_path: str, song_structure: Optional[List[Tuple[str, int]]] = None) -> Dict:
        """Analyze audio file to detect structure.
        
        Args:
            audio_path: Path to audio file
            song_structure: Optional predefined structure as list of (section_name, bars) tuples
        """
        logger.info(f"Analyzing audio structure: {audio_path}")
        
        # Load audio
        y, sr = librosa.load(audio_path)
        duration = len(y) / sr
        
        # Detect tempo and beats
        tempo_raw, beats = librosa.beat.beat_track(y=y, sr=sr)
        
        # Extract scalar tempo value
        if isinstance(tempo_raw, np.ndarray):
            self.tempo = float(tempo_raw.flatten()[0]) if tempo_raw.size > 0 else 120.0
        else:
            self.tempo = float(tempo_raw)
        
        # Get beat times
        beat_times = librosa.frames_to_time(beats, sr=sr)
        
        if song_structure:
            # Use instrumental-guided detection with predefined structure
            logger.info("Using instrumental-guided boundary detection")
            
            # Detect raw boundaries
            raw_boundaries = self._detect_boundaries_instrumental(y, sr)
            
            # Smart boundary mapping
            boundary_mapping = self._map_boundaries_with_confidence(
                raw_boundaries, song_structure, self.tempo
            )
            
            # Create final section mapping with confidence threshold
            final_sections = self._create_final_section_mapping(
                boundary_mapping, song_structure, confidence_threshold=0.75
            )
            
            # Create sections from final mapping
            time_sections = []
            bar_sections = []
            
            for i, section_data in enumerate(final_sections):
                section_name = section_data['name']
                bars = section_data['bars']
                start_time = section_data['start_time']
                
                # Calculate end time
                if i < len(final_sections) - 1:
                    end_time = final_sections[i + 1]['start_time']
                else:
                    # For last section, use expected duration
                    seconds_per_bar = (60.0 / self.tempo) * 4
                    end_time = start_time + (bars * seconds_per_bar)
                    end_time = min(end_time, duration)  # Don't exceed audio duration
                
                section_type = self._map_name_to_type(section_name)
                
                # Create time section
                time_sections.append(TimeSection(
                    section_type=section_type,
                    start_time=start_time,
                    end_time=end_time,
                    name=section_name
                ))
                
                # Create bar section
                start_bar = sum(s['bars'] for s in final_sections[:i]) + 1
                end_bar = start_bar + bars - 1
                
                bar_sections.append(BarSection(
                    section_type=section_type,
                    start_bar=start_bar,
                    end_bar=end_bar,
                    name=section_name
                ))
                
                logger.info(f"{section_name:15} → {start_time:6.1f}s [{section_data['source']}]")
            
            # Store confidence info for display
            self._confidence_info = {
                'high_confidence_count': sum(1 for s in final_sections if 'DETECTED' in s['source']),
                'expected_count': sum(1 for s in final_sections if 'EXPECTED' in s['source']),
                'total_sections': len(final_sections),
                'section_sources': [s['source'] for s in final_sections]
            }
        else:
            # Fallback to basic detection
            logger.info("Using basic automatic section detection")
            segments = self._detect_segments(y, sr)
            time_sections = self._segments_to_sections(segments, duration)
            bar_sections = self._time_to_bar_sections(time_sections, self.tempo) if self.tempo else []
        
        return {
            'tempo': self.tempo,
            'time_signature': self.time_signature,
            'time_sections': time_sections,
            'bar_sections': bar_sections,
            'beat_times': beat_times.tolist()
        }
    
    def _detect_segments(self, y: np.ndarray, sr: int) -> List[Tuple[float, float]]:
        """Detect segment boundaries using spectral analysis."""
        # Compute spectral features
        hop_length = 512
        chroma = librosa.feature.chroma_stft(y=y, sr=sr, hop_length=hop_length)
        mfcc = librosa.feature.mfcc(y=y, sr=sr, hop_length=hop_length)
        
        # Stack features
        features = np.vstack([chroma, mfcc])
        
        # Compute self-similarity matrix
        similarity = librosa.segment.recurrence_matrix(features, mode='affinity')
        
        # Detect boundaries
        boundaries = librosa.segment.agglomerative(features, k=10)
        boundary_times = librosa.frames_to_time(boundaries, sr=sr, hop_length=hop_length)
        
        # Create segments
        segments = []
        for i in range(len(boundary_times) - 1):
            segments.append((boundary_times[i], boundary_times[i + 1]))
        
        return segments
    
    def _detect_boundaries_instrumental(self, y: np.ndarray, sr: int) -> np.ndarray:
        """Detect section boundaries using instrumental audio features."""
        # OPTIMIZATION: Use coarser hop length for section-level analysis
        hop_length = 4096  # Coarse for faster computation
        
        # Extract features
        rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
        cent = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop_length)[0]
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop_length)
        onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)
        
        # Compute self-similarity matrix
        chroma_sim = librosa.segment.recurrence_matrix(chroma, mode='affinity')
        
        # Detect novelty from multiple features
        # 1. RMS novelty
        rms_diff = np.diff(rms)
        rms_novelty = np.abs(rms_diff)
        
        # 2. Spectral novelty
        cent_diff = np.diff(cent)
        cent_novelty = np.abs(cent_diff)
        
        # 3. Harmonic novelty (from self-similarity)
        kernel_size = 8
        kernel = np.outer(
            np.concatenate([np.ones(kernel_size//2), -np.ones(kernel_size//2)]),
            np.concatenate([np.ones(kernel_size//2), -np.ones(kernel_size//2)])
        )
        
        novelty_2d = convolve2d(chroma_sim, kernel, mode='same')
        rec_novelty = np.sum(np.abs(novelty_2d), axis=0)
        
        # Normalize novelty curves
        rms_novelty = (rms_novelty - np.mean(rms_novelty)) / (np.std(rms_novelty) + 1e-8)
        cent_novelty = (cent_novelty - np.mean(cent_novelty)) / (np.std(cent_novelty) + 1e-8)
        rec_novelty = (rec_novelty - np.mean(rec_novelty)) / (np.std(rec_novelty) + 1e-8)
        
        # Combine
        min_len = min(len(rms_novelty), len(cent_novelty), len(rec_novelty))
        combined_novelty = (rms_novelty[:min_len] + cent_novelty[:min_len] + rec_novelty[:min_len]) / 3
        
        # Smooth
        combined_novelty = signal.medfilt(combined_novelty, kernel_size=5)
        
        # Find peaks
        peaks, properties = signal.find_peaks(
            combined_novelty, 
            height=np.percentile(combined_novelty, 75),
            distance=int(2 * sr / hop_length)
        )
        
        # Convert to time
        boundary_times = librosa.frames_to_time(peaks, sr=sr, hop_length=hop_length)
        
        # Add start and end
        duration = len(y) / sr
        all_boundaries = np.concatenate([[0], boundary_times, [duration]])
        
        return all_boundaries
    
    def _smart_boundary_mapping(self, detected_boundaries: np.ndarray, song_structure: List[Tuple[str, int]], tempo: float) -> Tuple[np.ndarray, np.ndarray]:
        """Map detected boundaries to expected song structure intelligently."""
        # Calculate expected boundaries
        seconds_per_bar = (60.0 / tempo) * 4
        expected_boundaries = [0.0]
        current_time = 0.0
        
        for section, bars in song_structure:
            current_time += bars * seconds_per_bar
            expected_boundaries.append(current_time)
        
        # Filter detected boundaries - remove those too close together
        min_section_duration = 6.0  # ~4 bars at 140 BPM
        filtered_detected = [detected_boundaries[0]]
        
        for boundary in detected_boundaries[1:]:
            if boundary - filtered_detected[-1] >= min_section_duration:
                filtered_detected.append(boundary)
        
        logger.info(f"Filtered to {len(filtered_detected)} boundaries (removed short segments)")
        
        # Map filtered boundaries to expected structure
        final_boundaries = []
        tolerance = 3.0  # seconds
        
        for i, expected_time in enumerate(expected_boundaries[:-1]):
            # Find closest detected boundary within tolerance
            candidates = [b for b in filtered_detected if abs(b - expected_time) <= tolerance]
            
            if candidates:
                # Use the closest one
                closest = min(candidates, key=lambda x: abs(x - expected_time))
                final_boundaries.append(closest)
            else:
                # Use expected time if no detection nearby
                final_boundaries.append(expected_time)
        
        # Always add the end
        final_boundaries.append(detected_boundaries[-1])
        
        return np.array(final_boundaries), np.array(expected_boundaries)
    
    def _map_boundaries_with_confidence(self, detected_boundaries: np.ndarray, 
                                      song_structure: List[Tuple[str, int]], 
                                      tempo: float, tolerance_seconds: float = 3.0) -> Dict:
        """Map detected boundaries to expected structure with confidence scores."""
        # Calculate expected boundaries
        seconds_per_bar = (60.0 / tempo) * 4
        expected_boundaries = [0.0]
        current_time = 0.0
        
        for section, bars in song_structure:
            current_time += bars * seconds_per_bar
            expected_boundaries.append(current_time)
        
        # Create mapping with confidence scores
        mapping = {}
        used_detections = set()
        
        for i, exp_time in enumerate(expected_boundaries[:-1]):
            best_match = None
            best_distance = float('inf')
            
            for j, det_time in enumerate(detected_boundaries):
                if j in used_detections:
                    continue
                    
                distance = abs(det_time - exp_time)
                if distance < best_distance and distance <= tolerance_seconds:
                    best_distance = distance
                    best_match = j
            
            if best_match is not None:
                used_detections.add(best_match)
                mapping[i] = {
                    'expected_time': exp_time,
                    'detected_time': detected_boundaries[best_match],
                    'detected_index': best_match,
                    'error': best_distance,
                    'confidence': 1.0 - (best_distance / tolerance_seconds)
                }
            else:
                mapping[i] = {
                    'expected_time': exp_time,
                    'detected_time': None,
                    'detected_index': None,
                    'error': None,
                    'confidence': 0.0
                }
        
        return mapping
    
    def _create_final_section_mapping(self, boundary_mapping: Dict, 
                                    song_structure: List[Tuple[str, int]], 
                                    confidence_threshold: float = 0.75) -> List[Dict]:
        """Create final section times using detected boundaries when confident."""
        logger.info(f"Creating final section mapping (confidence threshold: {confidence_threshold:.0%})")
        
        final_sections = []
        high_confidence_count = 0
        
        for i, (section, bars) in enumerate(song_structure):
            if i in boundary_mapping:
                m = boundary_mapping[i]
                
                # Use detected if high confidence, otherwise use expected
                if m['confidence'] >= confidence_threshold and m['detected_time'] is not None:
                    final_time = m['detected_time']
                    source = f"DETECTED ({m['confidence']:.0%})"
                    high_confidence_count += 1
                else:
                    final_time = m['expected_time']
                    source = "EXPECTED"
                
                final_sections.append({
                    'name': section,
                    'bars': bars,
                    'start_time': final_time,
                    'source': source,
                    'confidence': m['confidence']
                })
        
        logger.info(f"Using {high_confidence_count}/{len(song_structure)} detected boundaries")
        logger.info(f"{len(song_structure) - high_confidence_count} sections will use expected timing")
        
        return final_sections
    
    def _segments_to_sections(self, segments: List[Tuple[float, float]], duration: float) -> List[TimeSection]:
        """Convert raw segments to labeled sections."""
        sections = []
        
        # Simple heuristic-based labeling
        for i, (start, end) in enumerate(segments):
            # First segment is likely intro
            if i == 0 and start < 10:
                section_type = SectionType.INTRO
            # Last segment is likely outro
            elif i == len(segments) - 1 and end > duration - 20:
                section_type = SectionType.OUTRO
            # Middle segments alternate between verse and chorus (simplified)
            else:
                section_type = SectionType.VERSE if i % 2 == 1 else SectionType.CHORUS
            
            sections.append(TimeSection(
                section_type=section_type,
                start_time=start,
                end_time=end
            ))
        
        return sections
    
    def _time_to_bar_sections(self, time_sections: List[TimeSection], tempo: float) -> List[BarSection]:
        """Convert time-based sections to bar-based."""
        bar_sections = []
        beats_per_bar = self.time_signature[0]
        seconds_per_beat = 60.0 / tempo
        seconds_per_bar = beats_per_bar * seconds_per_beat
        
        for section in time_sections:
            start_bar = int(section.start_time / seconds_per_bar) + 1
            end_bar = int(section.end_time / seconds_per_bar)
            
            bar_sections.append(BarSection(
                section_type=section.section_type,
                start_bar=start_bar,
                end_bar=end_bar,
                name=section.name
            ))
        
        return bar_sections
    
    def load_from_file(self, file_path: str) -> None:
        """Load structure from JSON or YAML file."""
        path = Path(file_path)
        
        if path.suffix == '.json':
            with open(path, 'r') as f:
                data = json.load(f)
        elif path.suffix in ['.yaml', '.yml']:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")
        
        self._load_from_dict(data)
    
    def _map_name_to_type(self, name: str) -> SectionType:
        """Map section name to SectionType enum."""
        name_lower = name.lower().strip()
        
        # Remove numbers and clean up
        name_clean = name_lower.replace(' 1', '').replace(' 2', '').replace(' 3', '')
        
        # Direct mappings
        mappings = {
            'intro': SectionType.INTRO,
            'verse': SectionType.VERSE,
            'chorus': SectionType.CHORUS,
            'bridge': SectionType.BRIDGE,
            'outro': SectionType.OUTRO,
            'instrumental': SectionType.INSTRUMENTAL,
            'interlude': SectionType.INTERLUDE,
            'pre-chorus': SectionType.PRECHORUS,
            'prechorus': SectionType.PRECHORUS,
            'drop': SectionType.DROP,
            'buildup': SectionType.BUILDUP,
            'breakdown': SectionType.BREAKDOWN,
            'hook': SectionType.HOOK,
            'refrain': SectionType.REFRAIN,
            'solo': SectionType.SOLO,
            'ad lib': SectionType.AD_LIB,
            'ad-lib': SectionType.AD_LIB,
            'vamp': SectionType.VAMP,
            'tag': SectionType.TAG,
            'coda': SectionType.CODA
        }
        
        return mappings.get(name_clean, SectionType.VERSE)
    
    def _load_from_dict(self, data: Dict) -> None:
        """Load structure from dictionary."""
        self.tempo = data.get('tempo')
        self.time_signature = tuple(data.get('time_signature', [4, 4]))
        
        self.sections = []
        
        # Load bar-based sections
        if 'bar_sections' in data:
            for section_data in data['bar_sections']:
                self.sections.append(BarSection(
                    section_type=SectionType(section_data['type'].lower()),
                    start_bar=section_data['start_bar'],
                    end_bar=section_data['end_bar'],
                    name=section_data.get('name')
                ))
        
        # Load time-based sections
        if 'time_sections' in data:
            for section_data in data['time_sections']:
                self.sections.append(TimeSection(
                    section_type=SectionType(section_data['type'].lower()),
                    start_time=section_data['start_time'],
                    end_time=section_data['end_time'],
                    name=section_data.get('name')
                ))
    
    def save_to_file(self, file_path: str) -> None:
        """Save structure to JSON or YAML file."""
        data = self.to_dict()
        path = Path(file_path)
        
        if path.suffix == '.json':
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
        elif path.suffix in ['.yaml', '.yml']:
            with open(path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")
        
        # Also save lyric video format if we have time sections
        if 'time_sections' in data and data['time_sections']:
            self._save_lyric_video_format(path)
    
    def _save_lyric_video_format(self, original_path: Path) -> None:
        """Save a companion file in video sections format."""
        # Create filename for video sections format
        lyric_video_path = original_path.parent / f"{original_path.stem}_video_sections.json"
        
        # Create lyric video format sections
        lyric_sections = []
        time_sections = [s for s in self.sections if hasattr(s, 'start_time')]
        
        for section in sorted(time_sections, key=lambda s: s.start_time):
            # Don't map! Use the original type directly
            lyric_sections.append({
                'name': section.name or section.section_type.value,
                'start': round(section.start_time, 2),
                'end': round(section.end_time, 2),
                'type': section.section_type.value  # Use original type!
            })
        
        # Save to file
        lyric_video_data = {'sections': lyric_sections}
        with open(lyric_video_path, 'w') as f:
            json.dump(lyric_video_data, f, indent=2)
        
        logger.info(f"Saved video sections format to: {lyric_video_path}")
    
    def to_dict(self) -> Dict:
        """Convert structure to dictionary."""
        bar_sections = []
        time_sections = []
        
        for section in self.sections:
            if isinstance(section, BarSection):
                bar_sections.append({
                    'type': section.section_type.value,
                    'start_bar': section.start_bar,
                    'end_bar': section.end_bar,
                    'name': section.name
                })
            elif isinstance(section, TimeSection):
                time_sections.append({
                    'type': section.section_type.value,
                    'start_time': section.start_time,
                    'end_time': section.end_time,
                    'name': section.name
                })
        
        return {
            'tempo': self.tempo,
            'time_signature': list(self.time_signature),
            'bar_sections': bar_sections,
            'time_sections': time_sections
        }
    
    def get_section_at_time(self, time: float) -> Optional[Union[TimeSection, BarSection]]:
        """Get the section at a given time."""
        for section in self.sections:
            if isinstance(section, TimeSection):
                if section.start_time <= time < section.end_time:
                    return section
            elif isinstance(section, BarSection) and self.tempo:
                time_section = section.to_time_section(self.tempo, self.time_signature)
                if time_section.start_time <= time < time_section.end_time:
                    return section
        return None
    
    def get_section_at_bar(self, bar: int) -> Optional[BarSection]:
        """Get the section at a given bar number."""
        for section in self.sections:
            if isinstance(section, BarSection):
                if section.start_bar <= bar <= section.end_bar:
                    return section
        return None