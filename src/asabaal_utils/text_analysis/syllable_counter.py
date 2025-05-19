import re
import sys
import csv
import nltk
from nltk.corpus import cmudict
from pathlib import Path

# Download CMU dictionary if not already downloaded
try:
    d = cmudict.dict()
except LookupError:
    nltk.download('cmudict')
    d = cmudict.dict()

def count_syllables(word):
    """
    Count syllables in a word using CMU pronunciation dictionary.
    If word is not found, use a fallback method.
    """
    word = word.lower()
    
    # Remove non-alphabetic characters
    word = re.sub(r'[^a-z]', '', word)
    
    if not word:
        return 0
    
    # Check if word is in the CMU dictionary
    if word in d:
        # Count vowel phonemes in the first pronunciation
        return max([len(list(y for y in x if y[-1].isdigit())) for x in d[word]])
    else:
        # Fallback: count vowel groups
        return count_syllables_fallback(word)

def count_syllables_fallback(word):
    """
    Fallback method for counting syllables.
    Counts vowel groups, with some adjustments for English syllable patterns.
    """
    word = word.lower()
    
    # Remove non-alphabetic characters
    word = re.sub(r'[^a-z]', '', word)
    
    if not word:
        return 0
        
    # Count vowel groups
    count = len(re.findall(r'[aeiouy]+', word))
    
    # Adjust for common patterns
    if word.endswith('e'):
        count -= 1
    if word.endswith('le') and len(word) > 2 and word[-3] not in 'aeiouy':
        count += 1
    if count == 0:
        count = 1
        
    return count

def count_line_syllables(line):
    """
    Count syllables in a line of text.
    """
    # Remove punctuation and split into words
    words = re.findall(r'\b[a-zA-Z\']+\b', line)
    return sum(count_syllables(word) for word in words)

