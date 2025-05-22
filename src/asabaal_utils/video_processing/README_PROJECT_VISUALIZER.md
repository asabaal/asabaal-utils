# CapCut Project Structure Visualizer

This interactive visualization tool allows you to explore and understand the structure of CapCut project files. It provides a graphical interface to navigate through the project hierarchy, view media relationships, and identify unused files.

## Features

### Interactive Project Structure Tree
- Visualize the entire project structure as an interactive tree
- Drill down into nested objects and arrays
- View detailed information about any node in the project

### Media File Management
- See all media files in your project with detailed information
- Identify which media files are used vs. unused
- Filter media by type (video, audio, image) and usage status

### Timeline Visualization
- View tracks and clips in a graphical timeline representation
- See how clips are positioned in the project
- Identify which media files are used in which clips

### Search Functionality
- Search the entire project for keys, values, or paths
- Navigate directly to any part of the project
- Find specific media files or settings

### Project Overview
- Get a high-level summary of your project
- See key statistics about media usage, timeline content, and more
- Identify potential areas for cleanup or optimization

## Usage

```bash
python visualize_project_structure.py path/to/draft_content.json [options]
```

### Options

- `--output` or `-o`: Directory to save visualization files (default: creates a "project_visualization" directory next to the project file)
- `--no-browser`: Don't automatically open the visualization in a browser
- `--verbose` or `-v`: Print detailed information during analysis

## Navigation

The visualization interface is divided into several tabs:

### Overview Tab
Provides a high-level summary of your project with key statistics and previews of the project structure and media usage.

### Structure Tab
Displays the complete project structure as an interactive tree. Click on any node to see its details in the panel below.

### Media Tab
Shows all media files in your project. You can filter by media type (video, audio, image) and usage status (used, unused). This helps identify unused media that can be removed to reduce project size.

### Timeline Tab
Visualizes the timeline tracks and clips in your project. Click on any clip to see its details, including which media file it uses.

### Search Tab
Allows you to search the entire project for specific content. Search results show the exact path in the project, making it easy to find and navigate to specific items.

## Troubleshooting

If you encounter issues with the visualization:

1. **Browser Compatibility**: The visualization works best in modern browsers (Chrome, Firefox, Edge). If you have display issues, try a different browser.

2. **Large Projects**: Very large project files may take longer to load and visualize. For best performance, consider closing other browser tabs when working with large projects.

3. **Path Resolution**: If media paths are not resolving correctly, check if your project uses absolute or relative paths and ensure all media files are in the expected locations.

4. **Manual Opening**: If the browser doesn't open automatically, use the `--no-browser` flag and manually open the HTML file from the output directory.

## Notes

- This tool analyzes the project structure without modifying any files
- For very large projects, the visualization may take a moment to load
- The tool works best with standard CapCut project files (draft_content.json)
- Different versions of CapCut may use slightly different project structures