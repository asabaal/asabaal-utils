# CapCut Project Visualizer (React Implementation)

This is a React-based implementation of the CapCut project visualizer, focusing on timeline visualization and unused media detection.

## Overview

The CapCut Project Visualizer provides an interactive interface to:

1. Visualize the structure of CapCut project files
2. Identify and display unused media files
3. Show timeline tracks and clips with their media relationships
4. Explore the connections between media files and timeline clips

## Project Structure Analysis

Based on our analysis of the CapCut project format, we understand:

### Media Structure
- Media files are stored in `materials` section, organized by type (videos, audios, images)
- Each media item has:
  - `id`: Unique identifier
  - `path`: File path
  - `type`: Media type (video, audio, image)
  - Additional metadata like duration, width, height

### Timeline Structure
- Timelines consist of tracks containing segments/clips
- Each clip typically references a media item through:
  - `material_id`: Reference to the ID of a media item
  - Sometimes direct `path` references
- Clips have position data:
  - `timeline_start`: Position in timeline
  - `timeline_duration`: Length in timeline
  - Sometimes source position data (for trimmed clips)

### Unused Media Detection
- Media is considered "unused" when:
  - It exists in the materials/media pool section
  - It has no corresponding clips in the timeline that reference it
  - No other project components (effects, etc.) reference it

## React Component Structure

The React implementation uses this component hierarchy:

```
App
├── ProjectOverview
│   ├── ProjectStats
│   └── MediaUsagePieChart
├── MediaExplorer
│   ├── MediaFilters
│   ├── MediaList
│   └── MediaDetails
├── TimelineVisualizer
│   ├── TimelineTrack
│   ├── TimelineClip
│   └── ClipDetails
└── StructureExplorer
    ├── TreeVisualizer
    └── NodeDetails
```

## Implementation Details

The visualization leverages:

- React for component structure
- D3.js for data visualization (pie charts, timelines)
- React Router for navigation
- Bootstrap for responsive layout
- Custom CSS for timeline and media visualization

## API Integration

The React frontend communicates with backend Python services:

1. `analyze_project_structure.py` - Provides project structure data
2. `detect_unused_media.py` - Identifies unused media
3. `visualize_project_structure.py` - Provides visualization data

## Deployment

This React application can be:

1. Built as a standalone web application
2. Embedded in an Electron wrapper for desktop use
3. Integrated with the existing Python tools via a REST API

## Usage

1. Upload or select a CapCut project file
2. View the automatically generated visualizations
3. Explore media files, filtering by type and usage
4. Examine the timeline structure
5. Generate reports for unused media