def analyze_lyrics_file(file_path):
    """
    Analyze lyrics for syllable count from a file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        results = []
        for line in lines:
            line = line.strip()
            if line == '':
                results.append((line, 0))
            else:
                syllable_count = count_line_syllables(line)
                results.append((line, syllable_count))
        
        return results
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return []
    except Exception as e:
        print(f"Error reading file: {e}")
        return []

def detect_sections(lines):
    """
    Attempt to detect song sections (verse, chorus, etc.) based on common section markers.
    """
    section_markers = [
        r'^\s*\[.*\]\s*$',              # [Section]
        r'^\s*verse\s*[\d:]*\s*$',      # Verse or Verse 1:
        r'^\s*chorus\s*[\d:]*\s*$',     # Chorus or Chorus:
        r'^\s*bridge\s*[\d:]*\s*$',     # Bridge or Bridge:
        r'^\s*intro\s*[\d:]*\s*$',      # Intro or Intro:
        r'^\s*outro\s*[\d:]*\s*$',      # Outro or Outro:
        r'^\s*pre.?chorus\s*[\d:]*\s*$', # Pre-Chorus or Prechorus:
        r'^\s*hook\s*[\d:]*\s*$',       # Hook or Hook:
    ]
    
    current_section = "Unknown"
    sections = []
    
    for i, (line, _) in enumerate(lines):
        # Check if this line is a section marker
        for pattern in section_markers:
            if re.match(pattern, line, re.IGNORECASE):
                current_section = line.strip()
                break
        
        sections.append(current_section)
    
    return sections

def print_analysis(results, sections=None):
    """
    Print analysis results with formatting and optional section information.
    """
    print("\nSYLLABLE COUNT ANALYSIS\n")
    if sections:
        print("{:<15} | {:<50} | {:<10}".format("Section", "Line", "Syllables"))
        print("-" * 80)
    else:
        print("{:<60} | {:<10}".format("Line", "Syllables"))
        print("-" * 75)
    
    current_section = None
    
    for i, (line, count) in enumerate(results):
        if count == 0 and line.strip() == '':
            print()
            continue
            
        if sections:
            section = sections[i]
            # Only print section if it changed
            display_section = section if section != current_section else ""
            current_section = section
            
            formatted_line = line[:47] + "..." if len(line) > 50 else line
            print("{:<15} | {:<50} | {:<10}".format(display_section, formatted_line, count))
        else:
            formatted_line = line[:57] + "..." if len(line) > 60 else line
            print("{:<60} | {:<10}".format(formatted_line, count))

def calculate_statistics(results, sections=None):
    """
    Calculate and print statistics, optionally grouped by section.
    """
    # Filter out empty lines
    filtered_results = [(line, count) for line, count in results if count > 0]
    
    if not filtered_results:
        print("\nNo data to analyze.")
        return
    
    # Overall statistics
    counts = [count for _, count in filtered_results]
    avg = sum(counts) / len(counts)
    
    print("\nOVERALL STATISTICS:")
    print(f"Total lines: {len(counts)}")
    print(f"Average syllables per line: {avg:.1f}")
    print(f"Minimum syllables: {min(counts)}")
    print(f"Maximum syllables: {max(counts)}")
    
    # Section-based statistics if sections are detected
    if sections:
        print("\nSTATISTICS BY SECTION:")
        unique_sections = set(sections)
        
        for section in unique_sections:
            if section.strip() == '':
                continue
                
            # Get all lines from this section
            section_lines = [(line, count) for (line, count), sec in zip(results, sections) 
                           if sec == section and count > 0]
            
            if section_lines:
                section_counts = [count for _, count in section_lines]
                section_avg = sum(section_counts) / len(section_counts)
                print(f"\n{section}:")
                print(f"  Lines: {len(section_counts)}")
                print(f"  Average syllables: {section_avg:.1f}")
                print(f"  Min: {min(section_counts)}, Max: {max(section_counts)}")
    
    # Identify potential rhythm issues
    threshold = avg * 1.5
    long_lines = [(line, count, i) for i, ((line, count), _) in enumerate(zip(results, sections if sections else [None] * len(results))) 
                 if count > threshold and count > 0]
    
    if long_lines:
        print("\nPOTENTIAL RHYTHM ISSUES:")
        print("These lines have significantly more syllables than average:")
        for line, count, i in long_lines:
            formatted_line = line[:47] + "..." if len(line) > 50 else line
            if sections:
                print(f"  - {sections[i]}: \"{formatted_line}\" ({count} syllables)")
            else:
                print(f"  - \"{formatted_line}\" ({count} syllables)")

def export_to_csv(results, sections, output_path):
    """
    Export analysis results to a CSV file.
    """
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            if sections:
                writer.writerow(['Line Number', 'Section', 'Line', 'Syllables'])
                for i, ((line, count), section) in enumerate(zip(results, sections)):
                    if count > 0 or line.strip():  # Skip empty lines
                        writer.writerow([i+1, section, line, count])
            else:
                writer.writerow(['Line Number', 'Line', 'Syllables'])
                for i, (line, count) in enumerate(results):
                    if count > 0 or line.strip():  # Skip empty lines
                        writer.writerow([i+1, line, count])
                        
        print(f"\nResults exported to {output_path}")
        return True
    except Exception as e:
        print(f"Error exporting to CSV: {e}")
        return False

def export_statistics_to_csv(results, sections, output_path):
    """
    Export statistics to a CSV file.
    """
    try:
        # Filter out empty lines
        filtered_results = [(line, count) for line, count in results if count > 0]
        
        if not filtered_results:
            print("\nNo data to analyze for statistics export.")
            return False
        
        # Calculate overall statistics
        counts = [count for _, count in filtered_results]
        avg = sum(counts) / len(counts)
        threshold = avg * 1.5
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write overall statistics
            writer.writerow(['OVERALL STATISTICS'])
            writer.writerow(['Total lines', len(counts)])
            writer.writerow(['Average syllables per line', f"{avg:.1f}"])
            writer.writerow(['Minimum syllables', min(counts)])
            writer.writerow(['Maximum syllables', max(counts)])
            writer.writerow([])
            
            # Write section-based statistics if sections are detected
            if sections:
                writer.writerow(['STATISTICS BY SECTION'])
                writer.writerow(['Section', 'Lines', 'Average syllables', 'Min', 'Max'])
                
                unique_sections = set(sections)
                for section in unique_sections:
                    if section.strip() == '':
                        continue
                    
                    # Get all lines from this section
                    section_lines = [(line, count) for (line, count), sec in zip(results, sections) 
                                  if sec == section and count > 0]
                    
                    if section_lines:
                        section_counts = [count for _, count in section_lines]
                        section_avg = sum(section_counts) / len(section_counts)
                        writer.writerow([section, len(section_counts), f"{section_avg:.1f}", 
                                        min(section_counts), max(section_counts)])
                        
                writer.writerow([])
            
            # Write potential rhythm issues
            long_lines = [(line, count, i) for i, ((line, count), _) in 
                         enumerate(zip(results, sections if sections else [None] * len(results))) 
                         if count > threshold and count > 0]
            
            if long_lines:
                writer.writerow(['POTENTIAL RHYTHM ISSUES'])
                if sections:
                    writer.writerow(['Section', 'Line', 'Syllables'])
                    for line, count, i in long_lines:
                        writer.writerow([sections[i], line, count])
                else:
                    writer.writerow(['Line', 'Syllables'])
                    for line, count, _ in long_lines:
                        writer.writerow([line, count])
        
        print(f"\nStatistics exported to {output_path}")
        return True
    except Exception as e:
        print(f"Error exporting statistics to CSV: {e}")
        return False
