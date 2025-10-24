# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.18.1
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Debug v2: Lyric Video Section Type Mapping Issue
#
# ## Problem Summary
# - analyze-structure SAVES correct types (hook, prechorus, interlude)
# - lyric video SHOWS wrong types (CHORUS, BRIDGE, INSTRUMENTAL)
#
# ## Step-by-Step Investigation

# %% [markdown]
# ## Step 1: Validate analyze-structure works correctly in isolation

# %%
# Cell 1.1: Run analyze-structure command and check output
import subprocess
import json
import os

# Clean up any existing output first
test_output = '/tmp/test_structure_final.json'
if os.path.exists(test_output):
    os.remove(test_output)

# Run analyze-structure
cmd = [
    'analyze-structure',
    '/mnt/d/Work/Asabaal Ventures/Asabaal/Vision/Week 4/WEEK 4/WEEK 4 - DRAFT AUDIO.mp3',
    '--structure-file', '/mnt/d/Work/Asabaal Ventures/Asabaal/Vision/Week 4/week4_structure_initial.json',
    '-o', test_output
]

print(f"Running: {' '.join(cmd)}")
result = subprocess.run(cmd, capture_output=True, text=True)

print(f"\nReturn code: {result.returncode}")
if result.returncode != 0:
    print(f"STDERR: {result.stderr}")
else:
    print("SUCCESS")

# %% [markdown]
# ## Step 2: Validate the saved output is correct

# %%
# Cell 2.1: Check the main output file
with open(test_output, 'r') as f:
    saved_structure = json.load(f)

print("=== SAVED STRUCTURE (main file) ===")
print("\nChecking key sections:")
for i in [1, 2, 4]:  # hook, interlude, prechorus
    section = saved_structure['time_sections'][i]
    print(f"Index {i}: type='{section['type']}', name='{section['name']}'")

# %%
# Cell 2.2: Check the video sections file that was auto-generated
video_sections_file = test_output.replace('.json', '_video_sections.json')
print(f"Looking for: {video_sections_file}")
print(f"Exists: {os.path.exists(video_sections_file)}")

if os.path.exists(video_sections_file):
    with open(video_sections_file, 'r') as f:
        video_sections = json.load(f)
    
    print("\n=== VIDEO SECTIONS FILE ===")
    print("\nChecking same key sections:")
    for i in [1, 2, 4]:  # hook, interlude, prechorus
        section = video_sections['sections'][i]
        print(f"Index {i}: type='{section['type']}', name='{section['name']}'")

# %% [markdown]
# ## Step 3: Investigate how lyric video creator extracts these points

# %%
# Cell 3.1: Import the lyric video components
import sys
sys.path.append('/home/asabaal/asabaal_ventures/repos/asabaal-utils/src')

from asabaal_utils.video_processing.lyric_video.structure_loader import StructureLoader
from asabaal_utils.video_processing.lyric_video.section_manager import SectionManager

print("Imports complete")

# %%
# Cell 3.2: Test the structure loader directly
loader = StructureLoader()
sections = loader.load_structure_file(video_sections_file)

print(f"StructureLoader loaded {len(sections)} sections")
print("\nKey sections after loading:")
for i in [1, 2, 4]:
    section = sections[i]
    print(f"Index {i}: name='{section.name}', section_type={section.section_type}")

# %%
# Cell 3.3: Check how the JSON is being parsed
# Let's trace through what happens in _load_json_format
import json

# Manually load and check
with open(video_sections_file, 'r') as f:
    raw_data = json.load(f)

print("Raw JSON data for section 1 (hook):")
print(raw_data['sections'][1])

print("\nRaw JSON data for section 4 (prechorus):")
print(raw_data['sections'][4])

# %% [markdown]
# ## Step 4: Show what's happening when lyric video loads the structure

# %%
# Cell 4.1: Simulate what section_manager does
manager = SectionManager()
loaded_sections = manager.load_structure_from_file(video_sections_file, 226.5)

print(f"SectionManager loaded {len(loaded_sections)} sections")
print("\nWhat SectionManager sees:")
for i in range(5):
    start, end, section_type = manager.sections[i]
    print(f"Index {i}: {section_type}")

# %%
# Cell 4.2: Check the logging output
# The lyric video logs "Song section structure:" - let's see what that's doing
manager.log_section_transitions(226.5)

# This should show us what's being logged

# %% [markdown]
# ## Step 5: Identify the issue and propose a fix

# %%
# Cell 5.1: Check if the issue is in _parse_section_type
# Test how the loader parses the 'type' field

test_types = ['hook', 'prechorus', 'interlude', 'chorus', 'bridge']

print("Testing _parse_section_type:")
for test_type in test_types:
    result = loader._parse_section_type(test_type)
    print(f"  '{test_type}' -> {result}")

# %%
# Cell 5.2: The issue might be that the 'type' field in the JSON
# is being mapped through type_mapping which converts:
# - 'chorus' (from type field) -> SectionType.CHORUS
# - 'bridge' (from type field) -> SectionType.BRIDGE
# But we want it to preserve the original types!

print("The issue: type_mapping in _save_lyric_video_format is converting:")
print("  SectionType.HOOK -> 'chorus' in JSON")
print("  SectionType.PRECHORUS -> 'bridge' in JSON")
print("\nThen when loading, these mapped types are used instead of the names!")

# %% [markdown]
# ## Step 6: Test the fix

# %%
# Cell 6.1: The fix should be to NOT map the types in the video sections file
# Instead, save the ORIGINAL type values

print("PROPOSED FIX:")
print("In _save_lyric_video_format, instead of using type_mapping,")
print("save the original section.section_type.value directly.")
print("\nThis way:")
print("  SectionType.HOOK -> 'hook' in JSON")
print("  SectionType.PRECHORUS -> 'prechorus' in JSON")
print("  SectionType.INTERLUDE -> 'interlude' in JSON")
