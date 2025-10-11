"""
Church Service Audio Classification Module

Specialized audio analysis for distinguishing between music, speech, and other
audio content in church services.
"""

import numpy as np
import librosa
import librosa.feature
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import logging
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class AudioClassificationResult:
    """Result of audio classification for a segment."""
    start_time: float
    end_time: float
    classification: str  # 'music', 'speech', 'singing', 'mixed', 'silence'
    confidence: float
    features: Dict[str, float]


class ChurchAudioClassifier:
    """
    Specialized audio classifier for church service content.
    
    Distinguishes between:
    - Music (instrumental)
    - Speech (sermon, announcements)
    - Singing (congregational/choir)
    - Mixed content
    - Silence/ambient
    """
    
    def __init__(self, sample_rate: int = 22050, hop_length: int = 512):
        """
        Initialize the audio classifier.
        
        Args:
            sample_rate: Audio sample rate for analysis
            hop_length: Hop length for STFT analysis
        """
        self.sample_rate = sample_rate
        self.hop_length = hop_length
        self.n_fft = 2048
        
        # Classification model
        self.classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        
        # Feature configuration
        self.feature_config = {
            'mfcc_coeffs': 13,
            'chroma_bins': 12,
            'spectral_contrast_bands': 7,
            'tonnetz_dims': 6
        }
    
    def extract_features(self, 
                        audio_segment: np.ndarray, 
                        sr: Optional[int] = None) -> Dict[str, float]:
        """
        Extract comprehensive audio features for classification.
        
        Args:
            audio_segment: Audio data
            sr: Sample rate (uses self.sample_rate if None)
            
        Returns:
            Dictionary of extracted features
        """
        if sr is None:
            sr = self.sample_rate
        
        features = {}
        
        try:
            # Ensure audio is not empty
            if len(audio_segment) == 0:
                return self._get_empty_features()
            
            # Basic spectral features
            spectral_centroids = librosa.feature.spectral_centroid(
                y=audio_segment, sr=sr, hop_length=self.hop_length
            )[0]
            features['spectral_centroid_mean'] = np.mean(spectral_centroids)
            features['spectral_centroid_std'] = np.std(spectral_centroids)
            
            # Spectral rolloff
            spectral_rolloff = librosa.feature.spectral_rolloff(
                y=audio_segment, sr=sr, hop_length=self.hop_length
            )[0]
            features['spectral_rolloff_mean'] = np.mean(spectral_rolloff)
            features['spectral_rolloff_std'] = np.std(spectral_rolloff)
            
            # Zero crossing rate (indicates speech vs music)
            zcr = librosa.feature.zero_crossing_rate(
                y=audio_segment, hop_length=self.hop_length
            )[0]
            features['zcr_mean'] = np.mean(zcr)
            features['zcr_std'] = np.std(zcr)
            
            # MFCCs (good for speech/music distinction)
            mfccs = librosa.feature.mfcc(
                y=audio_segment, sr=sr, 
                n_mfcc=self.feature_config['mfcc_coeffs'],
                hop_length=self.hop_length
            )
            for i in range(self.feature_config['mfcc_coeffs']):
                features[f'mfcc_{i}_mean'] = np.mean(mfccs[i])
                features[f'mfcc_{i}_std'] = np.std(mfccs[i])
            
            # Chroma features (harmonic content - good for music/singing)
            chroma = librosa.feature.chroma_stft(
                y=audio_segment, sr=sr, hop_length=self.hop_length
            )
            features['chroma_mean'] = np.mean(chroma)
            features['chroma_std'] = np.std(chroma)
            features['chroma_var'] = np.var(chroma)
            
            # Spectral contrast (timbral characteristics)
            contrast = librosa.feature.spectral_contrast(
                y=audio_segment, sr=sr, hop_length=self.hop_length
            )
            features['spectral_contrast_mean'] = np.mean(contrast)
            features['spectral_contrast_std'] = np.std(contrast)
            
            # Tonnetz (harmonic network - musical structure)
            tonnetz = librosa.feature.tonnetz(
                y=librosa.effects.harmonic(audio_segment), sr=sr
            )
            features['tonnetz_mean'] = np.mean(tonnetz)
            features['tonnetz_std'] = np.std(tonnetz)
            
            # Tempo and beat features
            try:
                tempo, beats = librosa.beat.beat_track(
                    y=audio_segment, sr=sr, hop_length=self.hop_length
                )
                features['tempo'] = tempo
                features['beat_strength'] = np.mean(librosa.onset.onset_strength(
                    y=audio_segment, sr=sr
                ))
            except:
                features['tempo'] = 0.0
                features['beat_strength'] = 0.0
            
            # RMS energy
            rms = librosa.feature.rms(
                y=audio_segment, hop_length=self.hop_length
            )[0]
            features['rms_mean'] = np.mean(rms)
            features['rms_std'] = np.std(rms)
            
            # Spectral bandwidth
            bandwidth = librosa.feature.spectral_bandwidth(
                y=audio_segment, sr=sr, hop_length=self.hop_length
            )[0]
            features['bandwidth_mean'] = np.mean(bandwidth)
            features['bandwidth_std'] = np.std(bandwidth)
            
            # Harmonic-percussive separation features
            harmonic, percussive = librosa.effects.hpss(audio_segment)
            features['harmonic_ratio'] = np.mean(np.abs(harmonic)) / (
                np.mean(np.abs(audio_segment)) + 1e-8
            )
            features['percussive_ratio'] = np.mean(np.abs(percussive)) / (
                np.mean(np.abs(audio_segment)) + 1e-8
            )
            
            # Pitch-related features
            try:
                pitches, magnitudes = librosa.piptrack(
                    y=audio_segment, sr=sr, hop_length=self.hop_length
                )
                pitch_values = []
                for t in range(pitches.shape[1]):
                    index = magnitudes[:, t].argmax()
                    pitch = pitches[index, t]
                    if pitch > 0:
                        pitch_values.append(pitch)
                
                if pitch_values:
                    features['pitch_mean'] = np.mean(pitch_values)
                    features['pitch_std'] = np.std(pitch_values)
                    features['pitch_range'] = max(pitch_values) - min(pitch_values)
                else:
                    features['pitch_mean'] = 0.0
                    features['pitch_std'] = 0.0
                    features['pitch_range'] = 0.0
            except:
                features['pitch_mean'] = 0.0
                features['pitch_std'] = 0.0
                features['pitch_range'] = 0.0
            
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return self._get_empty_features()
        
        return features
    
    def _get_empty_features(self) -> Dict[str, float]:
        """Return empty feature dictionary for error cases."""
        feature_names = [
            'spectral_centroid_mean', 'spectral_centroid_std',
            'spectral_rolloff_mean', 'spectral_rolloff_std',
            'zcr_mean', 'zcr_std',
            'chroma_mean', 'chroma_std', 'chroma_var',
            'spectral_contrast_mean', 'spectral_contrast_std',
            'tonnetz_mean', 'tonnetz_std',
            'tempo', 'beat_strength',
            'rms_mean', 'rms_std',
            'bandwidth_mean', 'bandwidth_std',
            'harmonic_ratio', 'percussive_ratio',
            'pitch_mean', 'pitch_std', 'pitch_range'
        ]
        
        # Add MFCC features
        for i in range(self.feature_config['mfcc_coeffs']):
            feature_names.extend([f'mfcc_{i}_mean', f'mfcc_{i}_std'])
        
        return {name: 0.0 for name in feature_names}
    
    def classify_audio_segment(self, 
                              audio_segment: np.ndarray,
                              start_time: float,
                              end_time: float,
                              sr: Optional[int] = None) -> AudioClassificationResult:
        """
        Classify a single audio segment.
        
        Args:
            audio_segment: Audio data
            start_time: Start time of segment
            end_time: End time of segment
            sr: Sample rate
            
        Returns:
            AudioClassificationResult with classification and confidence
        """
        if sr is None:
            sr = self.sample_rate
        
        # Extract features
        features = self.extract_features(audio_segment, sr)
        
        # Rule-based classification (can be enhanced with ML model)
        classification, confidence = self._rule_based_classification(features)
        
        return AudioClassificationResult(
            start_time=start_time,
            end_time=end_time,
            classification=classification,
            confidence=confidence,
            features=features
        )
    
    def _rule_based_classification(self, features: Dict[str, float]) -> Tuple[str, float]:
        """
        Rule-based classification for church service audio.
        
        Args:
            features: Extracted audio features
            
        Returns:
            Tuple of (classification, confidence)
        """
        # Check for silence first
        if features['rms_mean'] < 0.01:
            return 'silence', 0.9
        
        # Music detection rules
        music_score = 0.0
        speech_score = 0.0
        singing_score = 0.0
        
        # High harmonic content suggests music/singing
        if features['harmonic_ratio'] > 0.7:
            music_score += 0.3
            singing_score += 0.2
        
        # Regular beat pattern suggests music
        if features['beat_strength'] > 0.1 and features['tempo'] > 60:
            music_score += 0.3
        
        # High chroma variance suggests harmonic complexity (music)
        if features['chroma_var'] > 0.1:
            music_score += 0.2
            singing_score += 0.1
        
        # Zero crossing rate patterns
        if features['zcr_mean'] > 0.1:
            speech_score += 0.4  # Speech has higher ZCR
        elif features['zcr_mean'] < 0.05:
            music_score += 0.2   # Music has lower ZCR
        
        # Spectral centroid patterns
        if 1000 < features['spectral_centroid_mean'] < 3000:
            speech_score += 0.3  # Speech frequency range
        elif features['spectral_centroid_mean'] < 2000:
            music_score += 0.2   # Music often has lower centroid
        
        # Pitch stability (singing has more stable pitch than speech)
        if features['pitch_std'] > 0 and features['pitch_std'] < 100:
            singing_score += 0.3
        elif features['pitch_std'] > 200:
            speech_score += 0.2
        
        # MFCC patterns (simplified)
        mfcc_1_mean = features.get('mfcc_1_mean', 0)
        if abs(mfcc_1_mean) > 10:
            speech_score += 0.2
        
        # Determine classification
        scores = {
            'music': music_score,
            'speech': speech_score,
            'singing': singing_score
        }
        
        best_class = max(scores, key=scores.get)
        best_score = scores[best_class]
        
        # Mixed content detection
        if abs(music_score - speech_score) < 0.2:
            return 'mixed', 0.6
        
        # Low confidence threshold
        if best_score < 0.3:
            return 'mixed', 0.5
        
        # Normalize confidence
        confidence = min(1.0, best_score)
        
        return best_class, confidence
    
    def analyze_audio_file(self, 
                          audio_path: str,
                          segment_length: float = 10.0,
                          overlap: float = 2.0) -> List[AudioClassificationResult]:
        """
        Analyze an entire audio file in segments.
        
        Args:
            audio_path: Path to audio file
            segment_length: Length of each segment in seconds
            overlap: Overlap between segments in seconds
            
        Returns:
            List of AudioClassificationResult for each segment
        """
        # Load audio
        audio, sr = librosa.load(audio_path, sr=self.sample_rate)
        duration = len(audio) / sr
        
        results = []
        
        # Process in overlapping segments
        step = segment_length - overlap
        current_time = 0.0
        
        while current_time < duration - segment_length:
            start_sample = int(current_time * sr)
            end_sample = int((current_time + segment_length) * sr)
            
            segment = audio[start_sample:end_sample]
            
            result = self.classify_audio_segment(
                segment, current_time, current_time + segment_length, sr
            )
            results.append(result)
            
            current_time += step
        
        # Process final segment if needed
        if current_time < duration:
            start_sample = int(current_time * sr)
            segment = audio[start_sample:]
            
            result = self.classify_audio_segment(
                segment, current_time, duration, sr
            )
            results.append(result)
        
        return results
    
    def train_classifier(self, 
                        training_data: List[Tuple[np.ndarray, str]],
                        validation_split: float = 0.2) -> Dict[str, Any]:
        """
        Train the ML classifier with labeled audio data.
        
        Args:
            training_data: List of (audio_segment, label) tuples
            validation_split: Fraction of data to use for validation
            
        Returns:
            Training results and metrics
        """
        logger.info(f"Training classifier with {len(training_data)} samples")
        
        # Extract features and labels
        X = []
        y = []
        
        for audio_segment, label in training_data:
            features = self.extract_features(audio_segment)
            feature_vector = list(features.values())
            X.append(feature_vector)
            y.append(label)
        
        X = np.array(X)
        y = np.array(y)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=validation_split, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train classifier
        self.classifier.fit(X_train_scaled, y_train)
        self.is_trained = True
        
        # Evaluate
        train_score = self.classifier.score(X_train_scaled, y_train)
        test_score = self.classifier.score(X_test_scaled, y_test)
        
        y_pred = self.classifier.predict(X_test_scaled)
        
        results = {
            'train_accuracy': train_score,
            'test_accuracy': test_score,
            'classification_report': classification_report(y_test, y_pred),
            'feature_importance': dict(zip(
                [f'feature_{i}' for i in range(len(X[0]))],
                self.classifier.feature_importances_
            ))
        }
        
        logger.info(f"Training complete. Test accuracy: {test_score:.3f}")
        return results
    
    def save_model(self, model_path: str) -> None:
        """Save trained model to disk."""
        if not self.is_trained:
            raise ValueError("Model must be trained before saving")
        
        model_data = {
            'classifier': self.classifier,
            'scaler': self.scaler,
            'feature_config': self.feature_config,
            'is_trained': self.is_trained
        }
        
        joblib.dump(model_data, model_path)
        logger.info(f"Model saved to {model_path}")
    
    def load_model(self, model_path: str) -> None:
        """Load trained model from disk."""
        model_data = joblib.load(model_path)
        
        self.classifier = model_data['classifier']
        self.scaler = model_data['scaler']
        self.feature_config = model_data['feature_config']
        self.is_trained = model_data['is_trained']
        
        logger.info(f"Model loaded from {model_path}")


