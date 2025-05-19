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
            ("continually", 5),
            ("impossible", 4),
            ("environment", 4),
        ]
        
        # Collect all errors instead of failing on first error
        errors = []
        for word, expected in test_cases:
            actual = count_syllables(word)
            if actual != expected:
                errors.append(f"Word '{word}': Expected {expected} syllables, got {actual}")
        
        # Report all errors at once
        if errors:
            self.fail("\n".join(["Syllable counting errors:"]+errors))
    
    def test_count_line_syllables(self):
        # Test complete lines
        test_cases = [
            ("Do you see it?", 4),
            ("Have you opened your eyes?", 6),
            ("Vision. Vision. This my vision, vision", 11),
            ("A house divided will not stand, its foundation fractured", 14),
        ]
        
        # Collect all errors instead of failing on first error
        errors = []
        for line, expected in test_cases:
            actual = count_line_syllables(line)
            if actual != expected:
                errors.append(f"Line '{line}': Expected {expected} syllables, got {actual}")
        
        # Report all errors at once
        if errors:
            self.fail("\n".join(["Line syllable counting errors:"]+errors))
    
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
            
            # Collect all errors instead of failing on first error
            errors = []
            
            # Check if the correct number of lines were processed
            if len(results) != 7:  # 6 lines + 1 empty line
                errors.append(f"Expected 7 lines in results, got {len(results)}")
            
            # Check specific line counts
            expected_counts = [
                (0, 0),  # [Verse] (section marker)
                (1, 6),  # Mourning, death, crying, pain
                (2, 9),  # Passed away is the order of old
                (3, 0),  # Empty line
                (4, 0),  # [Chorus] (section marker)
                (5, 4),  # Do you see it?
                (6, 6),  # Have you opened your eyes?
            ]
            
            for i, expected_count in expected_counts:
                if i < len(results):
                    actual_count = results[i][1]
                    if actual_count != expected_count:
                        line_text = results[i][0] if results[i][0] else "[Empty line]"
                        errors.append(f"Line {i} ('{line_text}'): Expected {expected_count} syllables, got {actual_count}")
                else:
                    errors.append(f"Missing line {i} in results")
            
            # Report all errors at once
            if errors:
                self.fail("\n".join(["Lyrics file analysis errors:"]+errors))
        finally:
            # Clean up the temporary file
            os.unlink(temp_file_path)


if __name__ == "__main__":
    # Add extra verbosity to show more details when running directly
    def run_test_with_report(test_method):
        try:
            test_method()
            print(f"✅ {test_method.__name__} passed!")
        except AssertionError as e:
            print(f"❌ {test_method.__name__} failed:")
            print(str(e))
    
    tester = TestSyllableCounter()
    print("Running syllable counter tests...\n")
    run_test_with_report(tester.test_count_syllables)
    run_test_with_report(tester.test_count_line_syllables)
    run_test_with_report(tester.test_analyze_lyrics_file)
    print("\nTest run completed.")
