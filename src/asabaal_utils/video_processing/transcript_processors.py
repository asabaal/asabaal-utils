"""
Transcript processors for enhanced clip generation.

This module provides a set of processors that can be applied to transcripts
before final clipping to improve quality and coherence.
"""

import re
import logging
import itertools
from typing import List, Dict, Any, Optional, Union, Tuple, Callable
from dataclasses import dataclass
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


class FillerWordsProcessor:
    """
    Handles filler words in transcripts.
    
    This processor can remove or modify filler words like "um", "uh", etc.
    according to configurable policies.
    """
    
    def __init__(self, config=None):
        """
        Initialize the filler words processor.
        
        Args:
            config: Configuration dictionary with options:
                - words: List of filler words to handle
                - policy: How to handle fillers - "remove_all", "keep_all", "context_sensitive"
                - exceptions: Words to keep in specific contexts
        """
        # Default configuration
        default_config = {
            "words": ["um", "uh", "like", "you know", "I mean", "kind of", "sort of"],
            "policy": "remove_all",  # Options: remove_all, keep_all, context_sensitive
            "exceptions": []  # Words to keep in specific contexts
        }
        
        # Merge provided config with defaults
        if config is None:
            self.config = default_config
        else:
            self.config = default_config.copy()
            self.config.update(config)
        
        # Compile regex patterns for faster matching
        self._compile_patterns()
        
    def _compile_patterns(self):
        """Compile regex patterns for filler word detection."""
        # Sort words by length (longest first) to avoid partial matches
        sorted_words = sorted(self.config["words"], key=len, reverse=True)
        
        # Create pattern with word boundaries
        patterns = []
        for word in sorted_words:
            # Escape special regex characters
            escaped_word = re.escape(word)
            # Match word with optional punctuation
            patterns.append(fr'\b{escaped_word}\b')
        
        # Combine patterns
        self.pattern = re.compile(r'|'.join(patterns), re.IGNORECASE)
        
        # Exceptions pattern
        if self.config["exceptions"]:
            exception_patterns = []
            for exc in self.config["exceptions"]:
                # Split into filler and context pattern
                filler, context = exc.split("|")
                exception_patterns.append(fr'({re.escape(filler)}.*?{context})')
            
            self.exception_pattern = re.compile(r'|'.join(exception_patterns), re.IGNORECASE)
        else:
            self.exception_pattern = None
    
    def process(self, transcript):
        """
        Process the transcript by handling filler words according to config.
        
        Args:
            transcript: The transcript text or JSON object to process
        
        Returns:
            Processed transcript with filler words handled
        """
        if transcript is None:
            raise ValueError("Cannot process None transcript")        
        # Handle different input formats
        if isinstance(transcript, str):
            # Normalize line breaks and create continuous text for processing
            normalized_text = self._normalize_text(transcript)
            processed_text = self._process_text(normalized_text)
            # Preserve original line breaks
            return self._restore_line_breaks(transcript, processed_text)
        elif isinstance(transcript, list):
            # Handle list of segments (e.g., from JSON)
            for segment in transcript:
                if 'text' in segment:
                    # Normalize and process each segment's text
                    normalized_text = self._normalize_text(segment['text'])
                    segment['text'] = self._process_text(normalized_text)
            return transcript
        elif isinstance(transcript, dict):
            # Handle dictionary with text field
            if 'text' in transcript:
                normalized_text = self._normalize_text(transcript['text'])
                transcript['text'] = self._process_text(normalized_text)
            # Process segments if present
            if 'segments' in transcript and isinstance(transcript['segments'], list):
                for segment in transcript['segments']:
                    if 'text' in segment:
                        normalized_text = self._normalize_text(segment['text'])
                        segment['text'] = self._process_text(normalized_text)
            return transcript
        
        # Return unchanged if unknown format
        logger.warning("Unknown transcript format for filler word processing")
        return transcript
    
    def _normalize_text(self, text):
        """Normalize text by standardizing line breaks."""
        # Normalize line endings
        normalized = text.replace('\r\n', '\n')
        # Replace consecutive line breaks with a special marker
        normalized = re.sub(r'\n+', ' <LINEBREAK> ', normalized)
        return normalized
    
    def _restore_line_breaks(self, original_text, processed_text):
        """Restore original line break pattern after processing."""
        # Replace markers with line breaks
        result = processed_text.replace(' <LINEBREAK> ', '\n')
        return result
    
    def _process_text(self, text):
        """Process a text string to handle filler words."""
        # Apply the configured policy
        if self.config["policy"] == "keep_all":
            return text
        
        if self.config["policy"] == "remove_all":
            # Simply remove all fillers
            result = self.pattern.sub('', text)
            # Clean up multiple spaces
            result = re.sub(r'\s+', ' ', result).strip()
            return result
        
        if self.config["policy"] == "context_sensitive":
            # Identify fillers
            fillers = self._identify_fillers(text)
            # Apply context-sensitive rules
            return self._apply_context_rules(text, fillers)
        
        # Default fallback
        return text
    
    def _identify_fillers(self, text):
        """Identify filler words in the given text."""
        fillers = []
        for match in self.pattern.finditer(text):
            # Store match information
            fillers.append({
                'word': match.group(0),
                'start': match.start(),
                'end': match.end(),
                'keep': False  # Default to not keeping
            })
        
        # Check exceptions
        if self.exception_pattern:
            for match in self.exception_pattern.finditer(text):
                # Mark matching fillers to keep
                for filler in fillers:
                    if filler['start'] >= match.start() and filler['end'] <= match.end():
                        filler['keep'] = True
        
        return fillers
    
    def _apply_context_rules(self, text, fillers):
        """Apply context-sensitive rules to fillers."""
        # Sort fillers by position (start index) in reverse order
        # This allows us to modify the text without affecting positions of earlier fillers
        fillers.sort(key=lambda x: x['start'], reverse=True)
        
        # Create a mutable list of characters from the text
        chars = list(text)
        
        # Remove fillers that should be removed
        for filler in fillers:
            if not filler['keep']:
                # Replace filler with empty string
                chars[filler['start']:filler['end']] = []
        
        # Join characters back into text
        result = ''.join(chars)
        
        # Clean up multiple spaces
        result = re.sub(r'\s+', ' ', result).strip()
        
        return result


