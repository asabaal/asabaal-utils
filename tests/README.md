# Transcript Processors Test Suite

This directory contains test files for the transcript enhancement pipeline in the `asabaal_utils.video_processing.transcript_processors` module.

## Running Tests

### Run All Tests

To run all tests:

```bash
python -m tests.run_all_tests
```

### Run Specific Tests

To run a specific test file:

```bash
python -m unittest tests.test_transcript_processors
python -m unittest tests.test_srt_integration
python -m unittest tests.test_performance
```

To run a specific test class:

```bash
python -m unittest tests.test_transcript_processors.TestFillerWordsProcessor
```

To run a specific test method:

```bash
python -m unittest tests.test_transcript_processors.TestFillerWordsProcessor.test_remove_all_policy
```

### Run with pytest

If pytest is installed, you can also use:

```bash
pytest tests/
```

## Test Files

- `test_transcript_processors.py` - Core tests for all processor components
- `test_srt_integration.py` - Tests for SRT format handling
- `test_performance.py` - Performance tests for various transcript sizes
- `conftest.py` - Pytest fixtures and configuration

## Test Data

The tests use sample transcript data defined in the fixtures in `conftest.py`. 
These samples cover various scenarios including:

- Transcripts with filler words
- Transcripts with repetitions
- Transcripts with complex sentence structures
- Transcripts with semantic units
- Sample SRT format transcripts

## Adding Tests

When adding new tests:

1. Use the appropriate test file or create a new one if testing a different aspect
2. Add new test classes as subclasses of `unittest.TestCase`
3. Name test methods starting with `test_` followed by what they're testing
4. For common test data, consider adding fixtures to `conftest.py`

## Continuous Integration

These tests are designed to be run in a CI/CD environment. The test runner will 
return an exit code of 0 if all tests pass and 1 if any tests fail.