Contributing to spec-coder
===========================

This guide provides information for developers who want to contribute to the spec-coder project. We welcome contributions of all types, including bug fixes, new features, documentation improvements, and test enhancements.

Getting Started
---------------

Development Environment Setup
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Prerequisites**:
- Python 3.8 or higher
- Git
- Ollama (for AI model testing)
- Docker (optional, for containerized development)

**Setup Steps**:

1. **Fork and Clone**:
   .. code-block:: bash

      git clone https://github.com/your-username/spec-coder.git
      cd spec-coder

2. **Create Virtual Environment**:
   .. code-block:: bash

      python -m venv venv
      source venv/bin/activate  # On Windows: venv\Scripts\activate

3. **Install Dependencies**:
   .. code-block:: bash

      pip install -e ".[dev]"
      pip install -r requirements-dev.txt

4. **Install Pre-commit Hooks**:
   .. code-block:: bash

      pre-commit install

5. **Setup Ollama**:
   .. code-block:: bash

      # Install Ollama
      curl -fsSL https://ollama.ai/install.sh | sh
      
      # Start Ollama service
      ollama serve
      
      # Pull required models
      ollama pull llama3
      ollama pull codellama

6. **Run Tests**:
   .. code-block:: bash

      pytest tests/ -v

Development Workflow
~~~~~~~~~~~~~~~~~~~~

**1. Create a Feature Branch**:
   .. code-block:: bash

      git checkout -b feature/your-feature-name

**2. Make Changes**:
   - Write code following the style guidelines
   - Add tests for new functionality
   - Update documentation as needed

**3. Run Quality Checks**:
   .. code-block:: bash

      # Run linting
      flake8 src/
      black src/
      isort src/
      
      # Run type checking
      mypy src/
      
      # Run tests
      pytest tests/ --cov=src/
      
      # Run security checks
      bandit -r src/

**4. Commit Changes**:
   .. code-block:: bash

      git add .
      git commit -m "feat: add your feature description"

**5. Push and Create Pull Request**:
   .. code-block:: bash

      git push origin feature/your-feature-name
      # Create PR on GitHub

Code Style and Standards
------------------------

Python Code Style
~~~~~~~~~~~~~~~~~

We follow the following Python style guidelines:

**Formatting**:
- Use `black` for code formatting
- Use `isort` for import sorting
- Maximum line length: 88 characters

**Linting**:
- Use `flake8` for linting
- Follow PEP 8 guidelines
- Use type hints where appropriate

**Documentation**:
- Use docstrings for all public functions and classes
- Follow Google or NumPy docstring style
- Include type hints in function signatures

**Example**:

.. code-block:: python

   from typing import List, Dict, Optional
   
   def generate_code(
       spec: Specification,
       model: str = "llama3",
       config: Optional[Dict[str, Any]] = None
   ) -> GenerationResult:
       """Generate code from specification.
       
       Args:
           spec: The specification to generate code from
           model: The AI model to use for generation
           config: Optional configuration parameters
           
       Returns:
           GenerationResult containing the generated code and metadata
           
       Raises:
           GenerationError: If code generation fails
           ValidationError: If specification is invalid
       """
       pass

Testing Standards
~~~~~~~~~~~~~~~~~

**Test Structure**:
- Use `pytest` for testing
- Place tests in `tests/` directory
- Mirror source directory structure in tests

**Test Coverage**:
- Aim for >80% code coverage
- Test all public functions and classes
- Include edge cases and error conditions

**Test Naming**:
- Use descriptive test names
- Follow pattern: `test_<function>_<scenario>`

**Example**:

.. code-block:: python

   import pytest
   from spec_coder import CodeGenerator, Specification
   
   class TestCodeGenerator:
       def test_generate_code_success(self):
           """Test successful code generation."""
           spec = Specification(name="test", functions=[])
           generator = CodeGenerator()
           
           result = generator.generate_code(spec)
           
           assert result.success
           assert len(result.files_created) > 0
       
       def test_generate_code_invalid_spec_raises_error(self):
           """Test that invalid specification raises error."""
           spec = None  # Invalid spec
           generator = CodeGenerator()
           
           with pytest.raises(ValidationError):
               generator.generate_code(spec)

Documentation Standards
~~~~~~~~~~~~~~~~~~~~~~~

**Documentation Types**:
- **API Documentation**: Docstrings and type hints
- **User Documentation**: Guides and tutorials
- **Developer Documentation**: Architecture and contributing
- **Examples**: Code examples and use cases

**Documentation Style**:
- Use clear, concise language
- Include code examples
- Provide step-by-step instructions
- Use consistent formatting

**Review Process**:
- All documentation changes require review
- Documentation should be updated with code changes
- Include documentation in pull request reviews

Project Structure
-----------------

Directory Layout
~~~~~~~~~~~~~~~~

.. code-block:: text

   spec-coder/
   ├── src/
   │   └── spec_coder/
   │       ├── __init__.py
   │       ├── cli.py
   │       ├── orchestrator.py
   │       ├── generator.py
   │       ├── tester.py
   │       ├── healer/
   │       │   ├── __init__.py
   │       │   └── heal.py
   │       └── utils/
   │           ├── __init__.py
   │           ├── config.py
   │           └── logging.py
   ├── tests/
   │   ├── unit/
   │   ├── integration/
   │   └── fixtures/
   ├── docs/
   │   ├── source/
   │   │   ├── user_guide/
   │   │   ├── architecture/
   │   │   ├── development/
   │   │   └── api/
   │   └── build/
   ├── examples/
   ├── scripts/
   ├── requirements.txt
   ├── requirements-dev.txt
   ├── setup.py
   ├── pyproject.toml
   ├── README.md
   └── CONTRIBUTING.md