def create_sample_training_data(output_dir: str) -> None:
    """
    Create sample training data structure for church service audio classification.
    
    This function creates a directory structure where users can place audio samples
    for training the classifier.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories for each class
    classes = ['music', 'speech', 'singing', 'mixed', 'silence']
    
    for class_name in classes:
        class_dir = output_path / class_name
        class_dir.mkdir(exist_ok=True)
        
        # Create README for each class
        readme_content = f"""
# {class_name.title()} Audio Samples

Place audio files (.wav, .mp3, .m4a) in this directory to train the classifier
to recognize {class_name} content.

Examples of {class_name}:
"""
        
        if class_name == 'music':
            readme_content += """
- Instrumental music (piano, organ, orchestra)
- Background music during service
- Prelude/postlude music
"""
        elif class_name == 'speech':
            readme_content += """
- Sermon portions
- Announcements
- Scripture readings
- Prayers (spoken)
"""
        elif class_name == 'singing':
            readme_content += """
- Congregational singing/hymns
- Choir performances
- Solo vocal performances
"""
        elif class_name == 'mixed':
            readme_content += """
- Speech with background music
- Singing with instrumental accompaniment
- Transitional content
"""
        elif class_name == 'silence':
            readme_content += """
- Quiet/silent moments
- Very low volume ambient sound
- Pauses between segments
"""
        
        with open(class_dir / 'README.md', 'w') as f:
            f.write(readme_content)
    
    # Create main README
    main_readme = f"""
