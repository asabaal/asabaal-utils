# Spec-Coder E2E Test Issues Analysis

## Issues Identified

### 1. **Hardcoded Music Project Remnants in Templates** 
**Location**: `src/asabaal_utils/agents/spec_coder/templates.py:17`
**Issue**: Hardcoded module docstring `"Rhythmic Pulse Generator\\nImplements deterministic rhythmic pattern generation."`
**Impact**: Injects music-related content into every generated scaffold, causing tests to be generated for music functions that don't exist in the spec
**Solution**: Remove hardcoded music content and make template generic or derive from actual spec

### 2. **Hardcoded Paths in Test Functions** 
**Locations**: 
- `src/asabaal_utils/agents/spec_coder/align_behaviors.py:349` 
- `src/asabaal_utils/agents/spec_coder/compare_behaviors.py:357`
- `src/asabaal_utils/agents/spec_coder/tester.py:206`
- `src/asabaal_utils/agents/spec_coder/analyze_tests.py:162`
**Issue**: Hardcoded paths to `/home/asabaal/repos/music_creation/qa_test_project/reference/openspec/specs/rhythmic_pulse_generator.yml`
**Impact**: May cause fallback to music project specs during testing/alignment
**Solution**: Remove hardcoded paths or make them configurable parameters

### 3. **Subprocess Isolation Issues**
**Issue**: The subprocess calls (`aggregate_behaviors`, `build_logic_catalog`, `generate_prompts`) are finding files from outside the temp directory
**Impact**: Generates prompt files for functions not in the e2e test spec (9-12 extra prompt files)
**Solution**: Ensure subprocess calls are properly isolated to only see temp directory contents

### 4. **Template-Generated Test Mismatch**
**Issue**: Generated test file contains functions (`generate_rhythmic_pattern`, `calculate_pulse_width`) not in e2e spec, and wrong expectations for `basic_function` (expects `True` but spec says `int`)
**Impact**: 0% alignment rate because test behaviors don't match spec requirements
**Solution**: Fix templates to generate tests that match actual spec content

### 5. **Fallback Test Generation**
**Location**: `src/asabaal_utils/agents/spec_coder/generator.py:503-515`
**Issue**: Fallback tests use `assert True` causing false passes
**Impact**: Tests pass but provide no real validation
**Solution**: Already fixed - changed to `pytest.fail()` for proper failure indication

## Root Cause Analysis

**Primary Root Cause**: Issue #1 (hardcoded music content in templates) is the main driver of the hallucinations, causing the entire pipeline to generate music-related artifacts regardless of the input spec.

**Secondary Root Cause**: Issue #3 (subprocess isolation) allows external files to influence the pipeline, creating the additional prompt files problem.

The alignment rate issue is a **symptom** of these root causes, not the core problem itself.

## Test Results Summary

- **Good**: `basic_function` prompt and code were generated
- **Neutral**: 0% alignment rate (due to unclear spec and template issues)
- **Bad**: 9-12 additional prompt files generated from music project remnants

## Fix Implementation Plan

1. Fix hardcoded music content in templates.py
2. Remove hardcoded paths in test functions
3. Improve subprocess isolation
4. Verify template-generated tests match spec
5. Test and validate fixes

Generated: 2025-10-17
Investigation: E2E Pipeline Test Issues