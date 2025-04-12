# AI Agent Framework

A flexible framework for building and running AI agents powered by Claude or other LLM providers.

## Overview

This framework enables the creation of autonomous AI agents that can:

1. Analyze a project's current state
2. Plan the next steps needed
3. Implement changes through code generation
4. Test and validate those changes
5. Continue iterating without human intervention

The framework is designed to be model-agnostic, allowing you to swap between Claude, Gemini, or other providers with minimal changes.

## Components

- **Core**: The central agent loop and coordination system
- **Models**: Adapters for different AI providers (Claude, Gemini, etc.)
- **Project**: State management and context handling for projects
- **Tools**: Utilities for code generation, testing, and other agent capabilities
- **Monitoring**: Tracking token usage, performance, and costs

## Usage

Basic example of using the framework:

```python
from ai_agent import Agent, Project, ClaudeModel

# Initialize a project
project = Project(path="./my_project")

# Create an agent with Claude
agent = Agent(
    model=ClaudeModel(api_key="your_key_here"),
    project=project
)

# Run the agent for 1 hour
agent.run(max_runtime_hours=1)
```

## Development Status

This framework is under active development. See the roadmap below for planned features.

## Roadmap

- [x] Initial framework design
- [ ] Core agent loop implementation
- [ ] Claude model integration
- [ ] Project state management
- [ ] Cost tracking and optimization
- [ ] Gemini model adapter
- [ ] Advanced context management
- [ ] Comprehensive documentation and examples
