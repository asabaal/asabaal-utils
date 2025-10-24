Getting Started
===============

This guide will help you get up and running with the Spec-Coder Agent quickly.

Prerequisites
-------------

Before you begin, ensure you have the following installed:

* Python 3.8 or higher
* pip (Python package manager)
* Git (for cloning repositories)

Installation
-------------

Method 1: Install from PyPI
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   pip install asabaal-utils[spec-coder]

Method 2: Install from Source
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   git clone https://github.com/your-org/asabaal-utils.git
   cd asabaal-utils
   pip install -e .[spec-coder]

Method 3: Development Installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For developers who want to contribute:

.. code-block:: bash

   git clone https://github.com/your-org/asabaal-utils.git
   cd asabaal-utils
   pip install -e .[spec-coder,dev]

Quick Start
-----------

1. **Create a specification file** (``example_spec.yml``):

.. code-block:: yaml

   project_name: "Example Project"
   description: "A simple example project"
   functions:
     - name: "multiply_by_2"
       description: "Multiplies a number by 2"
       parameters:
         - name: "n"
           type: "int"
           description: "The number to multiply"
       return_type: "int"
       behaviors:
         - "Returns n * 2"
         - "Handles positive numbers"
         - "Handles negative numbers"
         - "Handles zero"

2. **Run the complete pipeline**:

.. code-block:: bash

   spec-coder run --spec example_spec.yml --output ./results

3. **Check the results**:

.. code-block:: bash

   ls -la results/
   # Results will contain:
   # - scaffolds/ (generated tests and code)
   # - reports/ (analysis and alignment reports)
   # - stage4_generation/ (final implementation)

Basic Usage
-----------

Running Individual Stages
~~~~~~~~~~~~~~~~~~~~~~~~~

You can run individual stages of the pipeline:

**Stage 1: Generate Tests**

.. code-block:: bash

   spec-coder generate --spec example_spec.yml --output ./tests

**Stage 2: Analyze Tests**

.. code-block:: bash

   spec-coder analyze --input ./tests --output ./analysis

**Stage 3: Align Behaviors**

.. code-block:: bash

   spec-coder align --spec example_spec.yml --analysis ./analysis --output ./alignment

**Stage 4: Generate Final Code**

.. code-block:: bash

   spec-coder finalize --alignment ./alignment --output ./final_code

Configuration
-------------

The Spec-Coder Agent can be configured through:

1. **Command-line arguments** (see :doc:`user_guide/configuration`)
2. **Configuration files** (``config.yaml``)
3. **Environment variables**

Example configuration file (``config.yaml``):

.. code-block:: yaml

   ollama:
     model: "llama2"
     base_url: "http://localhost:11434"
   
   pipeline:
     stages:
       - generate
       - analyze
       - align
       - finalize
   
   output:
     format: "structured"
     include_tests: true
     include_docs: true

Common Workflows
---------------

Workflow 1: Test Generation Only
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you only need to generate tests from an existing specification:

.. code-block:: bash

   spec-coder generate \
     --spec your_spec.yml \
     --output ./tests \
     --format pytest

Workflow 2: Full Pipeline with Custom Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   spec-coder run \
     --spec your_spec.yml \
     --config custom_config.yaml \
     --output ./results \
     --model llama3 \
     --verbose

Workflow 3: Iterative Development
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For iterative development with feedback:

.. code-block:: bash

   # Generate initial tests
   spec-coder generate --spec spec.yml --output ./v1
   
   # Review and modify tests if needed
   
   # Continue with analysis
   spec-coder analyze --input ./v1 --output ./analysis
   
   # Complete the pipeline
   spec-coder run --spec spec.yml --from-stage analyze --output ./final

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**Issue**: ``ModuleNotFoundError: No module named 'asabaal_utils'``

**Solution**: Ensure you've installed the package in development mode or your Python path is set correctly.

**Issue**: ``Connection refused to Ollama server``

**Solution**: Make sure Ollama is running and accessible at the configured URL.

**Issue**: ``IndentationError in generated test files``

**Solution**: This should be automatically handled now. If it persists, check the specification format and try regenerating.

Getting Help
------------

* **Documentation**: Full documentation at :doc:`index`
* **Issues**: Report bugs on `GitHub Issues <https://github.com/your-org/asabaal-utils/issues>`_
* **Discussions**: Join our `GitHub Discussions <https://github.com/your-org/asabaal-utils/discussions>`_

Next Steps
----------

* Read the :doc:`user_guide/overview` for a detailed understanding of the system
* Check the :doc:`user_guide/pipeline` for in-depth pipeline documentation
* Explore the :doc:`api/modules` for detailed API reference
* Review the :doc:`testing/overview` for testing information