Component Organization
~~~~~~~~~~~~~~~~~~~~~~

**Core Components**:
- `orchestrator.py`: Main pipeline coordination
- `generator.py`: Code generation logic
- `tester.py`: Test execution and validation
- `healer/`: Self-healing functionality

**Utilities**:
- `utils/config.py`: Configuration management
- `utils/logging.py`: Logging system
- `utils/validation.py`: Input validation

**External Interfaces**:
- `cli.py`: Command-line interface
- `api/`: REST API (if applicable)
- `templates/`: Code generation templates

Contribution Guidelines
-----------------------

Types of Contributions
~~~~~~~~~~~~~~~~~~~~~~

**Bug Fixes**:
- Report bugs using GitHub Issues
- Include reproduction steps
- Add tests that cover the bug
- Fix the issue with minimal changes

**New Features**:
- Propose features using GitHub Discussions
- Create design document for large features
- Implement with tests and documentation
- Follow existing patterns and conventions

**Documentation**:
- Fix typos and grammatical errors
- Improve clarity and examples
- Add missing documentation
- Translate to other languages

**Performance Improvements**:
- Profile performance bottlenecks
- Optimize critical paths
- Add performance tests
- Document performance changes

Pull Request Process
~~~~~~~~~~~~~~~~~~~~

**Before Submitting**:
1. Ensure all tests pass
2. Update documentation
3. Follow code style guidelines
4. Add changelog entry
5. Test with real specifications

**Pull Request Template**:

.. code-block:: markdown

   ## Description
   Brief description of changes
   
   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Documentation update
   - [ ] Performance improvement
   - [ ] Other
   
   ## Testing
   - [ ] Added tests for new functionality
   - [ ] All tests pass
   - [ ] Manual testing completed
   
   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Self-review completed
   - [ ] Documentation updated
   - [ ] Changelog updated
   
   ## Issues Fixed
   Closes #issue_number

**Review Process**:
1. Automated checks must pass
2. At least one maintainer review required
3. Address all review comments
4. Maintain clean commit history

Release Process
---------------

Version Management
~~~~~~~~~~~~~~~~~

We use Semantic Versioning (SemVer):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

**Release Types**:
- **Stable Releases**: Regular releases with full testing
- **Release Candidates**: Pre-release testing
- **Development Releases**: Cutting-edge features

Changelog Maintenance
~~~~~~~~~~~~~~~~~~~~

**Changelog Format**:

.. code-block:: markdown

   ## [1.2.0] - 2024-01-15
   
   ### Added
   - New AI model support for Qwen3-Coder
   - Parallel pipeline execution
   - Enhanced error reporting
   
   ### Changed
   - Improved code generation quality
   - Updated default model to llama3
   - Refactored configuration system
   
   ### Fixed
   - Memory leak in long-running pipelines
   - Import resolution issues
   - Test execution timeout problems
   
   ### Deprecated
   - Old configuration format (will be removed in 2.0)
   
   ### Security
   - Fixed potential prompt injection vulnerability

Release Checklist
~~~~~~~~~~~~~~~~~

**Pre-Release**:
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Changelog updated
- [ ] Version number updated
- [ ] Security scan completed
- [ ] Performance tests run

**Release**:
- [ ] Create release tag
- [ ] Build and publish packages
- [ ] Update documentation website
- [ ] Create GitHub release
- [ ] Notify community

**Post-Release**:
- [ ] Monitor for issues
- [ ] Update project roadmap
- [ ] Plan next release
- [ ] Thank contributors

Community Guidelines
--------------------

Code of Conduct
~~~~~~~~~~~~~~~

We are committed to providing a welcoming and inclusive environment for all contributors. Please:

- Be respectful and considerate
- Use inclusive language
- Focus on constructive feedback
- Help others learn and grow
- Report inappropriate behavior

Communication Channels
~~~~~~~~~~~~~~~~~~~~~

**GitHub**:
- Issues: Bug reports and feature requests
- Discussions: General questions and ideas
- Pull Requests: Code contributions

**Community**:
- Discord/Slack: Real-time discussions
- Mailing List: Announcements and discussions
- Blog: Tutorials and case studies

**Support**:
- Documentation: Primary source of information
- Issues: Bug reports and help requests
- Discussions: General questions

Getting Help
~~~~~~~~~~~~

**For Contributors**:
- Read this contributing guide
- Check existing issues and discussions
- Ask questions in GitHub Discussions
- Join community channels

**For Users**:
- Read user documentation
- Check FAQ and troubleshooting
- Search existing issues
- Create new issue if needed

Recognition and Appreciation
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Contributor Recognition**:
- Contributors section in README
- Release notes attribution
- Community spotlights
- Contributor badges

**Ways to Contribute**:
- Code contributions
- Documentation improvements
- Bug reports and feedback
- Community support
- Translation and localization

Thank you for contributing to spec-coder! Your contributions help make this project better for everyone.