# Church Service Audio Training Data

This directory contains training samples for the church service audio classifier.

## Directory Structure:
- `music/`: Instrumental music samples
- `speech/`: Spoken content (sermons, announcements)
- `singing/`: Vocal music (hymns, choir)
- `mixed/`: Content with multiple audio types
- `silence/`: Quiet/ambient audio

## Usage:
1. Place audio files in appropriate subdirectories
2. Use the ChurchAudioClassifier.train_from_directory() method
3. Save the trained model for future use

## Supported Formats:
- WAV (.wav)
- MP3 (.mp3)
- M4A (.m4a)
- Other formats supported by librosa

Created: {output_path}
"""
    
    with open(output_path / 'README.md', 'w') as f:
        f.write(main_readme)
    
    print(f"Training data structure created at: {output_path}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Church service audio classification")
    parser.add_argument("--create-training", help="Create training data directory structure")
    parser.add_argument("--analyze", help="Analyze audio file")
    parser.add_argument("--output", help="Output file for results")
    
    args = parser.parse_args()
    
    if args.create_training:
        create_sample_training_data(args.create_training)
    elif args.analyze:
        classifier = ChurchAudioClassifier()
        results = classifier.analyze_audio_file(args.analyze)
        
        print(f"\\nAudio Classification Results for: {args.analyze}")
        print("=" * 60)
        
        for result in results:
            print(f"{result.start_time:6.1f}s - {result.end_time:6.1f}s: "
                  f"{result.classification:10} (confidence: {result.confidence:.2f})")
        
        if args.output:
            import json
            output_data = [
                {
                    'start_time': r.start_time,
                    'end_time': r.end_time,
                    'classification': r.classification,
                    'confidence': r.confidence
                }
                for r in results
            ]
            
            with open(args.output, 'w') as f:
                json.dump(output_data, f, indent=2)
            print(f"\\nResults saved to: {args.output}")