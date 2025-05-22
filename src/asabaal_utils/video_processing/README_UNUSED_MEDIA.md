# Unused Media Detection Tools

This directory contains tools for analyzing CapCut projects and detecting unused media files. These tools help identify media that exists in your project's media pool but isn't used in the timeline, allowing you to clean up projects and reduce file size.

## Available Tools

### 1. Project Structure Analyzer

The `analyze_project_structure.py` script dissects a CapCut project file to understand where media pools, timeline clips, and other structures are stored. This is useful for understanding the project format and developing other tools.

```bash
python analyze_project_structure.py path/to/draft_content.json --output /path/to/output_dir --verbose
```

### 2. Unused Media Detector

The `detect_unused_media.py` script analyzes a CapCut project file to identify unused media files. It creates detailed reports of which files are unused.

```bash
python detect_unused_media.py path/to/draft_content.json --output /path/to/output_dir --html --verbose
```

Options:
- `--output` or `-o`: Directory to save output files
- `--html`: Generate an HTML report with visualization
- `--verbose` or `-v`: Print detailed information during analysis

### 3. Test Project Analyzer

The `test_project_analyzer.py` script is a simple wrapper for the project structure analyzer that sets up a standard output directory.

```bash
python test_project_analyzer.py path/to/draft_content.json
```

## Understanding CapCut Project Structure

CapCut project files (typically `draft_content.json`) contain several key sections:

1. **Materials**: Contains references to all media files in the project
   - Usually organized by type (videos, audios, images, etc.)
   - Each media item has an ID, path, and metadata

2. **Tracks**: Contains the timeline tracks with segments/clips
   - Each segment often has a reference to a material (material_id)
   - Can also contain direct media path references

3. **Other References**: Media paths may appear in various other places
   - Effects, transitions, and other elements might reference media

The relationship between these sections determines which media is actually used in the timeline and which is unused.

## How to Clean Up Unused Media

Once you've identified unused media:

1. Open your CapCut project
2. Go to the Media panel
3. Right-click on each unused media file and select 'Remove'
4. Save your project

This will reduce your project file size and clean up your media panel.

## Integration with Clip Dashboard

The unused media detection is also integrated into the Clip Preview Dashboard. When viewing the dashboard, you'll see a section showing any unused media files detected in the project.

## Troubleshooting

If the tools don't correctly identify unused media, try:

1. Using the `--verbose` flag to see more detailed analysis
2. Running the project structure analyzer first to understand the specific format
3. Looking for media references in different sections of the project file

Different versions of CapCut may store media references in slightly different ways, so these tools attempt to handle various formats but may need adjustments for specific cases.