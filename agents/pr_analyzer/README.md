# PR Analyzer Agent

A comprehensive tool for analyzing pull requests with AI-powered duplicate detection, quality assessment, and interactive feedback system.

## Overview

PR Analyzer creates detailed reports analyzing code changes at multiple granularity levels, from executive summaries to file-by-file analysis. It provides visual exploration with interactive charts and detailed impact scoring across business, technical, and user experience dimensions.

## Features

- **Multi-Level Analysis**: Executive summary, category overview, detailed file analysis
- **Impact Assessment**: Business, technical, UX, and risk scoring
- **Visual Exploration**: Interactive charts and graphs using Plotly and D3.js
- **File Classification**: Automatic categorization of files by purpose and importance
- **HTML Reports**: Professional, responsive reports with charts and visualizations
- **AI-Powered Analysis**: Duplicate detection and quality assessment using AI models
- **Feedback System**: Interactive feedback processing for continuous improvement

## Installation

This agent is part of the asabaal-utils repository. Install the main package:

```bash
pip install -e .
```

## Usage

### Command Line Interface

```bash
# Basic PR analysis
pr-analyzer --from main --to feature-branch

# Analyze specific repository
pr-analyzer --from main --to feature-branch --repo /path/to/repo

# Run specific stages
pr-analyzer --from main --to feature-branch --start-stage 3 --end-stage 6

# Provide feedback
pr-analyzer --feedback "The analysis missed some important files"

# Use different AI model
pr-analyzer --from main --to feature-branch --model anthropic/claude-3.5-sonnet
```

### Python API

```python
from agents.pr_analyzer.src import UnifiedPRAnalyzer

# Initialize analyzer
analyzer = UnifiedPRAnalyzer("/path/to/repo")

# Run complete analysis
success = analyzer.analyze_pr("main", "feature-branch")

# Run specific stages
success = analyzer.run_stage3_agent_communication()

# Process feedback
success = analyzer.update_analysis_with_feedback("Add more detail to file X")
```

## Architecture

This agent follows a modular stage-based architecture:

### Processing Stages

1. **Stage 1**: Context Preparation - Git analysis and file classification
2. **Stage 2**: Agent Prompts - Generate AI prompts for analysis
3. **Stage 3**: Agent Communication - Execute AI analysis
4. **Stage 4**: Response Parsing - Parse AI responses
5. **Stage 5**: Issue Extraction - Extract quality issues
6. **Stage 6**: Filtering & Combination - Combine and filter results
7. **Stage 7**: Detailed Analysis - Generate detailed insights
8. **Stage 8**: File Assessment - Assess individual files
9. **Stage 9**: HTML Generation - Create interactive reports
10. **Stage 10**: Feedback Updates - Process user feedback

### Directory Structure

```
agents/pr-analyzer/
├── src/                    # Source code
│   ├── analyzer.py        # Main UnifiedPRAnalyzer class
│   ├── cli.py             # Command-line interface
│   ├── stages/            # Processing stages
│   ├── core/              # Git analysis, report generation
│   ├── classifiers/       # File categorization
│   └── utils/             # Utilities and helpers
├── configs/               # Configuration files
│   ├── config/           # YAML configurations
│   ├── debug_outputs/    # Debug data and prompts
│   ├── prompt_data/      # AI prompt templates
│   └── pr_analysis_output/ # Generated reports
├── tests/                 # Test suite
└── README.md             # This file
```

## Configuration

### Analysis Configuration

Edit `configs/config/analysis_config.yaml` to customize:

- AI model selection
- Analysis thresholds
- Output formatting
- Stage execution parameters

### File Categories

Edit `configs/config/file_categories.yaml` to customize:

- File classification rules
- Category importance weights
- Impact scoring parameters

## Output

The agent generates comprehensive reports in the output directory:

### HTML Report
- Interactive charts and visualizations
- File-by-file analysis
- Executive summary
- Impact assessment scores

### Debug Outputs
- Stage-by-stage analysis data
- AI prompts and responses
- Processing logs
- Error details

## Dependencies

### Internal Dependencies
- `shared/agentic_toolkit/` - AI backend utilities
- `shared/mathematical_models/` - Mathematical utilities

### External Dependencies
- gitpython>=3.1.0 - Git operations
- jinja2>=3.0.0 - Template rendering
- pyyaml>=6.0 - Configuration parsing
- plotly>=5.0.0 - Interactive charts
- beautifulsoup4>=4.10.0 - HTML processing
- requests>=2.25.0 - HTTP client
- openai>=1.0.0 - AI API client

## Development

### Running Tests

```bash
cd agents/pr-analyzer
python -m pytest tests/
```

### Debug Mode

Enable debug mode for detailed logging:

```bash
pr-analyzer --from main --to feature-branch --debug
```

### Adding New Stages

1. Create new stage file in `src/stages/`
2. Implement stage class with required methods
3. Add stage to pipeline in `analyzer.py`
4. Update documentation

## AI Backend Configuration

The agent supports multiple AI backends:

### OpenRouter (Default)
```python
config = {
    "agentic_backend": {
        "provider": "openrouter",
        "model": "anthropic/claude-3.5-sonnet",
        "api_key": "your-openrouter-key"
    }
}
```

### Claude CLI
```python
config = {
    "agentic_backend": {
        "provider": "claude_cli",
        "model": "claude-3-5-sonnet-20241022"
    }
}
```

### Ollama (Local)
```python
config = {
    "agentic_backend": {
        "provider": "ollama",
        "model": "llama3.1:8b",
        "base_url": "http://localhost:11434"
    }
}
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure shared utilities are accessible
2. **Configuration Not Found**: Check configs directory structure
3. **AI API Errors**: Verify API keys and model availability
4. **Git Errors**: Ensure repository is a valid git repo

### Debug Information

Enable debug mode to get detailed information:
- Stage execution logs
- AI API responses
- File processing details
- Error stack traces

## Contributing

1. Follow the existing code structure
2. Add tests for new functionality
3. Update documentation
4. Use the shared utilities when possible

## License

Part of the Asabaal Ventures toolkit. See main repository for license details.

## Support

For issues and feature requests, please use the main asabaal-utils repository issue tracker.