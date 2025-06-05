import os
import re
import json
from pathlib import Path
from collections import Counter
import mimetypes

class DocumentAnalyzer:
    def __init__(self):
        self.supported_formats = ['.txt', '.md', '.py', '.js', '.json', '.csv']
    
    def analyze_document(self, file_path_or_content, content_type=None):
        """
        Analyze a document and return comprehensive statistics
        """
        try:
            # Handle both file paths and direct content
            if os.path.exists(str(file_path_or_content)):
                with open(file_path_or_content, 'r', encoding='utf-8') as f:
                    content = f.read()
                file_ext = Path(file_path_or_content).suffix
            else:
                content = str(file_path_or_content)
                file_ext = content_type or '.txt'
            
            analysis = {
                "basic_stats": self._get_basic_stats(content),
                "readability": self._calculate_readability(content),
                "content_analysis": self._analyze_content(content),
                "structure": self._analyze_structure(content, file_ext),
                "metadata": {
                    "file_type": file_ext,
                    "encoding": "utf-8",
                    "analysis_version": "1.0"
                }
            }
            
            return {
                "success": True,
                "data": analysis,
                "message": "Document analyzed successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to analyze document"
            }
    
    def _get_basic_stats(self, content):
        """Calculate basic document statistics"""
        lines = content.split('\n')
        words = content.split()
        sentences = re.split(r'[.!?]+', content)
        
        return {
            "character_count": len(content),
            "character_count_no_spaces": len(content.replace(' ', '')),
            "word_count": len(words),
            "line_count": len(lines),
            "sentence_count": len([s for s in sentences if s.strip()]),
            "paragraph_count": len([p for p in content.split('\n\n') if p.strip()]),
            "average_words_per_sentence": round(len(words) / max(len(sentences), 1), 2),
            "average_characters_per_word": round(len(content.replace(' ', '')) / max(len(words), 1), 2)
        }
    
    def _calculate_readability(self, content):
        """Calculate readability scores"""
        words = content.split()
        sentences = re.split(r'[.!?]+', content)
        sentences = [s for s in sentences if s.strip()]
        
        if not words or not sentences:
            return {"flesch_reading_ease": 0, "reading_level": "Unable to calculate"}
        
        # Simple readability calculation
        avg_sentence_length = len(words) / len(sentences)
        avg_syllables = sum(self._count_syllables(word) for word in words) / len(words)
        
        flesch_score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables)
        
        if flesch_score >= 90:
            level = "Very Easy"
        elif flesch_score >= 80:
            level = "Easy"
        elif flesch_score >= 70:
            level = "Fairly Easy"
        elif flesch_score >= 60:
            level = "Standard"
        elif flesch_score >= 50:
            level = "Fairly Difficult"
        elif flesch_score >= 30:
            level = "Difficult"
        else:
            level = "Very Difficult"
        
        return {
            "flesch_reading_ease": round(flesch_score, 2),
            "reading_level": level,
            "avg_sentence_length": round(avg_sentence_length, 2),
            "avg_syllables_per_word": round(avg_syllables, 2)
        }
    
    def _count_syllables(self, word):
        """Estimate syllable count in a word"""
        word = word.lower()
        vowels = 'aeiouy'
        syllable_count = 0
        prev_was_vowel = False
        
        for char in word:
            if char in vowels:
                if not prev_was_vowel:
                    syllable_count += 1
                prev_was_vowel = True
            else:
                prev_was_vowel = False
        
        if word.endswith('e'):
            syllable_count -= 1
        
        return max(1, syllable_count)
    
    def _analyze_content(self, content):
        """Analyze content patterns and keywords"""
        words = re.findall(r'\b\w+\b', content.lower())
        word_freq = Counter(words)
        
        # Find common patterns
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content)
        phone_numbers = re.findall(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', content)
        
        return {
            "most_common_words": word_freq.most_common(10),
            "unique_words": len(set(words)),
            "lexical_diversity": round(len(set(words)) / max(len(words), 1), 3),
            "emails_found": len(emails),
            "urls_found": len(urls),
            "phone_numbers_found": len(phone_numbers),
            "has_code_blocks": bool(re.search(r'```|`.*`', content)),
            "has_markdown": bool(re.search(r'[#*\-\+]|\[.*\]\(.*\)', content))
        }
    
    def _analyze_structure(self, content, file_ext):
        """Analyze document structure based on file type"""
        structure = {
            "file_type": file_ext,
            "estimated_reading_time_minutes": round(len(content.split()) / 200, 1)
        }
        
        if file_ext == '.md':
            headers = re.findall(r'^#+\s+(.+)$', content, re.MULTILINE)
            structure["markdown_headers"] = len(headers)
            structure["header_hierarchy"] = headers[:10]  # First 10 headers
        
        elif file_ext in ['.py', '.js']:
            functions = re.findall(r'def\s+(\w+)|function\s+(\w+)', content)
            classes = re.findall(r'class\s+(\w+)', content)
            structure["functions_found"] = len(functions)
            structure["classes_found"] = len(classes)
        
        elif file_ext == '.json':
            try:
                json_data = json.loads(content)
                structure["json_valid"] = True
                structure["json_keys"] = list(json_data.keys()) if isinstance(json_data, dict) else "Array"
            except:
                structure["json_valid"] = False
        
        return structure

# Example usage function
def analyze_text_sample():
    """Test the analyzer with sample text"""
    analyzer = DocumentAnalyzer()
    
    sample_text = """
    # Sample Document
    
    This is a sample document for testing our document analyzer tool. 
    It contains multiple sentences and paragraphs to demonstrate the analysis capabilities.
    
    ## Features
    
    The analyzer can:
    - Count words, sentences, and paragraphs
    - Calculate readability scores
    - Find patterns like emails and URLs
    - Analyze document structure
    
    Contact us at info@example.com or visit https://example.com for more information.
    You can also call us at 555-123-4567.
    
    This tool will be very useful for content analysis and document processing tasks.
    """
    
    result = analyzer.analyze_document(sample_text, '.md')
    return json.dumps(result, indent=2)

if __name__ == "__main__":
    print(analyze_text_sample())
