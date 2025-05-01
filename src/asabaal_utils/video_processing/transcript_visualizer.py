"""
Transcript enhancement visualizer for evaluating and visualizing 
the effectiveness of transcript enhancement.

This module provides tools to compare original and enhanced transcripts,
visualize enhancements, and evaluate the performance of the enhancement pipeline.
"""

import re
import difflib
import logging
from typing import Dict, List, Any, Optional, Tuple, Union, Set
from dataclasses import dataclass
from collections import defaultdict
import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from IPython.display import display, HTML, Markdown

logger = logging.getLogger(__name__)

class TranscriptEnhancementVisualizer:
    """
    Visualizes and evaluates the effectiveness of transcript enhancement.
    
    This class provides tools to compare original and enhanced transcripts,
    identify enhancement opportunities, and evaluate the performance of the
    enhancement pipeline.
    """
    
    def __init__(self):
        """Initialize the visualizer."""
        self.original_text = None
        self.enhanced_text = None
        
        # Enhancement categories with descriptions and colors for visualization
        self.enhancement_categories = {
            'repetition': {
                'color': 'red',
                'description': 'Repeated phrases'
            },
            'filler_words': {
                'pattern': r'\b(um|uh|like|you know|i mean|kind of|sort of)\b',
                'color': 'orange',
                'description': 'Filler words'
            },
            'false_starts': {
                'color': 'purple',
                'description': 'False starts'
            },
            'run_on': {
                'color': 'blue',
                'description': 'Run-on sentences'
            },
            'low_information': {
                'pattern': r'\b(okay|great|awesome|cool|alright|yeah|do do do|perfect){2,}',
                'color': 'green',
                'description': 'Low information content'
            }
        }
        
    def load_transcripts(self, original_path, enhanced_path=None):
        """Load transcripts from files."""
        with open(original_path, 'r', encoding='utf-8') as f:
            self.original_text = f.read()
        
        if enhanced_path:
            with open(enhanced_path, 'r', encoding='utf-8') as f:
                self.enhanced_text = f.read()
        
        return self.original_text, self.enhanced_text
        
    def load_transcript_strings(self, original_text, enhanced_text=None):
        """Load transcripts from strings."""
        self.original_text = original_text
        self.enhanced_text = enhanced_text
        return self.original_text, self.enhanced_text
    
    def preprocess_text(self, text):
        """Preprocess text to normalize line endings and combine relevant lines."""
        # Normalize line endings
        text = text.replace('\r\n', '\n')
        
        # Join short lines that appear to be part of the same sentence
        lines = text.split('\n')
        processed_lines = []
        current_line = ""
        
        for line in lines:
            line = line.strip()
            if not line:  # Skip empty lines
                if current_line:
                    processed_lines.append(current_line)
                    current_line = ""
                continue
                
            # If current line ends with certain patterns, it's likely complete
            if current_line and (current_line.endswith('.') or 
                               current_line.endswith('?') or 
                               current_line.endswith('!') or
                               len(current_line) > 80):  # Arbitrary threshold
                processed_lines.append(current_line)
                current_line = line
            else:
                if current_line:
                    current_line += " " + line
                else:
                    current_line = line
        
        # Don't forget the last line
        if current_line:
            processed_lines.append(current_line)
            
        return "\n".join(processed_lines)
    
    def find_repetitions(self, text):
        """Find repeated phrases across the entire text, not just within lines."""
        # Replace line breaks with spaces for continuous processing
        continuous_text = text.replace('\n', ' ').lower()
        
        # Tokenize into words
        words = re.findall(r'\b\w+\b', continuous_text)
        
        results = []
        min_phrase_length = 3  # Minimum words in a phrase to consider
        max_phrase_length = 7  # Maximum words in a phrase to check
        
        # For each phrase length
        for phrase_length in range(min_phrase_length, min(max_phrase_length + 1, len(words) // 2 + 1)):
            # Track phrases and their positions
            phrases = {}
            
            # Generate all phrases of current length
            for i in range(len(words) - phrase_length + 1):
                phrase = ' '.join(words[i:i+phrase_length])
                
                # Skip very short phrases or mostly stopwords
                if len(phrase) < 10 or self._is_low_information_phrase(phrase.split()):
                    continue
                
                # Record position
                if phrase in phrases:
                    phrases[phrase].append(i)
                else:
                    phrases[phrase] = [i]
            
            # Find phrases that repeat and are close together
            for phrase, positions in phrases.items():
                if len(positions) > 1:
                    # Check if positions are close enough (within 20 words)
                    for i in range(len(positions) - 1):
                        if positions[i+1] - positions[i] < 20:
                            # Find the actual positions in the original text
                            first_pos = self._find_phrase_position(text, phrase, positions[i], positions[i+1])
                            if first_pos != -1:
                                second_pos = text.lower().find(phrase, first_pos + 1)
                                if second_pos != -1:
                                    start = min(first_pos, second_pos)
                                    end = start + len(phrase)
                                    
                                    # Get line number
                                    line_number = text[:start].count('\n') + 1
                                    
                                    # Get context
                                    context_start = max(0, start - 30)
                                    context_end = min(len(text), end + 30)
                                    context = text[context_start:context_end]
                                    
                                    results.append({
                                        'category': 'repetition',
                                        'match': phrase,
                                        'start': start,
                                        'end': end,
                                        'context': context,
                                        'line_number': line_number,
                                        'color': self.enhancement_categories['repetition']['color'],
                                        'description': self.enhancement_categories['repetition']['description']
                                    })
        
        return results
    
    def _find_phrase_position(self, text, phrase, approx_pos, next_pos=None):
        """Find the actual position of a phrase in the text."""
        # Convert to lowercase for matching
        lower_text = text.lower()
        lower_phrase = phrase.lower()
        
        # First try direct search
        start_pos = lower_text.find(lower_phrase)
        if start_pos != -1:
            return start_pos
            
        # If not found, try more aggressive search (ignoring line breaks)
        continuous_text = lower_text.replace('\n', ' ')
        start_pos = continuous_text.find(lower_phrase)
        if start_pos != -1:
            # Map back to original text position (approximate)
            count = 0
            char_pos = 0
            
            for i, char in enumerate(text):
                if count >= start_pos:
                    return char_pos
                
                if char.lower() == continuous_text[count]:
                    count += 1
                    char_pos = i
        
        return -1
    
    def _is_low_information_phrase(self, phrase_tokens):
        """Determine if a phrase is mostly stopwords or very short words."""
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'if', 'of', 'at', 'by', 'for', 'to', 'in', 'with'}
        short_word_count = sum(1 for word in phrase_tokens if len(word) < 3 or word.lower() in stopwords)
        return short_word_count > len(phrase_tokens) * 0.6
    
    def find_false_starts(self, text):
        """Find false starts and abandoned phrases."""
        # Replace line breaks with spaces for continuous processing
        continuous_text = text.replace('\n', ' ')
        
        results = []
        
        # Common false start patterns
        patterns = [
            r"(I'(?:m|ll)|I (?:am|will)|so I'(?:m|ll)|and I'(?:m|ll)|I (?:want|need) to|I(?:'| )(?:was|thought)|(?:well|but|so|and|okay)\s+(?:I|we)).*?(?:\s+.*?){0,15}\1",
            r"(?:so I'(?:m|ll)|I'(?:m|ll) (?:going|trying) to).*?(?:\s+.*?){0,15}(?:(?:so )?I'(?:m|ll)(?: (?:going|trying) to)?)",
            r"(?:I'm|I am) here to tell you that.*?(?:\s+.*?){0,15}(?:I'm|I am)(?:.{0,30}?tell you)",
            r"(?:these files are|I just made).*?(?:\s+.*?){0,15}(?:these files are|I just made)"
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, continuous_text, re.IGNORECASE):
                start, end = match.span()
                
                # Get the line number
                line_number = text[:start].count('\n') + 1
                
                # Get context
                context_start = max(0, start - 30)
                context_end = min(len(text), end + 30)
                context = text[context_start:context_end]
                
                results.append({
                    'category': 'false_starts',
                    'match': match.group(0),
                    'start': start,
                    'end': end,
                    'context': context,
                    'line_number': line_number,
                    'color': self.enhancement_categories['false_starts']['color'],
                    'description': self.enhancement_categories['false_starts']['description']
                })
        
        return results
    
    def find_filler_words(self, text):
        """Find filler words across the entire text."""
        # Replace line breaks with spaces for continuous processing
        continuous_text = text.replace('\n', ' ')
        
        results = []
        pattern = self.enhancement_categories['filler_words']['pattern']
        
        for match in re.finditer(pattern, continuous_text, re.IGNORECASE):
            start, end = match.span()
            
            # Get the line number
            line_number = text[:start].count('\n') + 1
            
            # Get context
            context_start = max(0, start - 30)
            context_end = min(len(text), end + 30)
            context = text[context_start:context_end]
            
            results.append({
                'category': 'filler_words',
                'match': match.group(0),
                'start': start,
                'end': end,
                'context': context,
                'line_number': line_number,
                'color': self.enhancement_categories['filler_words']['color'],
                'description': self.enhancement_categories['filler_words']['description']
            })
        
        return results
    
    def find_run_on_sentences(self, text):
        """Find run-on sentences that could benefit from splitting."""
        # Replace line breaks with spaces for continuous processing
        continuous_text = text.replace('\n', ' ')
        
        results = []
        
        # Look for long sentences with multiple conjunctions
        sentences = re.split(r'[.!?]', continuous_text)
        
        for sentence in sentences:
            if len(sentence.split()) > 20:  # Long sentence
                # Count conjunctions
                conjunctions = len(re.findall(r'\b(and|but|so|or|because|that|which|when|if)\b', 
                                             sentence, re.IGNORECASE))
                
                if conjunctions > 2 or len(sentence.split()) > 35:  # Too many conjunctions or very long
                    start = continuous_text.find(sentence)
                    if start != -1:
                        end = start + len(sentence)
                        
                        # Map back to original text position
                        if text.replace('\n', ' ')[start:end] == sentence:
                            # Get the line number
                            line_number = text[:start].count('\n') + 1
                            
                            # Get context
                            context_start = max(0, start - 30)
                            context_end = min(len(text), end + 30)
                            context = text[context_start:context_end]
                            
                            results.append({
                                'category': 'run_on',
                                'match': sentence,
                                'start': start,
                                'end': end,
                                'context': context,
                                'line_number': line_number,
                                'color': self.enhancement_categories['run_on']['color'],
                                'description': self.enhancement_categories['run_on']['description']
                            })
        
        return results
    
    def find_low_information(self, text):
        """Find low-information content like repeated filler phrases."""
        # Replace line breaks with spaces for continuous processing
        continuous_text = text.replace('\n', ' ')
        
        results = []
        pattern = self.enhancement_categories['low_information']['pattern']
        
        for match in re.finditer(pattern, continuous_text, re.IGNORECASE):
            start, end = match.span()
            
            # Get the line number
            line_number = text[:start].count('\n') + 1
            
            # Get context
            context_start = max(0, start - 30)
            context_end = min(len(text), end + 30)
            context = text[context_start:context_end]
            
            results.append({
                'category': 'low_information',
                'match': match.group(0),
                'start': start,
                'end': end,
                'context': context,
                'line_number': line_number,
                'color': self.enhancement_categories['low_information']['color'],
                'description': self.enhancement_categories['low_information']['description']
            })
        
        return results
    
    def find_enhancements(self, text, category=None):
        """Find all instances of enhancement opportunities in the text."""
        if not text:
            return []
            
        results = []
        
        categories = [category] if category else self.enhancement_categories.keys()
        
        # Find each type of enhancement
        for cat in categories:
            if cat == 'repetition':
                results.extend(self.find_repetitions(text))
            elif cat == 'filler_words':
                results.extend(self.find_filler_words(text))
            elif cat == 'false_starts':
                results.extend(self.find_false_starts(text))
            elif cat == 'run_on':
                results.extend(self.find_run_on_sentences(text))
            elif cat == 'low_information':
                results.extend(self.find_low_information(text))
        
        # Sort by position in text
        results.sort(key=lambda x: x['start'])
        return results
    
    def identify_enhancement_chunks(self, max_distance=50):
        """Identify chunks of text that need enhancement."""
        if not self.original_text:
            return "Original text must be loaded."
            
        enhancements = self.find_enhancements(self.original_text)
        
        # Group enhancements that are close together
        chunks = []
        current_chunk = []
        
        for e in enhancements:
            if not current_chunk or e['start'] - current_chunk[-1]['end'] <= max_distance:
                current_chunk.append(e)
            else:
                # Find the text range for the chunk
                chunk_start = min(e['start'] for e in current_chunk)
                chunk_end = max(e['end'] for e in current_chunk)
                
                # Get the original text for this chunk
                chunk_text = self.original_text[chunk_start:chunk_end]
                
                chunks.append({
                    'start': chunk_start,
                    'end': chunk_end,
                    'text': chunk_text,
                    'enhancements': current_chunk,
                    'categories': set(e['category'] for e in current_chunk)
                })
                
                current_chunk = [e]
        
        # Don't forget the last chunk
        if current_chunk:
            chunk_start = min(e['start'] for e in current_chunk)
            chunk_end = max(e['end'] for e in current_chunk)
            chunk_text = self.original_text[chunk_start:chunk_end]
            
            chunks.append({
                'start': chunk_start,
                'end': chunk_end,
                'text': chunk_text,
                'enhancements': current_chunk,
                'categories': set(e['category'] for e in current_chunk)
            })
        
        return chunks
    
    def create_line_by_line_comparison(self):
        """Create a line-by-line comparison of original and enhanced texts."""
        if not self.original_text or not self.enhanced_text:
            return "Both original and enhanced texts must be loaded."
        
        original_lines = self.original_text.splitlines()
        enhanced_lines = self.enhanced_text.splitlines()
        
        # Create a list of dictionaries for the comparison
        comparison = []
        
        # Get the maximum number of lines
        max_lines = max(len(original_lines), len(enhanced_lines))
        
        for i in range(max_lines):
            orig_line = original_lines[i] if i < len(original_lines) else ""
            enh_line = enhanced_lines[i] if i < len(enhanced_lines) else ""
            
            # Check if the lines are different
            is_different = orig_line != enh_line
            
            # Find enhancements in the original line
            enhancements = []
            if orig_line:
                orig_line_enhancements = self.find_enhancements(orig_line)
                if orig_line_enhancements:
                    enhancements = [e['category'] for e in orig_line_enhancements]
            
            comparison.append({
                'Line Number': i + 1,
                'Original Line': orig_line,
                'Enhanced Line': enh_line,
                'Is Different': is_different,
                'Enhancement Categories': enhancements
            })
        
        return comparison
    
    def display_line_comparison(self, start_line=1, end_line=None):
        """Display line-by-line comparison in a notebook."""
        if not self.original_text or not self.enhanced_text:
            print("Both original and enhanced texts must be loaded.")
            return
            
        comparison = self.create_line_by_line_comparison()
        
        if end_line is None:
            end_line = len(comparison)
        
        # Filter the comparison
        filtered_df = [row for row in comparison 
                      if row['Line Number'] >= start_line and row['Line Number'] <= end_line]
        
        # Create HTML for display
        html_table = "<table class='comparison-table' style='width: 100%; border-collapse: collapse;'>"
        html_table += "<tr><th style='width: 5%;'>Line</th><th style='width: 45%;'>Original</th><th style='width: 45%;'>Enhanced</th><th style='width: 5%;'>Categories</th></tr>"
        
        for row in filtered_df:
            line_num = row['Line Number']
            orig_line = row['Original Line']
            enh_line = row['Enhanced Line']
            is_diff = row['Is Different']
            categories = row['Enhancement Categories']
            
            # Apply styling based on difference
            style = "background-color: #ffdddd;" if is_diff else ""
            
            # Create category indicators
            cat_indicators = ""
            for cat in categories:
                color = self.enhancement_categories[cat]['color']
                cat_indicators += f"<span style='color: {color};'>■</span> "
            
            html_table += f"<tr style='{style}'>"
            html_table += f"<td>{line_num}</td>"
            html_table += f"<td>{orig_line}</td>"
            html_table += f"<td>{enh_line}</td>"
            html_table += f"<td>{cat_indicators}</td>"
            html_table += "</tr>"
        
        html_table += "</table>"
        
        display(HTML(html_table))
    
    def display_enhancement_chunks(self):
        """Display chunks of text that need enhancement."""
        chunks = self.identify_enhancement_chunks()
        
        display(HTML("<h2>Enhancement Chunks</h2>"))
        display(HTML(f"<p>Found {len(chunks)} chunks of text needing enhancement</p>"))
        
        for i, chunk in enumerate(chunks[:20]):  # Show first 20 chunks
            categories = ", ".join(chunk['categories'])
            
            display(HTML(f"<h3>Chunk {i+1} ({categories})</h3>"))
            
            # Highlight enhancements in the chunk text
            highlighted_text = chunk['text']
            
            # Sort enhancements by end position in reverse order to avoid index shifts
            sorted_enhancements = sorted(chunk['enhancements'], key=lambda x: x['end'], reverse=True)
            
            for e in sorted_enhancements:
                # Calculate relative positions within the chunk
                rel_start = e['start'] - chunk['start']
                rel_end = e['end'] - chunk['start']
                
                # Skip if positions are out of bounds
                if rel_start < 0 or rel_end > len(highlighted_text):
                    continue
                    
                # Add highlighting
                highlight = f"<span style='background-color: {e['color']}; color: white;'>{highlighted_text[rel_start:rel_end]}</span>"
                highlighted_text = highlighted_text[:rel_start] + highlight + highlighted_text[rel_end:]
            
            display(HTML(f"<pre>{highlighted_text}</pre>"))
        
        if len(chunks) > 20:
            display(HTML(f"<p>... and {len(chunks) - 20} more chunks</p>"))
    
    def compare_enhancement_effectiveness(self):
        """Compare the effectiveness of the enhancement pipeline."""
        if not self.original_text or not self.enhanced_text:
            return "Both original and enhanced texts must be loaded."
        
        # Find enhancement opportunities in both texts
        original_enhancements = self.find_enhancements(self.original_text)
        enhanced_enhancements = self.find_enhancements(self.enhanced_text)
        
        # Count by category
        original_counts = {}
        enhanced_counts = {}
        
        for e in original_enhancements:
            cat = e['category']
            if cat not in original_counts:
                original_counts[cat] = 0
            original_counts[cat] += 1
        
        for e in enhanced_enhancements:
            cat = e['category']
            if cat not in enhanced_counts:
                enhanced_counts[cat] = 0
            enhanced_counts[cat] += 1
        
        # Create comparative data
        all_categories = set(list(original_counts.keys()) + list(enhanced_counts.keys()))
        comparison_data = []
        
        for cat in all_categories:
            orig_count = original_counts.get(cat, 0)
            enh_count = enhanced_counts.get(cat, 0)
            
            reduction = orig_count - enh_count
            reduction_pct = 0 if orig_count == 0 else (reduction / orig_count) * 100
            
            comparison_data.append({
                'Category': cat,
                'Original Count': orig_count,
                'Enhanced Count': enh_count,
                'Reduction': reduction,
                'Reduction %': reduction_pct
            })
        
        # Sort by reduction percentage
        comparison_data.sort(key=lambda x: x['Reduction %'], reverse=True)
        
        # Create a visualization of the comparison
        if plt:
            plt.figure(figsize=(12, 6))
            
            categories = [item['Category'] for item in comparison_data]
            orig_counts = [item['Original Count'] for item in comparison_data]
            enh_counts = [item['Enhanced Count'] for item in comparison_data]
            
            x = range(len(categories))
            width = 0.35
            
            plt.bar([i - width/2 for i in x], orig_counts, width, label='Original', color='red', alpha=0.7)
            plt.bar([i + width/2 for i in x], enh_counts, width, label='Enhanced', color='green', alpha=0.7)
            
            plt.xlabel('Enhancement Category')
            plt.ylabel('Count')
            plt.title('Enhancement Effectiveness Comparison')
            plt.xticks(x, categories)
            plt.legend()
            
            # Add percentage labels
            for i, item in enumerate(comparison_data):
                reduction_pct = item['Reduction %']
                if reduction_pct > 0:
                    plt.text(i, max(item['Original Count'], item['Enhanced Count']) + 1, 
                            f'-{reduction_pct:.1f}%', ha='center', color='blue')
            
            plt.tight_layout()
            plt.show()
        
        return comparison_data
    
    def create_enhancement_visualization(self):
        """Create a visualization of enhancement opportunities."""
        if not self.original_text:
            return "Original text must be loaded."
        
        # Get all enhancements
        all_enhancements = self.find_enhancements(self.original_text)
        
        # Create a list to track enhancement coverage
        coverage = [0] * len(self.original_text)
        
        # Mark areas covered by enhancements
        for e in all_enhancements:
            for i in range(e['start'], e['end']):
                if i < len(coverage):  # Safety check
                    coverage[i] = 1
        
        # Calculate enhancement density over segments
        segment_size = max(1, len(coverage) // 100)  # Divide into ~100 segments
        density = []
        
        for i in range(0, len(coverage), segment_size):
            segment = coverage[i:i+segment_size]
            density.append(sum(segment) / len(segment))
        
        # Create the visualization
        plt.figure(figsize=(15, 6))
        plt.plot(density, 'b-', linewidth=2)
        plt.fill_between(range(len(density)), density, alpha=0.3)
        plt.title('Enhancement Opportunity Density')
        plt.xlabel('Document Position (normalized)')
        plt.ylabel('Enhancement Density')
        plt.grid(True, alpha=0.3)
        
        # Add category markers
        for cat, info in self.enhancement_categories.items():
            cat_enhancements = self.find_enhancements(self.original_text, cat)
            
            if cat_enhancements:
                # Get positions
                positions = []
                for e in cat_enhancements:
                    pos = (e['start'] + e['end']) // 2
                    pos_normalized = pos // segment_size
                    if pos_normalized < len(density):
                        positions.append(pos_normalized)
                
                # Plot markers for a subset of positions to avoid overcrowding
                if len(positions) > 20:
                    positions = positions[:20]  # Take first 20 as sample
                
                plt.plot(positions, 
                         [density[p] for p in positions if p < len(density)],
                         'o', label=cat, color=info['color'], alpha=0.7)
        
        plt.legend()
        plt.tight_layout()
        plt.show()
        
        # Create a heatmap of enhancements by line and category
        lines = self.original_text.splitlines()
        heatmap_data = {}
        
        for i in range(1, len(lines)+1):
            heatmap_data[i] = {cat: 0 for cat in self.enhancement_categories.keys()}
        
        for e in all_enhancements:
            line_num = e['line_number']
            cat = e['category']
            if line_num <= len(lines) and line_num > 0:
                heatmap_data[line_num][cat] += 1
        
        # Convert to list format for heatmap
        heatmap_list = []
        for line_num, cats in heatmap_data.items():
            for cat, count in cats.items():
                heatmap_list.append({
                    'Line': line_num,
                    'Category': cat,
                    'Count': count
                })
        
        # Create heatmap
        if sns:
            plt.figure(figsize=(10, 8))
            
            # Reshape data for seaborn
            if heatmap_list:
                # Create a pivot table for easy visualization
                pivot_data = defaultdict(dict)
                for item in heatmap_list:
                    pivot_data[item['Line']][item['Category']] = item['Count']
                
                # Fill in zeros for missing values
                for line in pivot_data:
                    for cat in self.enhancement_categories:
                        if cat not in pivot_data[line]:
                            pivot_data[line][cat] = 0
                
                # Convert to array format
                lines = sorted(pivot_data.keys())
                cats = sorted(self.enhancement_categories.keys())
                data = np.zeros((len(lines), len(cats)))
                
                for i, line in enumerate(lines):
                    for j, cat in enumerate(cats):
                        data[i, j] = pivot_data[line].get(cat, 0)
                
                # Create heatmap
                ax = sns.heatmap(data, cmap="YlGnBu", linewidths=0.1, linecolor='white')
                
                # Set labels
                ax.set_yticks(np.arange(len(lines)) + 0.5)
                ax.set_yticklabels(lines)
                ax.set_xticks(np.arange(len(cats)) + 0.5)
                ax.set_xticklabels(cats)
                
                plt.title('Enhancement Opportunities by Line and Category')
                plt.ylabel('Line Number')
                plt.xlabel('Enhancement Category')
                plt.tight_layout()
                plt.show()

    def create_enhancement_report(self):
        """Create a detailed report of enhancement opportunities."""
        if not self.original_text:
            return "Original text must be loaded."
        
        enhancements = self.find_enhancements(self.original_text)
        
        # Group by category
        category_counts = {}
        category_examples = {}
        
        for e in enhancements:
            cat = e['category']
            if cat not in category_counts:
                category_counts[cat] = 0
                category_examples[cat] = []
            category_counts[cat] += 1
            
            # Store a limited number of examples per category
            if len(category_examples[cat]) < 5:
                category_examples[cat].append(e)
        
        # Create a list for the report
        report_data = []
        
        for cat, count in category_counts.items():
            color = self.enhancement_categories[cat]['color']
            description = self.enhancement_categories[cat]['description']
            
            report_data.append({
                'Category': cat,
                'Description': description,
                'Count': count,
                'Color': color,
                'Examples': category_examples[cat]
            })
        
        # Sort by count
        report_data.sort(key=lambda x: x['Count'], reverse=True)
        
        return report_data
    
    def display_enhancement_report(self):
        """Display enhancement opportunity report in a notebook."""
        report_data = self.create_enhancement_report()
        
        # Display summary table
        display(HTML("<h2>Enhancement Opportunity Summary</h2>"))
        
        summary_html = "<table style='width: 100%; border-collapse: collapse;'>"
        summary_html += "<tr><th style='text-align: left; padding: 8px; background-color: #f2f2f2;'>Category</th>"
        summary_html += "<th style='text-align: left; padding: 8px; background-color: #f2f2f2;'>Description</th>"
        summary_html += "<th style='text-align: right; padding: 8px; background-color: #f2f2f2;'>Count</th></tr>"
        
        for row in report_data:
            summary_html += f"<tr>"
            summary_html += f"<td style='padding: 8px; border: 1px solid #ddd;'>{row['Category']}</td>"
            summary_html += f"<td style='padding: 8px; border: 1px solid #ddd;'>{row['Description']}</td>"
            summary_html += f"<td style='padding: 8px; border: 1px solid #ddd; text-align: right;'>{row['Count']}</td>"
            summary_html += "</tr>"
        
        summary_html += "</table>"
        display(HTML(summary_html))
        
        # Display examples for each category
        display(HTML("<h2>Enhancement Examples</h2>"))
        
        for row in report_data:
            cat = row['Category']
            color = row['Color']
            count = row['Count']
            examples = row['Examples']
            
            display(HTML(f"<h3 style='color: {color};'>{cat.capitalize()}: {count} instances</h3>"))
            
            examples_html = "<table style='width: 100%; border-collapse: collapse;'>"
            examples_html += "<tr><th style='text-align: left; padding: 8px; background-color: #f2f2f2;'>Line Number</th>"
            examples_html += "<th style='text-align: left; padding: 8px; background-color: #f2f2f2;'>Content</th></tr>"
            
            for e in examples:
                # Highlight the matched text
                context = e['context']
                match_text = e['match']
                
                # Try to find the match in the context
                match_pos = context.lower().find(match_text.lower())
                if match_pos != -1:
                    highlighted_context = (
                        context[:match_pos] + 
                        f"<span style='background-color: {color}; color: white;'>{context[match_pos:match_pos+len(match_text)]}</span>" + 
                        context[match_pos+len(match_text):]
                    )
                else:
                    highlighted_context = context
                
                examples_html += f"<tr>"
                examples_html += f"<td style='padding: 8px; border: 1px solid #ddd;'>{e['line_number']}</td>"
                examples_html += f"<td style='padding: 8px; border: 1px solid #ddd;'>{highlighted_context}</td>"
                examples_html += "</tr>"
            
            examples_html += "</table>"
            display(HTML(examples_html))
    
    def evaluate_enhancement_pipeline(self):
        """Evaluate the enhancement pipeline by comparing original and enhanced texts."""
        if not self.original_text or not self.enhanced_text:
            return "Both original and enhanced texts must be loaded."
        
        # Find enhancement opportunities in both texts
        original_enhancements = self.find_enhancements(self.original_text)
        enhanced_enhancements = self.find_enhancements(self.enhanced_text)
        
        # Calculate statistics
        original_length = len(self.original_text)
        enhanced_length = len(self.enhanced_text)
        
        length_reduction = original_length - enhanced_length
        length_reduction_pct = 0 if original_length == 0 else (length_reduction / original_length) * 100
        
        # Count enhancements by category
        original_counts = defaultdict(int)
        enhanced_counts = defaultdict(int)
        
        for e in original_enhancements:
            original_counts[e['category']] += 1
        
        for e in enhanced_enhancements:
            enhanced_counts[e['category']] += 1
        
        # Calculate reduction by category
        categories = set(original_counts.keys()) | set(enhanced_counts.keys())
        category_reductions = {}
        
        for cat in categories:
            orig = original_counts[cat]
            enh = enhanced_counts[cat]
            reduction = orig - enh
            reduction_pct = 0 if orig == 0 else (reduction / orig) * 100
            
            category_reductions[cat] = {
                'original': orig,
                'enhanced': enh,
                'reduction': reduction,
                'reduction_pct': reduction_pct
            }
        
        # Calculate overall effectiveness
        total_original = sum(original_counts.values())
        total_enhanced = sum(enhanced_counts.values())
        total_reduction = total_original - total_enhanced
        total_reduction_pct = 0 if total_original == 0 else (total_reduction / total_original) * 100
        
        # Compile results
        results = {
            'text_length': {
                'original': original_length,
                'enhanced': enhanced_length,
                'reduction': length_reduction,
                'reduction_pct': length_reduction_pct
            },
            'enhancements': {
                'original': total_original,
                'enhanced': total_enhanced,
                'reduction': total_reduction,
                'reduction_pct': total_reduction_pct
            },
            'categories': category_reductions
        }
        
        return results
        
    def display_evaluation_results(self):
        """Display evaluation results in a notebook."""
        results = self.evaluate_enhancement_pipeline()
        
        if not isinstance(results, dict):
            print(results)  # Error message
            return
        
        display(HTML("<h2>Enhancement Pipeline Evaluation</h2>"))
        
        # Display text length information
        text_length = results['text_length']
        display(HTML("<h3>Text Length</h3>"))
        
        length_html = "<table style='width: 100%; border-collapse: collapse;'>"
        length_html += "<tr><th style='text-align: left; padding: 8px; background-color: #f2f2f2;'>Metric</th>"
        length_html += "<th style='text-align: right; padding: 8px; background-color: #f2f2f2;'>Value</th></tr>"
        
        length_html += f"<tr><td style='padding: 8px; border: 1px solid #ddd;'>Original Length</td>"
        length_html += f"<td style='padding: 8px; border: 1px solid #ddd; text-align: right;'>{text_length['original']} characters</td></tr>"
        
        length_html += f"<tr><td style='padding: 8px; border: 1px solid #ddd;'>Enhanced Length</td>"
        length_html += f"<td style='padding: 8px; border: 1px solid #ddd; text-align: right;'>{text_length['enhanced']} characters</td></tr>"
        
        length_html += f"<tr><td style='padding: 8px; border: 1px solid #ddd;'>Reduction</td>"
        length_html += f"<td style='padding: 8px; border: 1px solid #ddd; text-align: right;'>{text_length['reduction']} characters ({text_length['reduction_pct']:.1f}%)</td></tr>"
        
        length_html += "</table>"
        display(HTML(length_html))
        
        # Display enhancement count information
        enhancements = results['enhancements']
        display(HTML("<h3>Enhancement Opportunities</h3>"))
        
        enhancements_html = "<table style='width: 100%; border-collapse: collapse;'>"
        enhancements_html += "<tr><th style='text-align: left; padding: 8px; background-color: #f2f2f2;'>Metric</th>"
        enhancements_html += "<th style='text-align: right; padding: 8px; background-color: #f2f2f2;'>Value</th></tr>"
        
        enhancements_html += f"<tr><td style='padding: 8px; border: 1px solid #ddd;'>Original Enhancement Opportunities</td>"
        enhancements_html += f"<td style='padding: 8px; border: 1px solid #ddd; text-align: right;'>{enhancements['original']}</td></tr>"
        
        enhancements_html += f"<tr><td style='padding: 8px; border: 1px solid #ddd;'>Enhanced Enhancement Opportunities</td>"
        enhancements_html += f"<td style='padding: 8px; border: 1px solid #ddd; text-align: right;'>{enhancements['enhanced']}</td></tr>"
        
        enhancements_html += f"<tr><td style='padding: 8px; border: 1px solid #ddd;'>Reduction</td>"
        enhancements_html += f"<td style='padding: 8px; border: 1px solid #ddd; text-align: right;'>{enhancements['reduction']} ({enhancements['reduction_pct']:.1f}%)</td></tr>"
        
        enhancements_html += "</table>"
        display(HTML(enhancements_html))
        
        # Display category breakdown
        categories = results['categories']
        display(HTML("<h3>Enhancement Categories</h3>"))
        
        categories_html = "<table style='width: 100%; border-collapse: collapse;'>"
        categories_html += "<tr><th style='text-align: left; padding: 8px; background-color: #f2f2f2;'>Category</th>"
        categories_html += "<th style='text-align: right; padding: 8px; background-color: #f2f2f2;'>Original</th>"
        categories_html += "<th style='text-align: right; padding: 8px; background-color: #f2f2f2;'>Enhanced</th>"
        categories_html += "<th style='text-align: right; padding: 8px; background-color: #f2f2f2;'>Reduction</th>"
        categories_html += "<th style='text-align: right; padding: 8px; background-color: #f2f2f2;'>Reduction %</th></tr>"
        
        # Sort categories by reduction percentage
        sorted_categories = sorted(categories.items(), 
                                  key=lambda x: x[1]['reduction_pct'], 
                                  reverse=True)
        
        for cat, data in sorted_categories:
            categories_html += f"<tr>"
            categories_html += f"<td style='padding: 8px; border: 1px solid #ddd;'>{cat}</td>"
            categories_html += f"<td style='padding: 8px; border: 1px solid #ddd; text-align: right;'>{data['original']}</td>"
            categories_html += f"<td style='padding: 8px; border: 1px solid #ddd; text-align: right;'>{data['enhanced']}</td>"
            categories_html += f"<td style='padding: 8px; border: 1px solid #ddd; text-align: right;'>{data['reduction']}</td>"
            categories_html += f"<td style='padding: 8px; border: 1px solid #ddd; text-align: right;'>{data['reduction_pct']:.1f}%</td>"
            categories_html += "</tr>"
        
        categories_html += "</table>"
        display(HTML(categories_html))
        
        # Create visualization
        if plt:
            plt.figure(figsize=(10, 6))
            
            # Enhancement reduction by category
            cats = [cat for cat, _ in sorted_categories]
            orig_values = [data['original'] for _, data in sorted_categories]
            enh_values = [data['enhanced'] for _, data in sorted_categories]
            
            x = range(len(cats))
            width = 0.35
            
            plt.bar([i - width/2 for i in x], orig_values, width, label='Original', color='red', alpha=0.7)
            plt.bar([i + width/2 for i in x], enh_values, width, label='Enhanced', color='green', alpha=0.7)
            
            plt.xlabel('Category')
            plt.ylabel('Enhancement Opportunities')
            plt.title('Enhancement Reduction by Category')
            plt.xticks(x, cats)
            plt.legend()
            
            # Add percentage labels
            for i, (_, data) in enumerate(sorted_categories):
                if data['reduction_pct'] > 0:
                    plt.text(i, max(data['original'], data['enhanced']) + 1, 
                            f'-{data["reduction_pct"]:.1f}%', ha='center', color='blue')
            
            plt.tight_layout()
            plt.show()


def visualize_enhancement(original_file, enhanced_file=None):
    """
    Visualize the enhancement of a transcript.
    
    Args:
        original_file: Path to the original transcript
        enhanced_file: Path to the enhanced transcript (optional)
        
    Returns:
        Visualizer object with loaded transcripts
    """
    visualizer = TranscriptEnhancementVisualizer()
    
    # Load transcripts
    if enhanced_file:
        visualizer.load_transcripts(original_file, enhanced_file)
    else:
        visualizer.load_transcripts(original_file)
    
    # Display summary report
    visualizer.display_enhancement_report()
    
    # Visualize enhancement density
    visualizer.create_enhancement_visualization()
    
    # If enhanced file provided, evaluate effectiveness
    if enhanced_file:
        visualizer.display_evaluation_results()
    
    return visualizer


def generate_enhancement_report(original_file, enhanced_file=None, output_file=None):
    """
    Generate a comprehensive enhancement report and optionally save to file.
    
    Args:
        original_file: Path to the original transcript
        enhanced_file: Path to the enhanced transcript (optional)
        output_file: Path to save the report (optional)
        
    Returns:
        Report data
    """
    visualizer = TranscriptEnhancementVisualizer()
    
    # Load transcripts
    if enhanced_file:
        visualizer.load_transcripts(original_file, enhanced_file)
    else:
        visualizer.load_transcripts(original_file)
    
    # Generate report
    report = {}
    
    # Add enhancement opportunities
    report['enhancement_opportunities'] = visualizer.create_enhancement_report()
    
    # Add enhancement chunks
    report['enhancement_chunks'] = visualizer.identify_enhancement_chunks()
    
    # Add evaluation if enhanced file provided
    if enhanced_file:
        report['evaluation'] = visualizer.evaluate_enhancement_pipeline()
    
    # Save to file if requested
    if output_file:
        # Convert report to JSON-compatible format
        json_report = {
            'enhancement_opportunities': [
                {k: v for k, v in item.items() if k != 'Examples'}
                for item in report['enhancement_opportunities']
            ],
            'enhancement_chunks': [
                {
                    'start': chunk['start'],
                    'end': chunk['end'],
                    'text': chunk['text'],
                    'categories': list(chunk['categories'])
                }
                for chunk in report['enhancement_chunks']
            ]
        }
        
        if 'evaluation' in report:
            json_report['evaluation'] = report['evaluation']
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_report, f, indent=2)
    
    return report
