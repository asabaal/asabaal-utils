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
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Debug: Structure Flow from Analyze → Lyric Video
#
# ## Goal: Show EXACTLY where section types get changed

# %% [markdown]
# ## Part 1: What SHOULD happen

# %%
# What we WANT:
print("DESIRED FLOW:")
print("1. analyze-structure detects: type='hook', name='hook'")
print("2. Saves to video_sections.json: type='hook', name='hook'")
print("3. Lyric video loads: type='hook', name='hook'")
print("4. Lyric video displays: HOOK")

# %% [markdown]
# ## Part 2: Test current analyze-structure output

# %%
# Run analyze-structure fresh
import subprocess
import json
import os

test_output = '/tmp/debug_structure.json'
cmd = [
    'analyze-structure',
    '/mnt/d/Work/Asabaal Ventures/Asabaal/Vision/Week 4/WEEK 4/WEEK 4 - DRAFT AUDIO.mp3',
    '--structure-file', '/mnt/d/Work/Asabaal Ventures/Asabaal/Vision/Week 4/week4_structure_initial.json',
    '-o', test_output
]

result = subprocess.run(cmd, capture_output=True, text=True)
print(f"Return code: {result.returncode}")

# Check what was saved
video_sections_file = test_output.replace('.json', '_video_sections.json')
print(f"\nVideo sections file: {video_sections_file}")
print(f"Exists: {os.path.exists(video_sections_file)}")

# %%
# Check what's in the video sections file
if os.path.exists(video_sections_file):
    with open(video_sections_file, 'r') as f:
        video_data = json.load(f)
    
    print("VIDEO SECTIONS FILE CONTENT:")
    print("Section 1 (should be hook):")
    print(json.dumps(video_data['sections'][1], indent=2))
    print("\nSection 4 (should be prechorus):")
    print(json.dumps(video_data['sections'][4], indent=2))

# %% [markdown]
# ## Part 3: Trace how lyric video loads this

# %%
# Import the structure loader
import sys
sys.path.append('/home/asabaal/asabaal_ventures/repos/asabaal-utils/src')
from asabaal_utils.video_processing.lyric_video.structure_loader import StructureLoader, SectionType

# Check what SectionType values exist
print("Available SectionType values:")
for st in SectionType:
    print(f"  {st.name} = '{st.value}'")

# %%
# Load the structure file
loader = StructureLoader()
sections = loader.load_structure_file(video_sections_file)

print(f"\nLoaded {len(sections)} sections")
print("\nSection 1:")
s = sections[1]
print(f"  name: '{s.name}'")
print(f"  section_type: {s.section_type}")
print(f"  section_type.value: '{s.section_type.value}'")

# %%
# Check what happens when parsing 'hook' type
test_json = '{"type": "hook"}'
print("Testing _parse_section_type with 'hook':")

# This is what the loader does:
try:
    # First it tries direct enum lookup
    result = SectionType('hook')
    print(f"  Direct enum lookup: SUCCESS - {result}")
except ValueError as e:
    print(f"  Direct enum lookup: FAILED - {e}")
    # Then it falls back to name mapping
    print("  Will fall back to _map_name_to_type")

# %% [markdown]
# ## Part 4: The PROBLEM

# %%
# The issue is that SectionType enum doesn't have HOOK, PRECHORUS, or INTERLUDE!
print("PROBLEM IDENTIFIED:")
print("\n1. analyze-structure saves type='hook'")
print("2. But SectionType enum doesn't have HOOK value")
print("3. So loader falls back to _map_name_to_type")
print("4. Which maps 'hook' → CHORUS")

print("\nSectionType enum only has these values:")
for st in SectionType:
    print(f"  - {st.value}")

# %% [markdown]
# ## Part 5: The FIX

# %%
print("FIX OPTIONS:")
print("\nOption 1: Add missing types to SectionType enum")
print("  - Add HOOK, PRECHORUS, INTERLUDE to the enum")
print("  - Update section configs for visual styles")
print("\nOption 2: Save sections with existing enum values")
print("  - Map hook→chorus, prechorus→bridge WHEN SAVING")
print("  - But preserve the name field for display")
print("\nWhich option do you prefer?")

# %%
