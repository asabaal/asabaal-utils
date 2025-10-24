Testing Strategy Overview
==========================

The Spec-Coder Agent employs a comprehensive testing strategy to ensure reliability, correctness, and maintainability. This document provides an overview of our testing philosophy and organization.

Testing Philosophy
------------------

Our testing approach is based on several key principles:

**Test Pyramid**
~~~~~~~~~~~~~~~

We follow the classic test pyramid model:

* **Unit Tests (70%)**: Fast, isolated tests for individual components
* **Integration Tests (20%)**: Tests that verify component interactions
* **End-to-End Tests (10%)**: Full pipeline tests that simulate real usage

**Test-Driven Development**
~~~~~~~~~~~~~~~~~~~~~~~~~~~

While not all existing code was developed TDD, new features are expected to include:

1. **Tests first**: Write failing tests before implementation
2. **Red-Green-Refactor**: Follow the TDD cycle
3. **Continuous testing**: Tests run automatically on changes

**Quality Gates**
~~~~~~~~~~~~~~~~

All code must pass these quality gates:

* **100% test coverage** for critical paths
* **All tests must pass** in CI/CD pipeline
* **No flaky tests** allowed
* **Performance tests** for critical components

Test Organization
-----------------

Directory Structure
~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   tests/
   ├── unit/                    # Unit tests
   │   ├── test_generator.py
   │   ├── test_orchestrator.py
   │   ├── test_tester.py
   │   └── test_healer.py
   ├── integration/             # Integration tests
   │   ├── test_generator_integration.py
   │   ├── test_orchestrator_integration.py
   │   └── test_end_to_end_pipeline.py
   ├── fixtures/               # Test data and fixtures
   │   ├── sample_specs/
   │   └── expected_outputs/
   └── conftest.py             # Shared test configuration

Test Categories
~~~~~~~~~~~~~~~

**Unit Tests**
- Test individual functions and classes in isolation
- Use mocks for external dependencies
- Fast execution (milliseconds)
- High coverage of edge cases

**Integration Tests**
- Test component interactions
- Use real dependencies when possible
- Slower execution (seconds)
- Focus on interface contracts

**End-to-End Tests**
- Test complete workflows
- Use real data and configurations
- Slowest execution (minutes)
- Validate user-facing functionality

Testing Tools and Frameworks
----------------------------

**Core Framework**
~~~~~~~~~~~~~~~~~

We use `pytest <https://docs.pytest.org/>`_ as our primary testing framework:

* **Powerful assertions**: Rich assertion messages
* **Fixtures**: Reusable test setup and teardown
* **Parametrization**: Run tests with multiple inputs
* **Plugins**: Extensive ecosystem for additional features

**Mocking and Fakes**
~~~~~~~~~~~~~~~~~~~~

* **unittest.mock**: Python's built-in mocking framework
* **pytest-mock**: Enhanced mocking with pytest integration
* **Fake implementations**: Lightweight alternatives to external services

**Coverage Analysis**
~~~~~~~~~~~~~~~~~~~~~

* **pytest-cov**: Coverage reporting for pytest
* **Coverage.py**: Underlying coverage measurement tool
* **Coverage thresholds**: Enforced minimum coverage levels

**Performance Testing**
~~~~~~~~~~~~~~~~~~~~~~~

* **pytest-benchmark**: Performance regression testing
* **Memory profiling**: Detect memory leaks and inefficiencies
* **Load testing**: Validate performance under stress

Test Data Management
--------------------

Fixtures
~~~~~~~~

We use pytest fixtures for test data management:

.. code-block:: python

   @pytest.fixture
   def sample_spec():
       return {
           "project_name": "Test Project",
           "functions": [
               {
                   "name": "test_function",
                   "description": "A test function",
                   "parameters": [],
                   "return_type": "void",
                   "behaviors": ["Does nothing"]
               }
           ]
       }

   @pytest.fixture
   def temp_workspace(tmp_path):
       workspace = tmp_path / "workspace"
       workspace.mkdir()
       return workspace

Test Data Files
~~~~~~~~~~~~~~~

Sample specifications and expected outputs are stored in ``tests/fixtures/``:

* **Sample specifications**: Various spec formats and complexities
* **Expected outputs**: Reference outputs for comparison
* **Error cases**: Invalid inputs for error handling tests

Continuous Integration
----------------------

GitHub Actions
~~~~~~~~~~~~~~

Our CI pipeline runs on every push and pull request:

.. code-block:: yaml

   name: Tests
   on: [push, pull_request]
   jobs:
     test:
       runs-on: ubuntu-latest
       strategy:
         matrix:
           python-version: [3.8, 3.9, "3.10", "3.11"]
       steps:
         - uses: actions/checkout@v3
         - name: Set up Python
           uses: actions/setup-python@v4
           with:
             python-version: ${{ matrix.python-version }}
         - name: Install dependencies
           run: |
             pip install -e .[dev,test]
         - name: Run tests
           run: |
             pytest --cov=asabaal_utils --cov-report=xml
         - name: Upload coverage
           uses: codecov/codecov-action@v3

Quality Gates
~~~~~~~~~~~~~

* **All tests must pass** across all Python versions
* **Coverage threshold**: Minimum 90% line coverage
* **Performance tests**: No regressions allowed
* **Security scans**: No high-severity vulnerabilities

Test Coverage
-------------

Coverage Goals
~~~~~~~~~~~~~~

Our coverage targets are:

* **Overall coverage**: 90% minimum
* **Critical modules**: 95% minimum
* **New code**: 100% coverage required

Coverage Reports
~~~~~~~~~~~~~~~

Coverage is tracked and reported:

