Installation Guide
==================

This guide covers different installation methods for the Spec-Coder Agent.

System Requirements
-------------------

**Minimum Requirements:**

* Python 3.8 or higher
* 4GB RAM (8GB recommended)
* 2GB disk space

**Recommended Requirements:**

* Python 3.10 or higher
* 8GB RAM or more
* 5GB disk space
* Multi-core processor

**Optional Dependencies:**

* Ollama (for local AI model execution)
* Docker (for containerized deployment)
* Git (for version control integration)

Installation Methods
--------------------

Method 1: PyPI Installation (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install the latest stable version from PyPI:

.. code-block:: bash

   pip install asabaal-utils[spec-coder]

For development dependencies:

.. code-block:: bash

   pip install asabaal-utils[spec-coder,dev]

Method 2: Source Installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For the latest development version:

.. code-block:: bash

   git clone https://github.com/your-org/asabaal-utils.git
   cd asabaal-utils
   pip install -e .[spec-coder]

The ``-e`` flag installs in editable mode, allowing you to modify the source code.

Method 3: Development Setup
~~~~~~~~~~~~~~~~~~~~~~~~~~~

For contributors and developers:

.. code-block:: bash

   # Clone the repository
   git clone https://github.com/your-org/asabaal-utils.git
   cd asabaal-utils
   
   # Create a virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install in development mode
   pip install -e .[spec-coder,dev,test]
   
   # Install pre-commit hooks
   pre-commit install

Method 4: Docker Installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Using Docker for containerized deployment:

.. code-block:: bash

   # Pull the image
   docker pull asabaal-utils/spec-coder:latest
   
   # Run the container
   docker run -it --rm \
     -v $(pwd)/data:/app/data \
     asabaal-utils/spec-coder:latest \
     spec-coder run --spec /app/data/spec.yml --output /app/data/output

Or build from source:

.. code-block:: bash

   git clone https://github.com/your-org/asabaal-utils.git
   cd asabaal-utils
   docker build -t spec-coder .
   docker run -it spec-coder

Ollama Setup
------------

The Spec-Coder Agent uses Ollama for AI model execution. Install Ollama separately:

**Linux/macOS:**

.. code-block:: bash

   curl -fsSL https://ollama.ai/install.sh | sh

**Windows:**

Download and run the installer from https://ollama.ai/download/windows

**Start Ollama:**

.. code-block:: bash

   ollama serve

**Download a model:**

.. code-block:: bash

   ollama pull llama2
   # or
   ollama pull llama3
   # or
   ollama pull codellama

Configuration
-------------

After installation, configure the agent:

1. **Create a configuration file**:

.. code-block:: bash

   mkdir -p ~/.config/spec-coder
   cp /path/to/asabaal-utils/src/asabaal_utils/agents/spec_coder/config/config.yaml \
      ~/.config/spec-coder/config.yaml

2. **Edit the configuration**:

.. code-block:: yaml

   ollama:
     model: "llama3"  # or your preferred model
     base_url: "http://localhost:11434"
     timeout: 300
   
   pipeline:
     max_retries: 3
     parallel_stages: false
   
   output:
     base_dir: "./spec_coder_output"
     preserve_intermediate: true

3. **Verify the installation**:

.. code-block:: bash

   spec-coder --version
   spec-coder --help

Verification
------------

Test your installation with a simple example:

.. code-block:: bash

   # Create a test specification
   cat > test_spec.yml << EOF
   project_name: "Test Project"
   description: "A simple test project"
   functions:
     - name: "add_numbers"
       description: "Adds two numbers"
       parameters:
         - name: "a"
           type: "int"
         - name: "b"
           type: "int"
       return_type: "int"
       behaviors:
         - "Returns a + b"
         - "Handles positive numbers"
         - "Handles negative numbers"
   EOF

   # Run a quick test
   spec-coder generate --spec test_spec.yml --output ./test_output

   # Check the output
   ls -la test_output/

Troubleshooting
---------------

Common Installation Issues
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Issue**: ``pip: command not found``

**Solution**: Install pip first:

.. code-block:: bash

   python -m ensurepip --upgrade
   # or on Ubuntu/Debian:
   sudo apt-get install python3-pip

**Issue**: ``Permission denied`` during installation

**Solution**: Use a virtual environment or user installation:

.. code-block:: bash

   # Virtual environment (recommended)
   python -m venv venv
   source venv/bin/activate
   pip install asabaal-utils[spec-coder]
   
   # Or user installation
   pip install --user asabaal-utils[spec-coder]

**Issue**: ``ModuleNotFoundError`` after installation

**Solution**: Check your Python path and installation:

.. code-block:: bash

   python -c "import sys; print(sys.path)"
   pip show asabaal-utils
   which python

**Issue**: Ollama connection refused

**Solution**: Ensure Ollama is running:

.. code-block:: bash

   # Check if Ollama is running
   ps aux | grep ollama
   
   # Start Ollama if not running
   ollama serve &
   
   # Test connection
   curl http://localhost:11434/api/tags

Platform-Specific Issues
~~~~~~~~~~~~~~~~~~~~~~~~

**macOS**: If you encounter certificate errors:

.. code-block:: bash

   /Applications/Python\ 3.x/Install\ Certificates.command

**Windows**: If you encounter path issues:

.. code-block:: powershell

   # Add Python to PATH
   [Environment]::SetEnvironmentVariable("PATH", $env:PATH + ";C:\Python39\Scripts", "User")

**Linux**: If you encounter permission issues:

.. code-block:: bash

   # Use user installation
   pip install --user asabaal-utils[spec-coder]
   
   # Or fix permissions
   sudo chown -R $USER:$USER ~/.local

Getting Help
------------

If you encounter installation issues:

1. **Check the logs**: Run with ``--verbose`` flag for detailed output
2. **Search existing issues**: Check `GitHub Issues <https://github.com/your-org/asabaal-utils/issues>`_
3. **Create a new issue**: Include your OS, Python version, and error message
4. **Join discussions**: Ask questions in `GitHub Discussions <https://github.com/your-org/asabaal-utils/discussions>`_

Next Steps
----------

After successful installation:

* Read the :doc:`getting_started` guide
* Check the :doc:`user_guide/overview` for system understanding
* Review the :doc:`user_guide/configuration` for configuration options
* Explore the :doc:`user_guide/examples` for usage examples