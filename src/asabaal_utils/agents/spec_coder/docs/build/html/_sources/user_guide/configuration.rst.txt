Configuration Guide
===================

The spec-coder agent provides extensive configuration options to customize behavior, performance, and output formats.

Configuration Methods
---------------------

Configuration can be provided through multiple methods:

1. **Environment Variables**: Global settings
2. **Configuration Files**: YAML/JSON configuration files
3. **Constructor Parameters**: Runtime configuration
4. **Command Line Arguments**: CLI configuration

Environment Variables
---------------------

Global configuration through environment variables:

.. code-block:: bash

   # AI Model Configuration
   export SPEC_CODER_MODEL="llama3"
   export SPEC_CODER_OLLAMA_URL="http://localhost:11434"
   export SPEC_CODER_TIMEOUT=300
   
   # Pipeline Configuration
   export SPEC_CODER_MAX_RETRIES=3
   export SPEC_CODER_RETRY_DELAY=5
   export SPEC_CODER_PARALLEL_STAGES=true
   
# Output Configuration
    export SPEC_CODER_OUTPUT_DIR="./generated_code"
    export SPEC_CODER_VERBOSE=true
    export SPEC_CODER_LOG_LEVEL="INFO"

Configuration Files
-------------------

YAML Configuration File
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # spec_coder_config.yml
   model:
     name: "llama3"
     base_url: "http://localhost:11434"
     timeout: 300
     generation_config:
       temperature: 0.7
       max_tokens: 2048
   
   pipeline:
     max_retries: 3
     retry_delay: 5
     parallel_stages: true
     continue_on_error: true
   
    stages:
      stage1:
        enabled: true
        output_format: "python"
      stage2:
        enabled: true
        model: "codellama"
        generate_edge_cases: true
      stage3:
        enabled: true
        test_framework: "pytest"
      stage4:
        enabled: true
        analysis_depth: "comprehensive"
      stage5:
        enabled: true
        auto_heal: true
        max_heal_attempts: 3
    
    output:
      base_dir: "./generated_code"
      create_docs: true
      create_scaffolds: true
      file_naming: "descriptive"
   
   logging:
     level: "INFO"
     file: "spec_coder.log"
     format: "detailed"

JSON Configuration File
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: json

   {
     "model": {
       "name": "llama3",
       "base_url": "http://localhost:11434",
       "timeout": 300
     },
     "pipeline": {
       "max_retries": 3,
       "retry_delay": 5,
       "parallel_stages": true
     },
      "output": {
        "base_dir": "./generated_code",
        "create_docs": true
      }
   }

Constructor Configuration
------------------------

Direct configuration through code:

.. code-block:: python

   from spec_coder import IntegrationOrchestrator, CodeGenerator
   
   # Configure individual components
   generator = CodeGenerator(
       model="codellama",
       base_url="http://localhost:11434",
       timeout=300,
       temperature=0.7,
       max_tokens=2048
   )
   
   orchestrator = IntegrationOrchestrator(
       config_file="spec_coder_config.yml",
       max_retries=3,
       parallel_stages=True,
       continue_on_error=True
   )

Model Configuration
-------------------

AI Model Settings
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Model selection and configuration
   model_config = {
       "name": "llama3",  # llama3, codellama, llama2, qwen3-coder
       "base_url": "http://localhost:11434",
       "timeout": 300,
       "generation_config": {
           "temperature": 0.7,      # 0.0-1.0, higher = more creative
           "max_tokens": 2048,      # Maximum response length
           "top_p": 0.9,           # Nucleus sampling
           "frequency_penalty": 0.1, # Reduce repetition
           "presence_penalty": 0.1   # Encourage new topics
       }
   }

Available Models
~~~~~~~~~~~~~~~~

* **llama3**: General-purpose model, good balance of quality and speed
* **codellama**: Specialized for code generation tasks
* **llama2**: Lightweight model, faster but less capable
* **qwen3-coder**: Advanced coding model with excellent reasoning

Model Selection Guidelines
~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Speed Priority**: Use llama2 for quick prototyping
* **Quality Priority**: Use codellama or qwen3-coder for production
* **Balance**: Use llama3 for general development
* **Resource Constraints**: Consider model size and available memory

Pipeline Configuration
----------------------

Stage Configuration
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Configure individual pipeline stages
   pipeline_config = {
       "stage1": {
           "enabled": True,
           "output_format": "python",
           "validate_syntax": True,
           "create_docs": True
       },
       "stage2": {
           "enabled": True,
           "model": "codellama",
           "generate_edge_cases": True,
           "include_performance_tests": False,
           "test_density": "comprehensive"  # minimal, standard, comprehensive
       },
       "stage3": {
           "enabled": True,
           "test_framework": "pytest",
           "parallel_execution": True,
           "timeout_per_test": 30
       },
        "stage4": {
            "enabled": True,
            "analysis_depth": "comprehensive",  # basic, standard, comprehensive
            "gap_analysis": True,
            "recommendation_level": "detailed"
        },
        "stage5": {
            "enabled": True,
            "auto_heal": True,
            "max_heal_attempts": 3,
            "heal_timeout": 300
        }
   }

Error Handling
~~~~~~~~~~~~~~

.. code-block:: python

   # Error handling configuration
   error_config = {
       "max_retries": 3,
       "retry_delay": 5,  # seconds
       "exponential_backoff": True,
       "continue_on_error": True,
       "fallback_models": ["llama2", "llama3"],
       "error_recovery": {
           "syntax_errors": "auto_fix",
           "import_errors": "add_imports",
           "logic_errors": "regenerate"
       }
   }

