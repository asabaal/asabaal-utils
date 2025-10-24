IntegrationOrchestrator API
============================

The ``IntegrationOrchestrator`` class manages the complete pipeline workflow, coordinating all stages of the spec-coder process.

.. autoclass:: asabaal_utils.agents.spec_coder.orchestrator.IntegrationOrchestrator
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Core Methods
------------

run_pipeline
~~~~~~~~~~~~

.. automethod:: asabaal_utils.agents.spec_coder.orchestrator.IntegrationOrchestrator.run_pipeline

Executes the complete 4-stage pipeline from specification to final code generation.

**Parameters:**
- ``spec_file`` (Path): Path to the specification file
- ``output_dir`` (Path): Directory for all outputs
- ``config`` (dict, optional): Configuration overrides

**Returns:**
- ``bool``: True if pipeline completed successfully

Stage Methods
-------------

The orchestrator provides methods for each pipeline stage:

_stage1_spec_to_scaffolds
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: asabaal_utils.agents.spec_coder.orchestrator.IntegrationOrchestrator._stage1_spec_to_scaffolds

_stage2_scaffold_to_requirements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: asabaal_utils.agents.spec_coder.orchestrator.IntegrationOrchestrator._stage2_scaffold_to_requirements

_stage3_requirements_to_alignment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: asabaal_utils.agents.spec_coder.orchestrator.IntegrationOrchestrator._stage3_requirements_to_alignment

_stage4_alignment_to_generation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: asabaal_utils.agents.spec_coder.orchestrator.IntegrationOrchestrator._stage4_alignment_to_generation

Utility Methods
---------------

run
~~~

.. automethod:: asabaal_utils.agents.spec_coder.orchestrator.IntegrationOrchestrator.run

_clean_test_file_content
~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: asabaal_utils.agents.spec_coder.orchestrator.IntegrationOrchestrator._clean_test_file_content

This method handles the critical task of cleaning AI-generated test content to prevent IndentationError issues in Stage 2.

Configuration
-------------

The orchestrator can be configured through:

1. **Constructor parameters**: Base directory, configuration file
2. **Configuration file**: YAML configuration with stage settings
3. **Environment variables**: Override specific settings

Example Configuration
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   pipeline:
     stages:
       - spec_to_scaffolds
       - scaffold_to_requirements  
       - requirements_to_alignment
       - alignment_to_generation
     
     retry_attempts: 3
     timeout_seconds: 300
   
   output:
     preserve_intermediate: true
     create_reports: true

Error Handling
--------------

The orchestrator implements robust error handling:

* **Stage-level isolation**: Errors in one stage don't prevent others
* **Retry mechanisms**: Automatic retry with exponential backoff
* **Graceful degradation**: Partial results are preserved
* **Detailed logging**: Comprehensive error reporting

Examples
--------

Basic Usage
~~~~~~~~~~~

.. code-block:: python

   from asabaal_utils.agents.spec_coder.orchestrator import IntegrationOrchestrator
   
   orchestrator = IntegrationOrchestrator()
   
   success = orchestrator.run_pipeline(
       spec_file=Path("my_spec.yml"),
       output_dir=Path("./results")
   )
   
   if success:
       print("Pipeline completed successfully")
   else:
       print("Pipeline failed - check logs")

Custom Configuration
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   orchestrator = IntegrationOrchestrator(
       base_dir=Path("./workspace"),
       config_file=Path("custom_config.yaml")
   )
   
   # Run individual stages
   if orchestrator._stage1_spec_to_scaffolds(spec_file, output_dir):
       print("Stage 1 completed")
       if orchestrator._stage2_scaffold_to_requirements(output_dir):
           print("Stage 2 completed")

See Also
--------

* :doc:`generator` - Test generation functionality
* :doc:`tester` - Test execution and validation
* :doc:`spec_parser` - Specification parsing
* :doc:`user_guide/pipeline` - Pipeline workflow documentation