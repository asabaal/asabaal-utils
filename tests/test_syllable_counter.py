import unittest
import tempfile
import os
from asabaal_utils.text_analysis.syllable_counter import (
    count_syllables,
    count_line_syllables,
    analyze_lyrics_file
)

class TestSyllableCounter(unittest.TestCase):
    def test_count_syllables(self):
        # Test simple words with known syllable counts
        test_cases = [
            ("hello", 2),
            ("world", 1),
            ("beautiful", 3),
            ("syllable", 3),
            ("counting", 2),
            ("implemented", 4),
            ("vision", 2),
            ("continually", 4),
            ("impossible", 4),
            ("environment", 4),
        ]
        
        for word, expected in test_cases:
            with self.subTest(word=word):
                self.assertEqual(count_syllables(word), expected)
    
    def test_count_line_syllables(self):
        # Test complete lines
        test_cases = [
            ("Do you see it?", 3),
            ("Have you opened your eyes?", 6),
            ("Vision. Vision. This my vision, vision", 9),
            ("A house divided will not stand, its foundation fractured", 16),
        ]
        
        for line, expected in test_cases:
            with self.subTest(line=line):
                self.assertEqual(count_line_syllables(line), expected)
    
    def test_analyze_lyrics_file(self):
        # Create a temporary file with test lyrics
        test_lyrics = (
            "[Verse]\n"
            "Mourning, death, crying, pain\n"
            "Passed away is the order of old\n\n"
            "[Chorus]\n"
            "Do you see it?\n"
            "Have you opened your eyes?\n"
        )
        
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
            temp_file.write(test_lyrics)
            temp_file_path = temp_file.name
        
        try:
            # Analyze the temporary file
            results = analyze_lyrics_file(temp_file_path)
            
            # Check if the correct number of lines were processed
            self.assertEqual(len(results), 7)  # 6 lines + 1 empty line
            
            # Check specific line counts
            self.assertEqual(results[0][1], 0)  # [Verse] (section marker)
            self.assertEqual(results[1][1], 5)  # Mourning, death, crying, pain
            self.assertEqual(results[2][1], 9)  # Passed away is the order of old
            self.assertEqual(results[3][1], 0)  # Empty line
            self.assertEqual(results[4][1], 0)  # [Chorus] (section marker)
            self.assertEqual(results[5][1], 3)  # Do you see it?
            self.assertEqual(results[6][1], 6)  # Have you opened your eyes?
        finally:
            # Clean up the temporary file
            os.unlink(temp_file_path)


if __name__ == '__main__':
    unittest.main()