* **Local development**: Real-time coverage in terminal
* **CI/CD pipeline**: XML reports for Codecov
* **Documentation**: Coverage badges in README
* **Trends**: Historical coverage tracking

Coverage Exclusions
~~~~~~~~~~~~~~~~~~~

Some code is excluded from coverage:

* **Test files**: Don't test the tests
* **Configuration**: Simple configuration loading
* **Exception handling**: Hard-to-trigger error paths
* **Type hints**: Runtime type checking code

Running Tests
-------------

Local Development
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Install test dependencies
   pip install -e .[test]
   
   # Run all tests
   pytest
   
   # Run with coverage
   pytest --cov=asabaal_utils --cov-report=html
   
   # Run specific test file
   pytest tests/unit/test_generator.py
   
   # Run with verbose output
   pytest -v
   
   # Run only failed tests
   pytest --lf

Test Selection
~~~~~~~~~~~~~~

.. code-block:: bash

   # Run unit tests only
   pytest tests/unit/
   
   # Run integration tests only
   pytest tests/integration/
   
   # Run tests by keyword
   pytest -k "test_generate"
   
   # Run tests by marker
   pytest -m "slow"
   
   # Run tests in parallel
   pytest -n auto

Debugging Tests
~~~~~~~~~~~~~~~

.. code-block:: bash

   # Stop on first failure
   pytest -x
   
   # Drop into debugger on failure
   pytest --pdb
   
   # Show local variables on failure
   pytest -l
   
   # Run with maximum verbosity
   pytest -vv -s

Test Markers
------------

We use pytest markers to categorize tests:

.. code-block:: python

   @pytest.mark.unit
   def test_generator_function():
       """Unit test for generator function"""
       pass

   @pytest.mark.integration
   def test_pipeline_integration():
       """Integration test for pipeline"""
       pass

   @pytest.mark.slow
   def test_performance_regression():
       """Slow performance test"""
       pass

   @pytest.mark.external
   def test_ollama_connection():
       """Test requiring external service"""
       pass

Available markers:

* ``unit``: Fast unit tests
* ``integration``: Component integration tests
* ``slow``: Tests that take > 1 second
* ``external``: Tests requiring external services
* ``benchmark``: Performance tests

Best Practices
--------------

Writing Good Tests
~~~~~~~~~~~~~~~~~~

1. **Descriptive names**: Test names should describe what they test
2. **Arrange-Act-Assert**: Structure tests clearly
3. **Single assertion**: One logical assertion per test
4. **Independent tests**: Tests should not depend on each other
5. **Repeatable**: Tests should produce same results every time

Example:

.. code-block:: python

   def test_generator_creates_valid_python_files(temp_workspace, sample_spec):
       # Arrange
       generator = CodeGenerator()
       output_dir = temp_workspace / "tests"
       
       # Act
       result = generator.generate_tests(sample_spec, output_dir)
       
       # Assert
       assert result.success
       assert len(result.files_created) > 0
       
       for file_path in result.files_created:
           assert file_path.exists()
           assert file_path.suffix == ".py"
           
           # Verify valid Python syntax
           with open(file_path) as f:
               content = f.read()
               ast.parse(content)  # Should not raise

Mocking Guidelines
~~~~~~~~~~~~~~~~~~

1. **Mock external dependencies**: Don't make real network calls
2. **Use realistic mocks**: Mocks should behave like real objects
3. **Verify mock interactions**: Ensure mocks are called correctly
4. **Avoid over-mocking**: Don't mock the system under test

Example:

.. code-block:: python

   def test_generator_handles_ollama_error(sample_spec, temp_workspace):
       # Arrange
       mock_client = Mock()
       mock_client.generate.side_effect = ConnectionError("Service unavailable")
       
       generator = CodeGenerator(ollama_client=mock_client)
       
       # Act
       result = generator.generate_tests(sample_spec, temp_workspace)
       
       # Assert
       assert not result.success
       assert "Service unavailable" in result.error
       mock_client.generate.assert_called_once()

Test Data Management
~~~~~~~~~~~~~~~~~~~~

1. **Use fixtures**: Reusable test setup
2. **Minimal data**: Use smallest data that tests the feature
3. **Realistic data**: Test data should reflect real usage
4. **Isolated data**: Each test should have its own data

Performance Testing
~~~~~~~~~~~~~~~~~~~

1. **Benchmark critical paths**: Measure performance of key operations
2. **Set baselines**: Establish performance expectations
3. **Monitor regressions**: Alert on performance degradation
4. **Profile regularly**: Identify optimization opportunities

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**Flaky Tests**
- Identify non-deterministic behavior
- Use proper synchronization
- Isolate tests from external factors
- Add retry logic with exponential backoff

**Slow Tests**
- Profile test execution
- Identify bottlenecks
- Use mocks for slow dependencies
- Consider test parallelization

**Memory Leaks**
- Use memory profiling tools
- Check for unclosed resources
- Verify proper cleanup in fixtures
- Monitor memory usage in CI

Debugging Techniques
~~~~~~~~~~~~~~~~~~~

1. **Verbose output**: Use ``-vv`` for detailed information
2. **Debugger integration**: Use ``--pdb`` for interactive debugging
3. **Logging**: Add debug logging to tests
4. **Isolation**: Run tests individually to identify issues

Resources
---------

* `pytest documentation <https://docs.pytest.org/>`_
* `pytest-mock documentation <https://pytest-mock.readthedocs.io/>`_
* `test coverage documentation <https://coverage.readthedocs.io/>`_
* `Python testing best practices <https://docs.python-guide.org/writing/tests/>`_

See Also
--------

* :doc:`unit_tests` - Detailed unit testing guide
* :doc:`integration_tests` - Integration testing approach
* :doc:`test_coverage` - Coverage analysis and improvement