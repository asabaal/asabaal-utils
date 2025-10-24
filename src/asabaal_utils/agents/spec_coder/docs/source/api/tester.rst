Tester API
==========

The ``Tester`` class provides comprehensive test execution and validation capabilities for generated test suites.

.. autoclass:: asabaal_utils.agents.spec_coder.tester.Tester
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Core Methods
------------

run_tests
~~~~~~~~~

.. automethod:: asabaal_utils.agents.spec_coder.tester.Tester.run_tests

Executes test suites and provides detailed results analysis.

**Parameters:**
- ``test_dir`` (Path): Directory containing test files
- ``python_path`` (list, optional): Additional Python paths
- ``timeout`` (int, optional): Test execution timeout

**Returns:**
- ``TestResult``: Object containing test execution results

validate_tests
~~~~~~~~~~~~~~

.. automethod:: asabaal_utils.agents.spec_coder.tester.Tester.validate_tests

Validates test syntax and structure before execution.

**Parameters:**
- ``test_files`` (list): List of test file paths

**Returns:**
- ``ValidationResult``: Object containing validation results

TestResult Class
----------------

.. autoclass:: asabaal_utils.agents.spec_coder.tester.TestResult
   :members:
   :undoc-members:
   :show-inheritance:

Configuration
-------------

The Tester can be configured through:

1. **Constructor parameters**: Test execution settings
2. **Configuration file**: Test runner configuration
3. **Environment variables**: Override specific settings

Example Configuration
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   tester:
     timeout: 300
     parallel: true
     max_workers: 4
     python_path:
       - "./src"
       - "./lib"
   
   reporting:
     format: "junit"
     include_coverage: true
     coverage_threshold: 80

Examples
--------

Basic Usage
~~~~~~~~~~~

.. code-block:: python

   from asabaal_utils.agents.spec_coder.tester import Tester
   
   tester = Tester()
   
   result = tester.run_tests(Path("./tests"))
   
   if result.success:
       print(f"All {result.tests_run} tests passed")
   else:
       print(f"{result.failures} tests failed")
       for failure in result.failures:
           print(f"Failed: {failure.test_name}")

Advanced Usage
~~~~~~~~~~~~~~

.. code-block:: python

   tester = Tester(
       timeout=600,
       parallel=True,
       max_workers=8
   )
   
   # Validate first
   validation = tester.validate_tests(test_files)
   if validation.valid:
       # Run tests
       result = tester.run_tests(test_dir)
       
       # Generate report
       tester.generate_report(result, output_file="test_report.html")

See Also
--------

* :doc:`generator` - Test generation functionality
* :doc:`orchestrator` - Pipeline orchestration
* :doc:`testing/overview` - Testing strategy documentation