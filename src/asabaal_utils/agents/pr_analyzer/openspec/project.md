# Project Context

## Purpose
The PR Analyzer is an AI-powered pull request analysis tool that provides comprehensive code review automation. It analyzes git diffs, performs intelligent quality assessment using multiple AI backends, and generates detailed reports with visualizations and recommendations.

## Tech Stack
- **Python 3.7+** - Core language
- **GitPython** - Git repository analysis
- **Jinja2** - Template rendering for HTML reports
- **Plotly** - Interactive charts and visualizations
- **OpenAI/Anthropic APIs** - AI-powered code analysis
- **PyYAML** - Configuration management
- **BeautifulSoup4** - HTML processing

## Project Conventions

### Code Style
- **Python PEP 8** compliance with 4-space indentation
- **Type hints** required for all function signatures
- **Docstrings** in Google format for all public functions
- **Maximum line length**: 100 characters
- **Naming**: snake_case for variables/functions, PascalCase for classes

### Architecture Patterns
- **Modular pipeline**: 10 independent processing stages
- **Dependency injection**: Configuration-driven behavior
- **Error isolation**: Each stage handles errors independently
- **Graceful degradation**: Fallback mechanisms for optional features
- **Separation of concerns**: Clear boundaries between analysis, reporting, and utilities

### Testing Strategy
- **Unit tests** for each stage and utility function
- **Integration tests** for complete pipeline execution
- **Mock AI responses** for consistent testing
- **Test data** in `tests/test_data/` with sample repositories
- **Coverage target**: 80% minimum for critical paths

### Git Workflow
- **Feature branches**: `feature/` prefix for new capabilities
- **Commit format**: `type(scope): description` (e.g., `feat(ai): add new model support`)
- **PR reviews**: Required for all changes to core stages
- **Version tags**: Semantic versioning for releases

## Domain Context

### Pull Request Analysis
The system operates on git pull requests, analyzing:
- **Code changes**: Added, modified, deleted files
- **Business impact**: Effect on core functionality
- **Technical quality**: Code patterns, best practices
- **Risk assessment**: Merge blockers and warnings

### AI Integration
Multiple AI agents perform specialized analysis:
- **Duplicate Detection**: Identifies redundant code
- **Merge Readiness**: Evaluates integration safety
- **Pattern Analysis**: Detects architectural issues

### File Classification
Files are categorized by business importance:
- **CORE_BUSINESS_LOGIC**: Critical functionality
- **USER_INTERFACE**: Frontend components
- **DATABASE**: Schema and data changes
- **API_INTEGRATION**: External service connections

## Important Constraints

### Performance
- **Repository size**: Must handle repos up to 10,000 files
- **Processing time**: Complete analysis within 10 minutes for 500 files
- **Memory usage**: Maximum 2GB RAM usage
- **API limits**: Respect rate limits for external services

### Reliability
- **Error recovery**: Resume from any failed stage
- **Data integrity**: Validate all inputs between stages
- **Fallback options**: Multiple AI backends for redundancy
- **Idempotency**: Safe to re-run analysis on same PR

### Security
- **API keys**: Never log or expose authentication tokens
- **Content privacy**: Option for local AI processing
- **Access control**: Read-only repository access
- **Data retention**: Configurable output retention policies

## External Dependencies

### AI Services
- **OpenRouter**: Multi-model API gateway
- **Anthropic Claude**: Direct Claude API access
- **Ollama**: Local model hosting

### Development Tools
- **Shared utilities**: `src/asabaal_utils/shared/` for common functionality
- **Configuration**: YAML files for analysis parameters
- **Templates**: Jinja2 for HTML report generation

### System Requirements
- **Git**: Required for repository analysis
- **Python 3.7+**: Minimum runtime version
- **Network**: Internet access for AI APIs (optional for local mode)
