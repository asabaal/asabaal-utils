# AI Agent Framework Architecture

This document explains the architecture and operation of the AI Agent Framework.

## Overview

The AI Agent Framework enables autonomous software development by an AI agent. The agent follows an iterative development cycle:

1. **Analysis**: Understanding the current project state
2. **Planning**: Determining the next steps
3. **Implementation**: Writing or modifying code
4. **Validation**: Testing and verifying the changes

## Core Components

### Agent

The `Agent` class coordinates the overall process, managing the development cycle and orchestrating other components. It tracks the budget, monitors token usage, and decides when to stop based on completion, budget, or time constraints.

### Project

The `Project` class manages project state, including:
- Tracking files and their changes
- Building context from the codebase
- Providing utilities for querying and updating files

### Models

The framework provides a standardized interface for different LLM providers:
- `BaseModel`: Abstract interface all model adapters must implement
- `ClaudeModel`: Implementation for Anthropic's Claude models
- `GeminiModel`: (Stub) implementation for Google's Gemini models

### Tools

Specialized tools support the agent's capabilities:
- `CodeGenerator`: Generates code for implementing features, fixing bugs, etc.
- `UnitTestGenerator`: Creates unit tests for code
- `CodeValidator`: Validates code quality and correctness
- `TestRunner`: Executes tests to verify functionality

### Monitoring

The `CostMonitor` class tracks token usage and costs, ensuring the agent stays within budget.

## How It Works

### Project Evaluation

The agent evaluates a project through:

1. Scanning all files in the project directory
2. Building a context that includes file contents and structure
3. Prompting the LLM to analyze the project based on this context
4. Extracting structured information about the project state from the LLM's response

The agent relies on project documentation (like README files) to understand the project's goals and requirements.

### Decision Making Process

The agent makes decisions in this order:

1. Analyze the project to identify what's complete and what's missing
2. Plan the next highest-priority task to implement
3. Implement the task by generating or modifying code
4. Validate the changes through static analysis and tests
5. Repeat the process, building on the previous work

### Prompt Engineering

Each phase uses carefully constructed prompts that include:
- Current project context (file structure and contents)
- Prior phase results (e.g., the planning phase uses analysis results)
- Goal description and requirements
- Specific instructions for the current phase
- Expected output format (usually JSON)

### Implementation & Validation

When implementing changes, the agent:
1. Determines which files to create or modify
2. Generates appropriate code using the model
3. Saves changes to the project
4. Validates changes through static analysis
5. Generates unit tests to verify functionality
6. Executes tests and evaluates results
7. Decides whether to continue, fix issues, or move to the next task

## Configuration & Customization

The framework supports various configuration options:
- Budget limits to control costs
- Time limits to control duration
- Iteration limits to control scope
- Model selection to use different providers
- Logging verbosity for debugging

## Example Workflow

A typical agent session follows this flow:

1. Initialize the project and agent
2. Provide a goal description
3. Agent analyzes project state
4. Agent plans next feature to implement
5. Agent generates code for the feature
6. Agent tests the implementation
7. Agent iterates until complete or limits reached
8. Results and stats are saved for review

## Best Practices

For effective use of the framework:

1. Provide clear, detailed project documentation
2. Start with a basic project structure
3. Set appropriate budget and time limits
4. Review and commit changes manually after agent runs
5. Use the agent for iterative improvements rather than one-shot development