class RepetitionHandler:
    """
    Handles repeated phrases and words in transcripts.
    
    This processor can identify and handle repetitions according to
    configured strategies.
    """
    
    def __init__(self, config=None):
        """
        Initialize the repetition handler.
        
        Args:
            config: Configuration dictionary with options:
                - window_size: Number of words to check for repetitions
                - strategy: How to handle repetitions - "first_instance", "cleanest_instance", "combine"
                - min_phrase_length: Minimum length of phrase to consider a repetition
                - max_gap: Maximum gap between repetitions to consider them related
        """
        # Default configuration
        default_config = {
            "window_size": 50,  # Number of words to check for repetitions
            "strategy": "first_instance",  # Options: first_instance, cleanest_instance, combine
            "min_phrase_length": 3,  # Minimum number of words to consider a repetition
            "max_gap": 7,  # Maximum gap between repetitions to consider them related
            "max_distance": 100,  # Maximum distance between repetitions to consider them
        }
        # Merge provided config with defaults
        if config is None:
            self.config = default_config
        else:
            self.config = default_config.copy()
            self.config.update(config)
    
    def process(self, transcript):
        """
        Process the transcript by handling repetitions according to config.
        
        Args:
            transcript: The transcript text or JSON object to process
        
        Returns:
            Processed transcript with repetitions handled
        """
        if transcript is None:
            raise ValueError("Cannot process None transcript")        
        # Handle different input formats
        if isinstance(transcript, str):
            # Normalize and create continuous text for processing
            normalized_text = self._normalize_text(transcript)
            processed_text = self._process_text(normalized_text)
            # Preserve original line break structure
            return self._restore_line_breaks(transcript, processed_text)
        elif isinstance(transcript, list):
            # Handle list of segments (e.g., from JSON)
            for segment in transcript:
                if 'text' in segment:
                    # Normalize line breaks for processing
                    normalized_text = self._normalize_text(segment['text'])
                    segment['text'] = self._process_text(normalized_text)
            return transcript
        elif isinstance(transcript, dict):
            # Handle dictionary with text field
            if 'text' in transcript:
                normalized_text = self._normalize_text(transcript['text'])
                transcript['text'] = self._process_text(normalized_text)
            # Process segments if present
            if 'segments' in transcript and isinstance(transcript['segments'], list):
                for segment in transcript['segments']:
                    if 'text' in segment:
                        normalized_text = self._normalize_text(segment['text'])
                        segment['text'] = self._process_text(normalized_text)
            return transcript
        
        # Return unchanged if unknown format
        logger.warning("Unknown transcript format for repetition handling")
        return transcript
    
    def _normalize_text(self, text):
        """Normalize text to handle cross-line boundaries."""
        # Normalize line endings
        normalized = text.replace('\r\n', '\n')
        # Replace line breaks with a special marker for processing
        normalized = re.sub(r'\n+', ' <LINEBREAK> ', normalized)
        return normalized
    
    def _restore_line_breaks(self, original_text, processed_text):
        """Restore original line break pattern."""
        # Replace markers with line breaks
        result = processed_text.replace(' <LINEBREAK> ', '\n')
        return result
    
    def _process_text(self, text):
        """Process a text string to handle repetitions."""
        # Tokenize the text (treating it as continuous)
        tokens = text.split()
        
        # Identify repetitions across the entire text
        repetitions = self._identify_repetitions(tokens)
        
        # Apply the configured strategy
        processed_tokens = self._apply_strategy(tokens, repetitions)
        
        # Join tokens back into text
        return ' '.join(processed_tokens)
    
    def _identify_repetitions(self, tokens):
        """
        Identify repeated phrases in the token sequence.
        
        Returns:
            List of repetition objects, each containing:
            - phrase: The repeated phrase (list of tokens)
            - instances: List of positions where the phrase occurs
        """
        repetitions = []
        min_length = self.config["min_phrase_length"]
        max_distance = self.config["max_distance"]
        
        # Create n-grams for all possible phrase lengths
        for phrase_length in range(min_length, min(len(tokens) // 2, self.config["window_size"] + 1)):
            # Generate all phrases of this length
            phrases = {}  # Maps phrase -> list of positions
            
            for i in range(len(tokens) - phrase_length + 1):
                phrase = tuple(tokens[i:i+phrase_length])
                
                # Skip phrases with mostly stopwords or very short words
                if self._is_low_information_phrase(phrase):
                    continue
                
                if phrase in phrases:
                    # Check if this instance is within range of any previous one
                    phrases[phrase].append(i)
                else:
                    phrases[phrase] = [i]
            
            # Filter to phrases that occur multiple times within proximity
            for phrase, positions in phrases.items():
                if len(positions) > 1:
                    # Group positions that are close together
                    groups = self._group_positions(positions)
                    
                    # Only consider phrases with multiple groups (actual repetitions)
                    if len(groups) > 1:
                        repetitions.append({
                            'phrase': phrase,
                            'groups': groups
                        })
        
        # Sort repetitions by length (longer phrases first)
        repetitions.sort(key=lambda x: len(x['phrase']), reverse=True)
        
        # Remove overlapping repetitions (prefer longer phrases)
        return self._remove_overlapping_repetitions(repetitions)
    
    def _is_low_information_phrase(self, phrase):
        """Determine if a phrase is mostly stopwords or very short words."""
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'if', 'of', 'at', 'by', 'for', 'to', 'in', 'with'}
        short_word_count = sum(1 for word in phrase if len(word) < 3 or word.lower() in stopwords)
        return short_word_count > len(phrase) * 0.6
    
    def _group_positions(self, positions):
        """Group positions that are close together."""
        if not positions:
            return []
            
        # Sort positions
        sorted_positions = sorted(positions)
        groups = [[sorted_positions[0]]]
        max_gap = self.config["max_gap"]
        
        for pos in sorted_positions[1:]:
            # Check if this position is close to the last group
            if pos - groups[-1][-1] <= max_gap:
                groups[-1].append(pos)
            else:
                # Start a new group
                groups.append([pos])
        
        return groups
    
    def _remove_overlapping_repetitions(self, repetitions):
        """
        Remove overlapping repetitions, preferring longer phrases.
        
        Args:
            repetitions: List of repetition objects
            
        Returns:
            Filtered list with non-overlapping repetitions
        """
        if not repetitions:
            return []
            
        # Track which token positions are covered by repetitions
        covered_positions = set()
        filtered_repetitions = []
        
        for rep in repetitions:
            # Check if this repetition overlaps with existing ones
            overlapping = False
            phrase_length = len(rep['phrase'])
            
            # Check each group of this repetition
            for group in rep['groups']:
                # Check each position in this group
                for pos in group:
                    # Check all positions covered by this phrase instance
                    for offset in range(phrase_length):
                        if pos + offset in covered_positions:
                            overlapping = True
                            break
                    if overlapping:
                        break
                if overlapping:
                    break
            
            if not overlapping:
                # Add this repetition
                filtered_repetitions.append(rep)
                
                # Mark positions as covered
                for group in rep['groups']:
                    for pos in group:
                        for offset in range(phrase_length):
                            covered_positions.add(pos + offset)
        
        return filtered_repetitions
    
    def _apply_strategy(self, tokens, repetitions):
        """
        Apply the configured strategy to the identified repetitions.
        
        Args:
            tokens: List of tokens (words)
            repetitions: List of repetition objects
            
        Returns:
            Modified token list with repetitions handled
        """
        # Create a copy of tokens to modify
        result = tokens.copy()
        
        # Track which positions to remove (set to None)
        to_remove = set()
        
        # Handle each repetition according to strategy
        for rep in repetitions:
            if self.config["strategy"] == "first_instance":
                self._apply_first_instance_strategy(rep, to_remove)
            elif self.config["strategy"] == "cleanest_instance":
                self._apply_cleanest_instance_strategy(rep, result, to_remove)
            elif self.config["strategy"] == "combine":
                self._apply_combine_strategy(rep, result, to_remove)
        
        # Remove marked positions
        return [t for i, t in enumerate(result) if i not in to_remove]
    
    def _apply_first_instance_strategy(self, repetition, to_remove):
        """Keep only the first instance of repetitions."""
        phrase_length = len(repetition['phrase'])
        
        # Keep the first group, remove others
        for group_idx, group in enumerate(repetition['groups']):
            if group_idx == 0:
                continue  # Keep first group
            
            # Mark all positions in other groups for removal
            for pos in group:
                for offset in range(phrase_length):
                    to_remove.add(pos + offset)
    
    def _apply_cleanest_instance_strategy(self, repetition, tokens, to_remove):
        """Keep the cleanest instance of repetitions."""
        phrase_length = len(repetition['phrase'])
        
        # Score each group based on "cleanliness"
        group_scores = []
        for group in repetition['groups']:
            score = self._calculate_cleanliness_score(group[0], phrase_length, tokens)
            group_scores.append((group, score))
        
        # Find the group with the highest score
        cleanest_group = max(group_scores, key=lambda x: x[1])[0]
        
        # Remove all groups except the cleanest
        for group in repetition['groups']:
            if group != cleanest_group:
                for pos in group:
                    for offset in range(phrase_length):
                        to_remove.add(pos + offset)
    
    def _calculate_cleanliness_score(self, position, length, tokens):
        """
        Calculate a cleanliness score for a phrase instance.
        
        Higher score means fewer fillers, hesitations, etc.
        """
        # Context window around the phrase
        context_start = max(0, position - 5)
        context_end = min(len(tokens), position + length + 5)
        context = tokens[context_start:context_end]
        
        # Count potential filler words
        filler_words = {'um', 'uh', 'like', 'you know', 'i mean', 'kind of', 'sort of'}
        filler_count = sum(1 for word in context if word.lower() in filler_words)
        
        # Base score - penalize for fillers
        score = 10 - filler_count
        
        # Add bonus for being complete sentences or syntactic units
        if position > 0 and tokens[position-1] in {'.', '!', '?', ';'}:
            score += 2  # Phrase starts after punctuation
        
        if position + length < len(tokens) and tokens[position+length] in {'.', '!', '?', ';'}:
            score += 2  # Phrase ends with punctuation
            
        return score
    
    def _apply_combine_strategy(self, repetition, tokens, to_remove):
        """
        Combine repetitions if they are adjacent or nearly adjacent.
        
        This strategy keeps the first occurrence of a repeated phrase,
        but may incorporate improvements from later occurrences.
        """
        phrase_length = len(repetition['phrase'])
        groups = repetition['groups']
        
        # Keep first group
        first_group = groups[0]
        
        # Mark all other groups for removal
        for group_idx, group in enumerate(groups):
            if group_idx == 0:
                continue  # Skip first group
                
            for pos in group:
                for offset in range(phrase_length):
                    to_remove.add(pos + offset)
                    
                # If groups are very close, check if we can improve the first instance
                if pos - first_group[0] < self.config["max_gap"] * 2:
                    # Use a simple heuristic: if the second instance has fewer filler words,
                    # it might be cleaner, so consider incorporating parts of it
                    if self._calculate_cleanliness_score(pos, phrase_length, tokens) > \
                       self._calculate_cleanliness_score(first_group[0], phrase_length, tokens):
                        # We could do a more sophisticated merging here if needed
                        pass


class SentenceBoundaryDetector:
    """
    Detects sentence boundaries in transcripts.
    
    This processor identifies natural sentence boundaries and can optimize
    clip boundaries to align with sentences.
    """
    
    def __init__(self, config=None):
        """
        Initialize the sentence boundary detector.
        
        Args:
            config: Configuration dictionary with options:
                - min_sentence_length: Minimum words to consider as complete sentence
                - boundary_indicators: Words/characters that indicate boundaries
                - clause_connectors: Words that connect clauses
                - pause_threshold: Pause duration that suggests a boundary
                - boundary_confidence_threshold: Confidence threshold for boundaries
        """
        # Default configuration
        default_config = {
            "min_sentence_length": 5,  # Minimum words to consider as complete sentence
            "boundary_indicators": [".", "?", "!", ";", "okay", "right", "so", "well", "and", "but"],
            "clause_connectors": ["and", "but", "or", "so", "because", "although", "however"],
            "pause_threshold": 0.8,  # In seconds, if timing info available
            "boundary_confidence_threshold": 0.65  # Confidence level to consider a boundary
        }
        
        # Merge provided config with defaults
        if config is None:
            self.config = default_config
        else:
            self.config = default_config.copy()
            self.config.update(config)
        
        # Initialize NLP components if needed
        self._initialize_nlp()
    
    def _initialize_nlp(self):
        """Initialize NLP components if available."""
        # Try to import spaCy if available
        try:
            import spacy
            try:
                # Try to load a small model
                self.nlp = spacy.load("en_core_web_sm")
                self.use_spacy = True
                logger.info("Using spaCy for sentence boundary detection")
            except:
                self.use_spacy = False
                logger.info("spaCy model not available, using rule-based sentence detection")
        except ImportError:
            self.use_spacy = False
            logger.info("spaCy not installed, using rule-based sentence detection")
    
    def process(self, transcript):
        """
        Process the transcript by detecting sentence boundaries.
        
        Args:
            transcript: The transcript text or JSON object to process
        
        Returns:
            Processed transcript with sentence boundaries identified
        """
        if transcript is None:
            raise ValueError("Cannot process None transcript")        
        # Handle different input formats
        if isinstance(transcript, str):
            # Normalize the text for processing
            normalized_text = self._normalize_text(transcript)
            boundaries = self._identify_boundaries(normalized_text)
            return self._mark_boundaries(normalized_text, boundaries)
        elif isinstance(transcript, list):
            # Handle list of segments (e.g., from JSON)
            for segment in transcript:
                if 'text' in segment:
                    # Normalize for processing
                    normalized_text = self._normalize_text(segment['text'])
                    boundaries = self._identify_boundaries(normalized_text)
                    segment['sentence_boundaries'] = boundaries
                    # Optionally set clip boundaries if segment has start/end times
                    if 'start_time' in segment and 'end_time' in segment:
                        segment['clip_boundaries'] = self._optimize_clip_boundaries(
                            normalized_text, boundaries, segment['start_time'], segment['end_time']
                        )
            return transcript
        elif isinstance(transcript, dict):
            # Handle dictionary with text field
            if 'text' in transcript:
                normalized_text = self._normalize_text(transcript['text'])
                boundaries = self._identify_boundaries(normalized_text)
                transcript['sentence_boundaries'] = boundaries
                
                # Optionally set clip boundaries if transcript has timing info
                if 'start_time' in transcript and 'end_time' in transcript:
                    transcript['clip_boundaries'] = self._optimize_clip_boundaries(
                        normalized_text, boundaries, transcript['start_time'], transcript['end_time']
                    )
            
            # Process segments if present
            if 'segments' in transcript and isinstance(transcript['segments'], list):
                for segment in transcript['segments']:
                    if 'text' in segment:
                        normalized_text = self._normalize_text(segment['text'])
                        boundaries = self._identify_boundaries(normalized_text)
                        segment['sentence_boundaries'] = boundaries
                        # Optionally set clip boundaries if segment has start/end times
                        if 'start_time' in segment and 'end_time' in segment:
                            segment['clip_boundaries'] = self._optimize_clip_boundaries(
                                normalized_text, boundaries, segment['start_time'], segment['end_time']
                            )
            return transcript
        
        # Return unchanged if unknown format
        logger.warning("Unknown transcript format for sentence boundary detection")
        return transcript
    
    def _normalize_text(self, text):
        """Normalize text for processing."""
        # Normalize line endings
        normalized = text.replace('\r\n', '\n')
        # Replace line breaks with spaces for continuous processing
        normalized = re.sub(r'\n+', ' ', normalized)
        return normalized
    
    def _identify_boundaries(self, text):
        """
        Identify potential sentence boundaries in the text.
        
        Returns:
            List of boundary positions with confidence scores
        """
        if self.use_spacy:
            return self._identify_boundaries_spacy(text)
        else:
            return self._identify_boundaries_rules(text)
    
    def _identify_boundaries_spacy(self, text):
        """Use spaCy to identify sentence boundaries."""
        doc = self.nlp(text)
        boundaries = []
        
        for sent in doc.sents:
            end_char = sent.end_char
            # Calculate confidence based on sentence completeness
            confidence = self._calculate_sentence_confidence(sent)
            boundaries.append({
                'position': end_char,
                'confidence': confidence,
                'text': sent.text
            })
        
        return boundaries
    
    def _calculate_sentence_confidence(self, sent):
        """Calculate confidence that a spaCy sentence is a true sentence."""
        # Base confidence on sentence structure
        has_subject = any(token.dep_ in {'nsubj', 'nsubjpass'} for token in sent)
        has_verb = any(token.pos_ in {'VERB', 'AUX'} for token in sent)
        ends_with_punct = sent[-1].is_punct
        
        confidence = 0.5  # Base confidence
        if has_subject and has_verb:
            confidence += 0.3  # Complete clause
        if ends_with_punct:
            confidence += 0.2  # Proper punctuation
            
        return min(confidence, 1.0)
    
    def _identify_boundaries_rules(self, text):
        """Use rule-based approach to identify sentence boundaries."""
        boundaries = []
        
        # Split text into words
        words = text.split()
        
        # Track character position as we go
        char_pos = 0
        
        # Look for boundary indicators
        for i, word in enumerate(words):
            char_pos += len(word) + (1 if i > 0 else 0)  # Add space except before first word
            
            # Check if this word ends with punctuation
            ends_with_punct = any(word.endswith(p) for p in ['.', '?', '!', ';'])
            
            # Check if this word is a discourse marker
            is_marker = word.lower() in self.config["boundary_indicators"]
            
            # Check if we're at a potential clause or sentence boundary
            if ends_with_punct or is_marker:
                # Calculate confidence based on context
                confidence = self._calculate_boundary_confidence(i, words)
                
                if confidence >= self.config["boundary_confidence_threshold"]:
                    # We have a boundary
                    # Calculate the exact character position
                    boundaries.append({
                        'position': char_pos,
                        'confidence': confidence,
                        'text': ' '.join(words[:i+1])
                    })
        
        return boundaries
    
    def _calculate_boundary_confidence(self, position, words):
        """
        Calculate confidence that a position is a sentence boundary.
        
        Args:
            position: Word position in the text
            words: List of words in the text
            
        Returns:
            Confidence score between 0 and 1
        """
        # Base confidence on various factors
        confidence = 0.0
        
        # Check if the position is near the beginning or end
        if position < 2 or position > len(words) - 2:
            confidence += 0.1  # Slight boost for being at edges
        
        # Check if preceding text has minimum length to be a sentence
        if position >= self.config["min_sentence_length"]:
            confidence += 0.2
        
        # Check for punctuation
        word = words[position]
        if any(word.endswith(p) for p in ['.', '?', '!', ';']):
            confidence += 0.4  # Strong indicator
            
            # Check if next word starts with capital (if available)
            if position < len(words) - 1 and words[position + 1][0].isupper():
                confidence += 0.2  # Additional evidence
        
        # Check for discourse markers
        if word.lower() in {"okay", "right", "well", "so", "and", "but"}:
            confidence += 0.3
            
            # Discount if it's a conjunction in the middle of a clause
            if position > 0 and position < len(words) - 1:
                if word.lower() in self.config["clause_connectors"]:
                    # Check if it looks like it's connecting clauses
                    # This is a simplistic check - in a real system, you'd want
                    # to use syntactic parsing
                    confidence -= 0.2
        
        # Look for subject-predicate patterns
        # This is a simplistic approximation - would be better with dependency parsing
        subject_words = {"i", "you", "he", "she", "it", "we", "they", "this", "that", "these", "those"}
        if position > 0 and any(words[i].lower() in subject_words for i in range(max(0, position-5), position)):
            confidence += 0.1  # Slight boost for having a subject
        
        return min(confidence, 1.0)  # Cap at 1.0
    
    def _mark_boundaries(self, text, boundaries):
        """
        Mark sentence boundaries in the text.
        
        Args:
            text: Original text
            boundaries: List of boundary positions
            
        Returns:
            Text with marked boundaries (using | symbols)
        """
        # Sort boundaries by position in reverse order
        sorted_boundaries = sorted(boundaries, key=lambda x: x['position'], reverse=True)
        
        # Insert boundary markers
        result = list(text)
        for boundary in sorted_boundaries:
            if boundary['confidence'] >= self.config["boundary_confidence_threshold"]:
                pos = boundary['position']
                # Insert marker at this position
                result.insert(pos, ' | ')
        
        return ''.join(result)
    
    def _optimize_clip_boundaries(self, text, sentence_boundaries, start_time, end_time):
        """
        Optimize clip boundaries to align with sentence boundaries.
        
        Args:
            text: Transcript text
            sentence_boundaries: Identified sentence boundaries
            start_time: Original clip start time
            end_time: Original clip end time
            
        Returns:
            Optimized clip boundaries as {start_time, end_time}
        """
        # Filter to boundaries with high confidence
        high_confidence = [b for b in sentence_boundaries 
                         if b['confidence'] >= self.config["boundary_confidence_threshold"]]
        
        if not high_confidence:
            # No good boundaries, keep original
            return {'start_time': start_time, 'end_time': end_time}
        
        # Estimate character positions for original boundaries
        char_per_second = len(text) / (end_time - start_time)
        start_char = 0  # Assume clip starts at beginning of text
        end_char = len(text)  # Assume clip ends at end of text
        
        # Find nearest sentence boundary to start
        nearest_start = None
        min_start_diff = float('inf')
        
        for boundary in high_confidence:
            diff = abs(boundary['position'] - start_char)
            if diff < min_start_diff:
                min_start_diff = diff
                nearest_start = boundary
        
        # Find nearest sentence boundary to end
        nearest_end = None
        min_end_diff = float('inf')
        
        for boundary in high_confidence:
            diff = abs(boundary['position'] - end_char)
            if diff < min_end_diff:
                min_end_diff = diff
                nearest_end = boundary
        
        # Calculate new times
        adjusted_start = start_time
        adjusted_end = end_time
        
        # Only adjust if the boundary is reasonably close (within 20% of clip duration)
        max_diff = 0.2 * (end_time - start_time)
        
        if nearest_start and min_start_diff / char_per_second < max_diff:
            # Adjust start time
            adjusted_start = start_time + (nearest_start['position'] - start_char) / char_per_second
            
        if nearest_end and min_end_diff / char_per_second < max_diff:
            # Adjust end time
            adjusted_end = start_time + (nearest_end['position'] - start_char) / char_per_second
        
        return {'start_time': adjusted_start, 'end_time': adjusted_end}


class SemanticUnitPreserver:
    """
    Preserves semantic units in transcripts.
    
    This processor identifies and preserves semantic units like explanations,
    lists, question-answer pairs, etc.
    """
    
    def __init__(self, config=None):
        """
        Initialize the semantic unit preserver.
        
        Args:
            config: Configuration dictionary with options:
                - keyword_threshold: Threshold for keyword repetition
                - preserve_patterns: Patterns to preserve
                - max_unit_length: Maximum words in a semantic unit
                - topic_change_indicators: Words suggesting topic changes
        """
        # Default configuration
        default_config = {
            "keyword_threshold": 0.4,  # Threshold for keyword repetition to indicate related content
            "preserve_patterns": ["first.*second.*third", "if.*then", "problem.*solution"],
            "max_unit_length": 150,  # Maximum words in a semantic unit before forced split
            "topic_change_indicators": ["now", "so", "anyway", "okay", "moving on", "let's talk about"]
        }
        
        # Merge provided config with defaults
        if config is None:
            self.config = default_config
        else:
            self.config = default_config.copy()
            self.config.update(config)
        
        # Compile patterns
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for semantic unit detection."""
        self.patterns = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in self.config["preserve_patterns"]]
        
        # Create topic change pattern
        topic_indicators = '|'.join(re.escape(w) for w in self.config["topic_change_indicators"])
        self.topic_pattern = re.compile(rf'\b({topic_indicators})\b', re.IGNORECASE)
    
    def process(self, transcript, proposed_boundaries=None):
        """
        Process the transcript by preserving semantic units.
        
        Args:
            transcript: The transcript text or JSON object to process
            proposed_boundaries: Optional list of proposed boundary positions
            
        Returns:
            Processed transcript with semantic units preserved
        """
        if transcript is None:
            raise ValueError("Cannot process None transcript")        
        # Handle different input formats
        if isinstance(transcript, str):
            # Normalize text for processing
            normalized_text = self._normalize_text(transcript)
            semantic_units = self._identify_semantic_units(normalized_text)
            if proposed_boundaries:
                adjusted_boundaries = self._adjust_boundaries(proposed_boundaries, semantic_units)
                return self._mark_adjusted_boundaries(normalized_text, adjusted_boundaries)
            else:
                return self._mark_semantic_units(normalized_text, semantic_units)
        elif isinstance(transcript, list):
            # Handle list of segments (e.g., from JSON)
            for segment in transcript:
                if 'text' in segment:
                    normalized_text = self._normalize_text(segment['text'])
                    semantic_units = self._identify_semantic_units(normalized_text)
                    segment['semantic_units'] = semantic_units
                    
                    # Adjust clip boundaries if provided
                    if 'clip_boundaries' in segment and proposed_boundaries:
                        segment['clip_boundaries'] = self._adjust_boundaries(
                            proposed_boundaries, semantic_units
                        )
            return transcript
        elif isinstance(transcript, dict):
            # Handle dictionary with text field
            if 'text' in transcript:
                normalized_text = self._normalize_text(transcript['text'])
                semantic_units = self._identify_semantic_units(normalized_text)
                transcript['semantic_units'] = semantic_units
                
                # Adjust clip boundaries if provided
                if 'clip_boundaries' in transcript and proposed_boundaries:
                    transcript['clip_boundaries'] = self._adjust_boundaries(
                        proposed_boundaries, semantic_units
                    )
            
            # Process segments if present
            if 'segments' in transcript and isinstance(transcript['segments'], list):
                for segment in transcript['segments']:
                    if 'text' in segment:
                        normalized_text = self._normalize_text(segment['text'])
                        semantic_units = self._identify_semantic_units(normalized_text)
                        segment['semantic_units'] = semantic_units
                        
                        # Adjust clip boundaries if provided
                        if 'clip_boundaries' in segment and proposed_boundaries:
                            segment['clip_boundaries'] = self._adjust_boundaries(
                                proposed_boundaries, semantic_units
                            )
            return transcript
        
        # Return unchanged if unknown format
        logger.warning("Unknown transcript format for semantic unit preservation")
        return transcript
    
    def _normalize_text(self, text):
        """Normalize text to handle cross-line boundaries."""
        # Normalize line endings
        normalized = text.replace('\r\n', '\n')
        # Replace line breaks with spaces for continuous processing
        normalized = re.sub(r'\n+', ' ', normalized)
        return normalized
    
    def _identify_semantic_units(self, text):
        """
        Identify semantic units in the text.
        
        Returns:
            List of semantic unit objects, each with:
            - start: Character position of unit start
            - end: Character position of unit end
            - type: Type of semantic unit (e.g., "list", "explanation", "qa_pair")
            - confidence: Confidence score for this unit
        """
        units = []
        
        # Look for common semantic unit patterns
        units.extend(self._identify_list_patterns(text))
        units.extend(self._identify_question_answer_pairs(text))
        units.extend(self._identify_explanation_sequences(text))
        
        # Add topic change boundaries
        units.extend(self._detect_topic_changes(text))
        
        # Sort by position
        units.sort(key=lambda x: x['start'])
        
        # Merge overlapping units
        merged_units = self._merge_overlapping_units(units)
        
        # Force breaks at maximum unit length if necessary
        final_units = self._enforce_max_length(merged_units, text)
        
        return final_units
    
    def _identify_list_patterns(self, text):
        """Identify list patterns (first, second, third...)."""
        units = []
        
        # Look for explicit list markers
        list_markers = [
            r'\b(first|1st|one)[,:]? (.{10,}?) (second|2nd|two)[,:]?',
            r'\b(step one|step 1)[,:]? (.{10,}?) (step two|step 2)[,:]?'
        ]
        
        for pattern in list_markers:
            for match in re.finditer(pattern, text, re.IGNORECASE | re.DOTALL):
                # Try to find the end of the list
                start_pos = match.start()
                # Approximate end by looking for the next marker in sequence
                next_marker = "third" if "second" in match.group().lower() else "step three"
                end_pos = text.lower().find(next_marker, match.end())
                if end_pos == -1:
                    # If no next marker, go to end of current sentence or paragraph
                    for end_char in ['.', '!', '?', '\n']:
                        pos = text.find(end_char, match.end())
                        if pos != -1:
                            end_pos = pos + 1  # Include the end character
                            break
                    if end_pos == -1:
                        end_pos = min(match.end() + 200, len(text))  # Limit how far we go
                else:
                    # Found the next marker, go to end of that section
                    for end_char in ['.', '!', '?', '\n']:
                        pos = text.find(end_char, end_pos + len(next_marker))
                        if pos != -1:
                            end_pos = pos + 1  # Include the end character
                            break
                    if end_pos == -1:
                        end_pos = min(end_pos + 200, len(text))  # Limit how far we go
                
                units.append({
                    'start': start_pos,
                    'end': end_pos,
                    'type': 'list',
                    'confidence': 0.8  # High confidence for explicit lists
                })
        
        return units
    
    def _identify_question_answer_pairs(self, text):
        """Identify question-answer pairs."""
        units = []
        
        # Look for question marks
        for match in re.finditer(r'\?', text):
            # Find the start of the question (approximate)
            start_pos = text.rfind('.', 0, match.start())
            if start_pos == -1:
                start_pos = text.rfind('!', 0, match.start())
            if start_pos == -1:
                start_pos = text.rfind('?', 0, match.start())
            if start_pos == -1 or start_pos < max(0, match.start() - 200):
                start_pos = max(0, match.start() - 100)  # Limit how far back we go
            else:
                start_pos += 1  # Move past the punctuation
            
            # Find a potential answer (looking for end of next sentence)
            end_pos = text.find('.', match.end())
            if end_pos == -1:
                end_pos = text.find('!', match.end())
            if end_pos == -1:
                end_pos = text.find('?', match.end())
            if end_pos == -1:
                end_pos = min(match.end() + 200, len(text))  # Limit how far we go
            else:
                end_pos += 1  # Include the end punctuation
            
            # Check if it's likely a Q&A pair (simple heuristic - answer follows question directly)
            is_qa_pair = end_pos - match.end() < 300  # Answer is reasonably close
            
            if is_qa_pair:
                units.append({
                    'start': start_pos,
                    'end': end_pos,
                    'type': 'qa_pair',
                    'confidence': 0.7  # Fairly high confidence
                })
        
        return units
    
    def _identify_explanation_sequences(self, text):
        """Identify explanatory sequences (problem → solution, etc.)."""
        units = []
        
        # Look for explanation patterns
        explanation_indicators = [
            (r'\b(problem is|issue is|challenge is)', r'\b(solution is|way to|fix is|resolve this)'),
            (r'\b(if you want to|if you need to|if you have to)', r'\b(you should|you need to|you have to|here\'s how)'),
            (r'\b(context is|background is)', r'\b(means that|implies that|suggests that)')
        ]
        
        for start_pattern, end_pattern in explanation_indicators:
            # Find potential start of explanation
            for start_match in re.finditer(start_pattern, text, re.IGNORECASE):
                start_pos = start_match.start()
                
                # Look for end indicator within reasonable distance
                for end_match in re.finditer(end_pattern, text[start_pos:start_pos + 500], re.IGNORECASE):
                    end_pos = start_pos + end_match.end()
                    
                    # Extend to end of sentence if possible
                    for end_char in ['.', '!', '?']:
                        pos = text.find(end_char, end_pos)
                        if pos != -1 and pos < end_pos + 100:  # Within reasonable distance
                            end_pos = pos + 1  # Include the end character
                            break
                    
                    units.append({
                        'start': start_pos,
                        'end': end_pos,
                        'type': 'explanation',
                        'confidence': 0.6  # Moderate confidence
                    })
                    break  # Only use the first matching end indicator
        
        return units
    
    def _detect_topic_changes(self, text):
        """Detect topic changes in the text."""
        units = []
        
        # Look for topic change indicators
        for match in self.topic_pattern.finditer(text):
            # Topic change suggests the end of one unit and start of another
            units.append({
                'start': match.start(),
                'end': match.start(),  # Not a unit, just a boundary
                'type': 'topic_change',
                'confidence': 0.5  # Moderate confidence
            })
        
        return units
    
    def _merge_overlapping_units(self, units):
        """Merge overlapping semantic units."""
        if not units:
            return []
            
        # Sort by start position
        sorted_units = sorted(units, key=lambda x: x['start'])
        
        merged = [sorted_units[0]]
        
        for unit in sorted_units[1:]:
            prev = merged[-1]
            
            # Check if this unit overlaps with the previous one
            if unit['start'] <= prev['end']:
                # Merge units
                merged[-1] = {
                    'start': prev['start'],
                    'end': max(prev['end'], unit['end']),
                    'type': prev['type'] if prev['confidence'] > unit['confidence'] else unit['type'],
                    'confidence': max(prev['confidence'], unit['confidence'])
                }
            else:
                # No overlap, add as is
                merged.append(unit)
        
        return merged
    
    def _enforce_max_length(self, units, text):
        """Force breaks at maximum unit length if necessary."""
        max_length = self.config["max_unit_length"]
        result = []
        
        for unit in units:
            unit_text = text[unit['start']:unit['end']]
            unit_words = unit_text.split()
            
            if len(unit_words) <= max_length:
                # Unit is within limit, keep as is
                result.append(unit)
            else:
                # Unit is too long, split at natural break points
                current_pos = unit['start']
                words_so_far = 0
                
                # Look for natural break points (periods, commas, etc.)
                for match in re.finditer(r'[.!?,;]', unit_text):
                    # Calculate position in the original text
                    break_pos = unit['start'] + match.end()
                    
                    # Count words up to this point
                    segment_text = text[current_pos:break_pos]
                    segment_words = len(segment_text.split())
                    
                    if words_so_far + segment_words >= max_length:
                        # We've reached the maximum length, create a unit up to here
                        result.append({
                            'start': current_pos,
                            'end': break_pos,
                            'type': unit['type'],
                            'confidence': unit['confidence'] * 0.9  # Slightly lower confidence for forced splits
                        })
                        
                        # Reset counters
                        current_pos = break_pos
                        words_so_far = 0
                    else:
                        # Keep counting
                        words_so_far += segment_words
                
                # Add any remaining text as a final unit
                if current_pos < unit['end']:
                    result.append({
                        'start': current_pos,
                        'end': unit['end'],
                        'type': unit['type'],
                        'confidence': unit['confidence'] * 0.9
                    })
        
        return result
    
    def _adjust_boundaries(self, proposed_boundaries, semantic_units):
        """
        Adjust proposed clip boundaries to respect semantic units.
        
        Args:
            proposed_boundaries: List of proposed boundary positions
            semantic_units: List of identified semantic units
            
        Returns:
            Adjusted boundary positions
        """
        if not proposed_boundaries or not semantic_units:
            return proposed_boundaries
        
        # Convert boundaries to a mutable list of dictionaries if necessary
        if not isinstance(proposed_boundaries[0], dict):
            boundaries = [{'position': pos} for pos in proposed_boundaries]
        else:
            boundaries = proposed_boundaries.copy()
        
        # For each proposed boundary, check if it breaks a semantic unit
        for i, boundary in enumerate(boundaries):
            pos = boundary['position']
            
            # Check if this position is inside a semantic unit
            for unit in semantic_units:
                if unit['start'] < pos < unit['end']:
                    # This boundary breaks a unit
                    # Decide whether to move it before or after the unit
                    if (pos - unit['start']) < (unit['end'] - pos):
                        # Closer to the start, move boundary before unit
                        boundaries[i]['position'] = unit['start']
                        boundaries[i]['adjusted'] = True
                    else:
                        # Closer to the end, move boundary after unit
                        boundaries[i]['position'] = unit['end']
                        boundaries[i]['adjusted'] = True
                    break
        
        return boundaries
    
    def _mark_semantic_units(self, text, semantic_units):
        """
        Mark semantic units in the text.
        
        Args:
            text: Original text
            semantic_units: List of semantic unit positions
            
        Returns:
            Text with marked semantic units (using brackets)
        """
        # Sort units by start position in reverse order
        sorted_units = sorted(semantic_units, key=lambda x: x['start'], reverse=True)
        
        # Insert unit markers
        result = list(text)
        for unit in sorted_units:
            if unit['type'] != 'topic_change':  # Skip topic change markers
                # Insert end marker
                result.insert(unit['end'], ' ]')
                # Insert start marker
                result.insert(unit['start'], '[ ')
        
        return ''.join(result)
    
    def _mark_adjusted_boundaries(self, text, adjusted_boundaries):
        """
        Mark adjusted boundaries in the text.
        
        Args:
            text: Original text
            adjusted_boundaries: List of boundary positions
            
        Returns:
            Text with marked boundaries (using brackets)
        """
        # Sort boundaries by position in reverse order
        sorted_boundaries = sorted(adjusted_boundaries, key=lambda x: x['position'], reverse=True)
        
        # Insert boundary markers
        result = list(text)
        for boundary in sorted_boundaries:
            pos = boundary['position']
            # Use different markers for adjusted vs. original boundaries
            if boundary.get('adjusted', False):
                marker = ' |* '  # Adjusted boundary
            else:
                marker = ' | '  # Original boundary
            result.insert(pos, marker)
        
        return ''.join(result)


class TranscriptEnhancementPipeline:
    """
    Pipeline for enhancing transcripts before clip generation.
    
    This class manages a sequence of processors that can be applied to
    transcripts before final clipping.
    """
    
    def __init__(self, processors=None, config=None):
        """
        Initialize the transcript enhancement pipeline.
        
        Args:
            processors: List of processor objects to apply
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Create default processors if none provided
        self.processors = processors or [
            FillerWordsProcessor(),
            RepetitionHandler(),
            SentenceBoundaryDetector(),
            SemanticUnitPreserver()
        ]
    
    def process(self, transcript, generate_report=False):
        """
        Run the transcript through the enhancement pipeline.
        
        Args:
            transcript: Transcript to process (text or structured data)
            generate_report: Whether to generate a report of changes
            
        Returns:
            Enhanced transcript, with optional report if requested
        """
        if transcript is None:
            raise ValueError("Cannot process None transcript")        
        # Keep original for reporting
        original_transcript = transcript
        # Process through each processor in sequence
        enhanced_transcript = transcript
        results = []
        
        for processor in self.processors:
            enhanced_transcript = processor.process(enhanced_transcript)
            results.append({
                'processor': processor.__class__.__name__,
                'result': enhanced_transcript
            })
        
        # Generate report if requested
        if generate_report:
            report = self.generate_report(original_transcript, enhanced_transcript, results)
            return enhanced_transcript, report
        
        return enhanced_transcript
    
    def generate_report(self, original, enhanced, processing_steps):
        """
        Generate a report of changes made during enhancement.
        
        Args:
            original: Original transcript
            enhanced: Enhanced transcript
            processing_steps: Results from each processing step
            
        Returns:
            Report of changes made
        """
        report = {
            'processing_steps': processing_steps,
            'summary': {
                'original_length': len(original) if isinstance(original, str) else None,
                'enhanced_length': len(enhanced) if isinstance(enhanced, str) else None,
            }
        }
        
        # Add more detailed analysis as needed
        if isinstance(original, str) and isinstance(enhanced, str):
            # Text-level analysis
            report['summary']['filler_words_removed'] = self._count_filler_words(original) - self._count_filler_words(enhanced)
            report['summary']['repetitions_handled'] = self._estimate_repetitions_handled(original, enhanced)
            
            # Calculate readability scores
            try:
                report['summary']['readability_improvement'] = self._calculate_readability_improvement(original, enhanced)
            except:
                # Skip readability calculation if it fails
                pass
        
        return report
    
    def _count_filler_words(self, text):
        """Count filler words in text."""
        filler_words = ['um', 'uh', 'like', 'you know', 'I mean', 'kind of', 'sort of']
        count = 0
        for filler in filler_words:
            count += sum(1 for _ in re.finditer(r'\b' + re.escape(filler) + r'\b', text, re.IGNORECASE))
        return count
    
    def _estimate_repetitions_handled(self, original, enhanced):
        """Estimate number of repetitions handled."""
        # Simple but imperfect method based on length reduction
        words_original = len(original.split())
        words_enhanced = len(enhanced.split())
        
        # Discount filler words to focus on repetition removal
        filler_count_diff = self._count_filler_words(original) - self._count_filler_words(enhanced)
        
        # Rough estimate: assume average repeated phrase is 5 words
        repetition_reduction = (words_original - words_enhanced - filler_count_diff) / 5
        
        return max(0, int(repetition_reduction))
    
    def _calculate_readability_improvement(self, original, enhanced):
        """Calculate improvement in readability scores."""
        # Basic improvement metric based on sentence length and complexity
        # In a real implementation, you might use a proper readability metric like Flesch-Kincaid
        
        def avg_sentence_length(text):
            sentences = re.split(r'[.!?]', text)
            words_per_sentence = [len(s.split()) for s in sentences if s.strip()]
            return sum(words_per_sentence) / len(words_per_sentence) if words_per_sentence else 0
        
        def avg_word_length(text):
            words = [w for w in text.split() if w.isalpha()]
            char_count = sum(len(w) for w in words)
            return char_count / len(words) if words else 0
        
        # Calculate metrics
        orig_sentence_len = avg_sentence_length(original)
        enhanced_sentence_len = avg_sentence_length(enhanced)
        
        orig_word_len = avg_word_length(original)
        enhanced_word_len = avg_word_length(enhanced)
        
        # Shorter sentences and similar word length suggests improved readability
        # Normalize to a percentage improvement for reporting
        sentence_improvement = (orig_sentence_len - enhanced_sentence_len) / orig_sentence_len
        
        # Combine factors (more sophisticated metrics would be better)
        return {'sentence_length_improvement': sentence_improvement * 100}


# Helper functions

def enhance_transcript(transcript, config=None, output_file=None):
    """
    Apply transcript enhancement pipeline with default settings.
    
    Args:
        transcript: Transcript to enhance (text or structured data)
        config: Optional configuration override
        output_file: Optional path to save enhanced transcript
        
    Returns:
        Enhanced transcript
    """
    pipeline = TranscriptEnhancementPipeline(config=config)
    enhanced_transcript = pipeline.process(transcript)
    
    # Save to file if output_file is provided
    if output_file:
        if isinstance(enhanced_transcript, str):
            # Save simple text
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(enhanced_transcript)
        elif isinstance(enhanced_transcript, (dict, list)):
            # Save structured data as JSON
            import json
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(enhanced_transcript, f, indent=2)
    
    return enhanced_transcript

def extract_enhanced_clips(
    video_file, 
    transcript_file, 
    output_dir=None, 
    config=None, 
    clip_prefix="clip",
    top_n=None,
    min_score=None,
    min_duration=None,
    max_duration=None,
    add_padding=0.5,
    use_ffmpeg=True,
    save_enhanced_transcript=True
):
    """
    Process transcript and extract enhanced clips.
    
    Args:
        video_file: Path to video file
        transcript_file: Path to transcript file
        output_dir: Directory to save clips
        config: Optional configuration for transcript enhancement
        clip_prefix: Prefix for output clip filenames
        top_n: Only extract the top N clips by importance score
        min_score: Only extract clips with importance score above this value
        min_duration: Only extract clips longer than this duration in seconds
        max_duration: Only extract clips shorter than this duration in seconds
        add_padding: Add padding in seconds before/after each clip
        use_ffmpeg: Use direct FFmpeg calls instead of MoviePy
        save_enhanced_transcript: Whether to save the enhanced transcript to a file
        
    Returns:
        List of extracted clip information
    """
    from .clip_extractor import extract_clips_from_json
    import json
    import logging
    from pathlib import Path
    
    logger = logging.getLogger(__name__)
    logger.info("Enhancing transcript before clip extraction")
    
    # Load transcript
    with open(transcript_file, 'r', encoding='utf-8') as f:
        transcript_data = json.load(f)
    
    # Apply enhancements
    if config is not None and 'processors' in config:
        pipeline = TranscriptEnhancementPipeline(processors=config['processors'])
        logger.info(f"Using custom processors: {[p.__class__.__name__ for p in config['processors']]}")
    else:
        pipeline = TranscriptEnhancementPipeline()
        logger.info("Using all transcript processors with default settings")
    
    enhanced_transcript, report = pipeline.process(transcript_data, generate_report=True)
    
    logger.info("Transcript enhancement complete")
    
    # Log some details about the enhancement
    if isinstance(report, dict) and 'summary' in report:
        summary = report['summary']
        if 'filler_words_removed' in summary:
            logger.info(f"Removed {summary['filler_words_removed']} filler words")
        if 'repetitions_handled' in summary:
            logger.info(f"Handled {summary['repetitions_handled']} repetitions")
    
    # Create output directory if not provided
    if output_dir is None:
        video_path = Path(video_file)
        output_dir = str(video_path.with_suffix('_clips'))
    
    # Create the directory if it doesn't exist
    Path(output_dir).mkdir(exist_ok=True)
    
    # Save enhanced transcript if requested
    if save_enhanced_transcript:
        # Use the transcript filename as a base
        transcript_path = Path(transcript_file)
        enhanced_transcript_filename = transcript_path.stem + "_enhanced" + transcript_path.suffix
        enhanced_transcript_path = str(Path(output_dir) / enhanced_transcript_filename)
        
        with open(enhanced_transcript_path, 'w', encoding='utf-8') as f:
            json.dump(enhanced_transcript, f, indent=2)
        
        logger.info(f"Saved enhanced transcript to: {enhanced_transcript_path}")
    
    # Create temporary file for enhanced transcript
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8') as f:
        json.dump(enhanced_transcript, f)
        enhanced_json_path = f.name
    
    try:
        # Extract clips based on enhanced transcript
        logger.info("Extracting clips from enhanced transcript")
        clips = extract_clips_from_json(
            video_file=video_file, 
            json_file=enhanced_json_path, 
            output_dir=output_dir,
            clip_prefix=clip_prefix,
            top_n=top_n,
            min_score=min_score,
            min_duration=min_duration,
            max_duration=max_duration,
            add_padding=add_padding,
            use_ffmpeg=use_ffmpeg
        )
        return clips
    finally:
        # Clean up temporary file
        import os
        os.unlink(enhanced_json_path)