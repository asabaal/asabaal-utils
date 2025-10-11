# PR Analyzer

A comprehensive tool for analyzing pull requests with visual exploration capabilities and detailed impact assessment.

## Overview

PR Analyzer creates comprehensive reports analyzing code changes at multiple granularity levels, from executive summaries to file-by-file analysis. It provides visual exploration with interactive charts and detailed impact scoring across business, technical, and user experience dimensions.

## Features

- **Multi-Level Analysis**: Executive summary, category overview, detailed file analysis
- **Impact Assessment**: Business, technical, UX, and risk scoring
- **Visual Exploration**: Interactive charts and graphs using Plotly and D3.js
- **File Classification**: Automatic categorization of files by purpose and importance
- **HTML Reports**: Professional, responsive reports with charts and visualizations
- **Comprehensive Metrics**: Lines changed, file categories, change types, impact scores

## Installation

```bash
# Clone the asabaal-utils repository
git clone <repository-url>
cd asabaal-utils/pr_analyzer

# Install dependencies (if any additional packages needed)
pip install -r requirements.txt  # when available
```

## Usage

### Basic Analysis

```bash
# Analyze PR between branches
python main.py --from main --to feature-branch --repo /path/to/repo

# Generate HTML report
python main.py --from main --to feature-branch --output report.html

# Include detailed diffs
python main.py --from main --to feature-branch --include-diffs --output detailed-report.html
```

### Command Line Options

- `--from`: Source branch (default: main)
- `--to`: Target branch (default: current branch)
- `--repo`: Repository path (default: current directory)
- `--output`: Output HTML file path
- `--include-diffs`: Include detailed diff analysis
- `--config`: Custom configuration file path

### Configuration

The tool uses configuration files in the `config/` directory:

- `categories.json`: File classification rules and categories
- `analysis_settings.json`: Impact scoring weights and thresholds

## Report Structure

### Executive Summary
- PR scale assessment (Small/Medium/Large/Massive)
- Overall impact score (0-10)
- Risk level (Low/Medium/High)
- Transformation type classification

### Impact Analysis
- **Business Impact**: Effect on business operations and value
- **Technical Impact**: Technical complexity and architecture changes
- **UX Impact**: User interface and experience modifications
- **Risk Score**: Potential deployment and maintenance risks

### Visual Components
- Category distribution pie chart
- Lines of code changes bar chart
- Change types breakdown
- File size distribution

### File Explorer
- Categorized file listing with change indicators
- Lines added/removed for each file
- File importance and category icons

## File Categories

The analyzer classifies files into categories:

- **🏛️ Core Business Logic**: Critical business functionality
- **🔗 API Integration**: API endpoints and integrations
- **🗄️ Database**: Database schemas, migrations, queries
- **🎨 User Interface**: Frontend components and layouts
- **📝 Blog Content**: Content management and blog posts
- **⚙️ Configuration**: Config files and settings
- **🖼️ Assets/Media**: Images, videos, static assets
- **📚 Documentation**: README, docs, guides
- **🧪 Testing**: Test files and testing utilities

## Impact Scoring

### Business Impact (0-10)
- Core business logic changes: High impact
- API and database changes: High impact
- UI changes: Medium-high impact
- Content and assets: Medium impact

### Technical Impact (0-10)
- Lines of code changed
- Architecture-affecting categories
- New vs modified files
- Complexity indicators

### Risk Score (0-10)
- Large change volume
- Critical system modifications
- Configuration changes
- File deletions

## Example Output

```bash
$ python main.py --from main --to feature-branch --output analysis.html

🔍 PR Analyzer v1.0.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Analysis Results:
• Files Changed: 125
• Lines Added: 15,432
• Lines Removed: 2,108
• Net Change: +13,324

🎯 Impact Assessment:
• Overall Score: 8.7/10 (Very High Impact)
• Business Impact: 9.2/10
• Technical Impact: 8.1/10
• Risk Score: 6.3/10 (Medium Risk)

📈 Generated HTML report: analysis.html
```

## Development

### Project Structure

```
pr_analyzer/
├── core/
│   ├── git_analyzer.py      # Git operations and diff parsing
│   └── models.py            # Data models and structures
├── classifiers/
│   └── file_classifier.py   # File categorization logic
├── analyzers/
│   └── impact_analyzer.py   # Impact scoring and analysis
├── visualizers/
│   └── html_generator.py    # HTML report generation
├── config/
│   ├── categories.json      # File classification config
│   └── analysis_settings.json # Analysis configuration
├── main.py                  # CLI entry point
└── README.md               # This file
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

Part of the Asabaal Ventures toolkit. See main repository for license details.

## Support

For issues and feature requests, please use the main asabaal-utils repository issue tracker.