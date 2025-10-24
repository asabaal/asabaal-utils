BehaviorComparator API
=======================

The ``BehaviorComparator`` class compares and analyzes behaviors between specifications and test implementations.

.. autoclass:: asabaal_utils.agents.spec_coder.compare_behaviors.BehaviorComparator
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Core Methods
------------

compare_behaviors
~~~~~~~~~~~~~~~~

.. automethod:: asabaal_utils.agents.spec_coder.compare_behaviors.BehaviorComparator.compare_behaviors

Compares specification behaviors with test behaviors to identify gaps and alignment issues.

**Parameters:**
- ``spec_behaviors`` (list): Behaviors from specification
- ``test_behaviors`` (list): TestBehavior objects from test analysis

**Returns:**
- ``dict``: Comparison analysis results including gaps, strengths, and coverage metrics

Examples
--------

.. code-block:: python

   from asabaal_utils.agents.spec_coder.compare_behaviors import BehaviorComparator
   
   comparator = BehaviorComparator()
   result = comparator.compare_behaviors(spec_behaviors, test_behaviors)
   
   print(f"Coverage: {result['alignment_analysis']['coverage_percentage']:.1f}%")
   print(f"Gaps found: {len(result['gaps'])}")
   for gap in result['gaps']:
       print(f"  - {gap['description']}")