Output Configuration
-------------------

File Organization
~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Output structure configuration
    output_config = {
        "base_dir": "./generated_code",
        "structure": "feature_based",  # feature_based, flat, hierarchical
        "file_naming": "descriptive",  # descriptive, numeric, uuid
        "create_subdirs": {
            "code": True,
            "tests": True,
            "docs": True,
            "scaffolds": True,
            "reports": True
        },
        "file_extensions": {
            "code": ".py",
            "tests": ".py",
            "docs": ".md",
            "reports": ".json"
        }
    }

Content Generation
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Content generation settings
    content_config = {
        "include_docstrings": True,
        "include_type_hints": True,
        "include_error_handling": True,
        "include_edge_cases": True,
        "include_performance_tests": False,
        "include_unit_tests": True,
        "test_style": "pytest",  # pytest, unittest, custom
        "code_style": {
            "line_length": 88,
            "use_black_formatting": True,
            "import_style": "sorted"
        },
        "generation_focus": "production"  # prototype, production, educational
    }

Performance Configuration
------------------------

Parallel Processing
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Performance optimization
   performance_config = {
       "parallel_stages": True,
       "max_workers": 4,
       "chunk_size": 10,
       "memory_limit": "4GB",
       "cache_enabled": True,
       "cache_dir": "./cache",
       "cache_ttl": 3600  # seconds
   }

Resource Management
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Resource limits
   resource_config = {
       "max_memory_usage": "4GB",
       "max_cpu_usage": 80,  # percentage
       "max_concurrent_requests": 3,
       "request_timeout": 300,
       "batch_processing": True,
       "batch_size": 5
   }

Logging Configuration
---------------------

Log Levels
~~~~~~~~~~

.. code-block:: python

   # Logging configuration
   logging_config = {
       "level": "INFO",  # DEBUG, INFO, WARNING, ERROR, CRITICAL
       "file": "spec_coder.log",
       "format": "detailed",  # simple, detailed, json
       "rotation": {
           "enabled": True,
           "max_size": "10MB",
           "backup_count": 5
       },
       "handlers": {
           "console": True,
           "file": True,
           "remote": False
       }
   }

Log Formats
~~~~~~~~~~~

.. code-block:: python

   # Custom log formatting
   format_config = {
       "simple": "%(levelname)s: %(message)s",
       "detailed": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
       "json": {
           "timestamp": True,
           "level": True,
           "module": True,
           "function": True,
           "line": True,
           "message": True
       }
   }

Advanced Configuration
---------------------

Custom Templates
~~~~~~~~~~~~~~~~

.. code-block:: python

   # Custom template configuration
   template_config = {
       "test_template": "custom_test_template.py.j2",
       "doc_template": "custom_doc_template.md.j2",
       "scaffold_template": "custom_scaffold_template.py.j2",
       "template_variables": {
           "author": "Development Team",
           "company": "Your Company",
           "license": "MIT",
           "version": "1.0.0"
       }
   }

Integration Settings
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # External tool integration
   integration_config = {
       "git": {
           "auto_commit": False,
           "commit_message_template": "feat: generated tests for {feature}",
           "branch": "generated-tests"
       },
       "ci_cd": {
           "github_actions": True,
           "pipeline_file": ".github/workflows/test-generation.yml"
       },
       "documentation": {
           "generate_docs": True,
           "format": "markdown",
           "include_api_docs": True
       }
   }

Configuration Validation
------------------------

The spec-coder agent includes configuration validation:

.. code-block:: python

   from spec_coder import validate_config
   
   # Validate configuration
   config = {
       "model": {"name": "llama3"},
       "pipeline": {"max_retries": 3}
   }
   
   validation_result = validate_config(config)
   
   if validation_result.is_valid:
       print("Configuration is valid")
   else:
       print(f"Configuration errors: {validation_result.errors}")
       print(f"Warnings: {validation_result.warnings}")

Best Practices
--------------

1. **Start Simple**: Begin with basic configuration and add complexity as needed
2. **Environment-Specific**: Use different configurations for development, testing, and production
3. **Version Control**: Store configuration files in version control
4. **Documentation**: Document custom configuration options
5. **Validation**: Always validate configuration before use
6. **Monitoring**: Monitor performance and adjust configuration accordingly

Example: Complete Configuration
--------------------------------

.. code-block:: yaml

   # production_config.yml
   model:
     name: "codellama"
     base_url: "http://localhost:11434"
     timeout: 600
     generation_config:
       temperature: 0.5
       max_tokens: 4096
   
   pipeline:
     max_retries: 5
     retry_delay: 10
     parallel_stages: true
     continue_on_error: false
   
   stages:
     stage2:
       generate_edge_cases: true
       include_performance_tests: true
       test_density: "comprehensive"
     stage4:
       analysis_depth: "comprehensive"
       gap_analysis: true
   
    output:
      base_dir: "./production_code"
      create_docs: true
      file_naming: "descriptive"
   
   performance:
     parallel_stages: true
     max_workers: 8
     cache_enabled: true
   
   logging:
     level: "INFO"
     file: "production.log"
     format: "json"

Next Steps
----------

* :doc:`../getting_started` - Quick start with default configuration
* :doc:`../api/modules` - Detailed API documentation
* :doc:`examples` - Configuration examples and use cases