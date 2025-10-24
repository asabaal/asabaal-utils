Healer API
==========

The ``Healer`` class provides automated code healing and fixing capabilities for generated code that fails tests or has issues.

.. autoclass:: asabaal_utils.agents.spec_coder.healer.Healer
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Core Methods
------------

heal_code
~~~~~~~~~

.. automethod:: asabaal_utils.agents.spec_coder.healer.Healer.heal_code

Automatically identifies and fixes issues in generated code.

**Parameters:**
- ``code_path`` (Path): Path to the code file to heal
- ``test_results`` (TestResult): Test failure information
- ``max_attempts`` (int, optional): Maximum healing attempts

**Returns:**
- ``HealResult``: Object containing healing results

analyze_failures
~~~~~~~~~~~~~~~~

.. automethod:: asabaal_utils.agents.spec_coder.healer.Healer.analyze_failures

Analyzes test failures to determine root causes.

**Parameters:**
- ``test_results`` (TestResult): Test execution results

**Returns:**
- ``FailureAnalysis``: Analysis of failure patterns

HealResult Class
----------------

.. autoclass:: asabaal_utils.agents.spec_coder.healer.HealResult
   :members:
   :undoc-members:
   :show-inheritance:

Examples
--------

Basic Usage
~~~~~~~~~~~

.. code-block:: python

   from asabaal_utils.agents.spec_coder.healer import Healer
   
   healer = Healer()
   
   result = healer.heal_code(
       code_path=Path("./generated_code.py"),
       test_results=test_results
   )
   
   if result.success:
       print(f"Code healed successfully in {result.attempts} attempts")
   else:
       print("Healing failed - manual intervention required")

See Also
--------

* :doc:`generator` - Code generation functionality
* :doc:`tester` - Test execution and validation
* :doc:`orchestrator` - Pipeline orchestration