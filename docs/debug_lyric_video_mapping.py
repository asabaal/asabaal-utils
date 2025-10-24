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
# # Debug: Lyric Video Section Type Mapping Issue
#
# ## Problem
# - analyze-structure saves CORRECT section types (hook, prechorus, interlude)
# - lyric video displays WRONG types (CHORUS instead of HOOK, BRIDGE instead of PRECHORUS)
#
# ## Goal
# Find where the section type mapping is being changed

# %%
# Cell 1: Import minimal dependencies
import json
import sys
sys.path.append('/home/asabaal/asabaal_ventures/repos/asabaal-utils/src')

print("Imports complete")

# %%
# Cell 2: Load the files we're comparing
# The CORRECT output from analyze-structure
with open('/mnt/d/Work/Asabaal Ventures/Asabaal/Vision/Week 4/week4_structure_final.json', 'r') as f:
    final_structure = json.load(f)

# The lyric video format file that was auto-generated
with open('/mnt/d/Work/Asabaal Ventures/Asabaal/Vision/Week 4/week4_structure_final_lyric_video.json', 'r') as f:
    lyric_video_structure = json.load(f)

print("Loaded both files")

# %%
# Cell 3: Check what's in the final structure
print("=== FINAL STRUCTURE (from analyze-structure) ===")
print("\nFirst 3 time sections:")
for i, section in enumerate(final_structure['time_sections'][:3]):
    print(f"{i}: type='{section['type']}', name='{section['name']}'")

print("\nSection at index 4 (should be prechorus):")
section = final_structure['time_sections'][4]
print(f"type='{section['type']}', name='{section['name']}'")

# %%
# Cell 4: Check what's in the lyric video format
print("=== LYRIC VIDEO FORMAT (auto-generated) ===")
print("\nFirst 3 sections:")
for i, section in enumerate(lyric_video_structure['sections'][:3]):
    print(f"{i}: type='{section['type']}', name='{section['name']}'")

print("\nSection at index 4 (should be prechorus but shows as bridge):")
section = lyric_video_structure['sections'][4]
print(f"type='{section['type']}', name='{section['name']}'")

# %%
# Cell 5: Load the structure loader to see how it processes files
from asabaal_utils.video_processing.lyric_video.structure_loader import StructureLoader

loader = StructureLoader()
print(f"StructureLoader loaded")
print(f"\nSection name mappings:")
for key, value in loader.section_name_mappings.items():
    if 'hook' in key or 'pre' in key:
        print(f"  '{key}' -> {value}")

# %%
# Cell 6: Test loading the lyric video format file
sections = loader.load_structure_file('/mnt/d/Work/Asabaal Ventures/Asabaal/Vision/Week 4/week4_structure_final_lyric_video.json')
print(f"Loaded {len(sections)} sections")
print("\nFirst 5 sections after loading:")
for i, section in enumerate(sections[:5]):
    print(f"{i}: name='{section.name}', section_type={section.section_type}")

# %%
# Cell 7: Check if the issue is in how the type is parsed
test_section = {'name': 'hook', 'type': 'chorus', 'start': 0, 'end': 10}
print("Testing how structure loader handles explicit types...")
print(f"Input: {test_section}")

# The loader should use the 'type' field if provided
# Let's trace through the _load_json_format method logic

# %%
# Cell 8: Test the section manager display
from asabaal_utils.video_processing.lyric_video.section_manager import SectionManager, SectionType

manager = SectionManager()
# Load our structure
manager.load_structure_from_file('/mnt/d/Work/Asabaal Ventures/Asabaal/Vision/Week 4/week4_structure_final_lyric_video.json', 226.5)

print("Sections loaded into manager:")
for i, (start, end, section_type) in enumerate(manager.sections[:5]):
    print(f"{i}: {start:.1f}s - {end:.1f}s: {section_type}")
