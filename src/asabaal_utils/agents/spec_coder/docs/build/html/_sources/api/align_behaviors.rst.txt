BehavioralAligner API
=====================

The ``BehavioralAligner`` class aligns extracted test behaviors with specification requirements using AI analysis.

.. autoclass:: asabaal_utils.agents.spec_coder.align_behaviors.BehavioralAligner
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Core Methods
------------

align_all_tests
~~~~~~~~~~~~~~~

.. automethod:: asabaal_utils.agents.spec_coder.align_behaviors.BehavioralAligner.align_all_tests

Aligns all test behaviors with specification requirements.

**Parameters:**
- ``test_behaviors`` (list): TestBehavior objects from analysis
- ``spec`` (OpenSpec): Parsed specification object

**Returns:**
- ``list``: List of AlignmentMatch objects

Examples
--------

.. code-block:: python

   from asabaal_utils.agents.spec_coder.align_behaviors import BehavioralAligner
   
   aligner = BehavioralAligner()
   matches = aligner.align_all_tests(test_behaviors, spec)
   
   for match in matches:
       print(f"Test: {match.test.test_name} -> Requirement: {match.requirement.id if match.requirement else 'Additional'}")