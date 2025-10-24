Debugging Guide
===============

This guide provides comprehensive debugging strategies and tools for troubleshooting issues in the spec-coder system.

Common Issues and Solutions
---------------------------

Installation and Setup Issues
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Issue**: Ollama Connection Failed
.. code-block:: text

   Error: Failed to connect to Ollama server at http://localhost:11434

**Solutions**:
1. **Check Ollama Service**:
   .. code-block:: bash

      # Check if Ollama is running
      ps aux | grep ollama
      
      # Start Ollama service
      ollama serve

2. **Verify Port Availability**:
   .. code-block:: bash

      # Check if port 11434 is available
      netstat -tlnp | grep 11434
      
      # Kill any process using the port
      sudo fuser -k 11434/tcp

3. **Check Firewall Settings**:
   .. code-block:: bash

      # Allow port 11434 through firewall
      sudo ufw allow 11434

**Issue**: Model Not Found
.. code-block:: text

   Error: Model 'llama3' not found

**Solutions**:
1. **Pull Required Models**:
   .. code-block:: bash

      ollama pull llama3
      ollama pull codellama
      ollama pull qwen3-coder

2. **List Available Models**:
   .. code-block:: bash

      ollama list

3. **Update Model Configuration**:
   .. code-block:: python

      config = {
          "model": {
              "name": "llama2",  # Use available model
              "base_url": "http://localhost:11434"
          }
      }

Pipeline Execution Issues
~~~~~~~~~~~~~~~~~~~~~~~~~

**Issue**: Pipeline Stuck at Stage 2
.. code-block:: text

   Pipeline running... (stuck for long time)

**Solutions**:
1. **Check AI Model Response**:
   .. code-block:: python

      # Test model directly
      from spec_coder import OllamaClient
      client = OllamaClient()
      response = client.generate("llama3", "Hello, world!")
      print(response)

2. **Increase Timeout**:
   .. code-block:: python

      config = {
          "model": {
              "timeout": 600  # Increase to 10 minutes
          }
      }

3. **Use Faster Model**:
   .. code-block:: python

      config = {
          "stages": {
              "stage2": {
                  "model": "llama2"  # Faster but less capable
              }
          }
      }

**Issue**: Memory Usage Too High
.. code-block:: text

   MemoryError: Unable to allocate memory

**Solutions**:
1. **Reduce Batch Size**:
   .. code-block:: python

      config = {
          "pipeline": {
              "batch_size": 1  # Process one item at a time
          }
      }

2. **Enable Streaming**:
   .. code-block:: python

      config = {
          "model": {
              "stream": True
          }
      }

3. **Clear Cache**:
   .. code-block:: python

      # Clear AI model cache
      ollama rm llama3
      ollama pull llama3

Code Generation Issues
~~~~~~~~~~~~~~~~~~~~~~

**Issue**: Generated Code Has Syntax Errors
.. code-block:: text

   SyntaxError: invalid syntax

**Solutions**:
1. **Enable Auto-Healing**:
   .. code-block:: python

      config = {
          "stages": {
              "stage5": {
                  "auto_heal": True,
                  "max_heal_attempts": 5
              }
          }
      }

2. **Check Model Temperature**:
   .. code-block:: python

      config = {
          "model": {
              "generation_config": {
                  "temperature": 0.3  # Lower for more deterministic output
              }
          }
      }

3. **Validate Input Specification**:
   .. code-block:: python

      from spec_coder import SpecParser
      parser = SpecParser()
      spec = parser.parse_file("spec.yml")
      validation = parser.validate_spec(spec)
      print(validation.errors)

**Issue**: Generated Code Doesn't Match Requirements
.. code-block:: text

   Generated function doesn't implement required behavior

**Solutions**:
1. **Improve Specification**:
   .. code-block:: yaml

      functions:
        - name: "calculate_total"
          description: "Calculate total with tax"
          parameters:
            - name: "amount"
              type: "float"
            - name: "tax_rate"
              type: "float"
          behaviors:
            - "Multiplies amount by (1 + tax_rate)"
            - "Returns float with 2 decimal places"
            - "Handles negative amounts"
          examples:
            - "calculate_total(100, 0.1) returns 110.00"

2. **Adjust Generation Parameters**:
   .. code-block:: python

      config = {
          "stages": {
              "stage4": {
                  "model": "codellama",
                  "generation_config": {
                      "temperature": 0.5,
                      "max_tokens": 4096
                  }
              }
          }
      }

3. **Enable Detailed Analysis**:
   .. code-block:: python

      config = {
          "stages": {
              "stage3": {
                  "analysis_depth": "comprehensive"
              }
          }
      }

Test Execution Issues
~~~~~~~~~~~~~~~~~~~~~

**Issue**: Tests Fail on Generated Code
.. code-block:: text

   AssertionError: Expected 5 but got 3

**Solutions**:
1. **Check Test Logic**:
   .. code-block:: python

      # Review generated test
      with open("generated_tests/test_function.py", "r") as f:
           print(f.read())

2. **Enable Healing**:
   .. code-block:: python

      config = {
          "stages": {
              "stage5": {
                  "auto_heal": True,
                  "heal_strategy": "test_driven"
              }
          }
      }

3. **Manual Intervention**:
   .. code-block:: python

      # Fix code manually and re-run tests
      result = orchestrator.run_stage("stage5", context)

Debugging Tools and Techniques
------------------------------

Logging and Monitoring
~~~~~~~~~~~~~~~~~~~~~~

**Enable Debug Logging**:
.. code-block:: python

   import logging
   
   # Enable debug logging
   logging.basicConfig(
       level=logging.DEBUG,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   )
   
   # Or use configuration
   config = {
       "logging": {
           "level": "DEBUG",
           "file": "debug.log"
       }
   }

**Monitor Pipeline Progress**:
.. code-block:: python

   from spec_coder import IntegrationOrchestrator
   
   orchestrator = IntegrationOrchestrator()
   
   # Add progress callback
   def progress_callback(stage, status, progress):
       print(f"Stage {stage}: {status} ({progress:.1f}%)")
   
   result = orchestrator.run_pipeline(
       spec_file="spec.yml",
       output_dir="./output",
       progress_callback=progress_callback
   )

**Analyze Pipeline Metrics**:
.. code-block:: python

   # Get detailed pipeline metrics
   result = orchestrator.run_pipeline("spec.yml", "./output")
   
   for stage_name, stage_result in result.stage_results.items():
       print(f"{stage_name}:")
       print(f"  Success: {stage_result.success}")
       print(f"  Duration: {stage_result.duration:.2f}s")
       print(f"  Memory: {stage_result.memory_usage:.1f}MB")
       print(f"  Errors: {len(stage_result.errors)}")

Interactive Debugging
~~~~~~~~~~~~~~~~~~~~~

**Debug Individual Stages**:
.. code-block:: python

   from spec_coder import IntegrationOrchestrator
   
   orchestrator = IntegrationOrchestrator()
   
   # Run stages one by one
   context = orchestrator.create_context("spec.yml", "./output")
   
   # Stage 1
   stage1_result = orchestrator.run_stage("stage1", context)
   print(f"Stage 1: {stage1_result.success}")
   
   # Stage 2
   if stage1_result.success:
       context = orchestrator.update_context(context, stage1_result)
       stage2_result = orchestrator.run_stage("stage2", context)
       print(f"Stage 2: {stage2_result.success}")

**Inspect Intermediate Results**:
.. code-block:: python

   # Check parsed specification
   from spec_coder import SpecParser
   parser = SpecParser()
   spec = parser.parse_file("spec.yml")
   print(f"Functions: {len(spec.functions)}")
   print(f"Behaviors: {len(spec.behaviors)}")
   
   # Check generated tests
   from spec_coder import CodeGenerator
   generator = CodeGenerator()
   test_result = generator.generate_tests(spec)
   print(f"Test files: {test_result.files_created}")

**Test AI Model Responses**:
.. code-block:: python

   from spec_coder import OllamaClient
   
   client = OllamaClient()
   
   # Test simple prompt
   response = client.generate("llama3", "Write a Python function that adds two numbers.")
   print(response)
   
   # Test with specification
   spec_prompt = """
   Generate a Python function based on this specification:
   - Name: calculate_area
   - Parameters: width (float), height (float)
   - Returns: float (area)
   - Behavior: multiplies width by height
   """
   response = client.generate("codellama", spec_prompt)
   print(response)

Performance Debugging
~~~~~~~~~~~~~~~~~~~~~

**Profile Pipeline Performance**:
.. code-block:: python

   import cProfile
   import pstats
   
   # Profile pipeline execution
   profiler = cProfile.Profile()
   profiler.enable()
   
   result = orchestrator.run_pipeline("spec.yml", "./output")
   
   profiler.disable()
   stats = pstats.Stats(profiler)
   stats.sort_stats('cumulative')
   stats.print_stats(10)  # Top 10 functions

**Memory Usage Analysis**:
.. code-block:: python

   import tracemalloc
   
   # Start memory tracing
   tracemalloc.start()
   
   result = orchestrator.run_pipeline("spec.yml", "./output")
   
   # Get memory statistics
   current, peak = tracemalloc.get_traced_memory()
   print(f"Current memory usage: {current / 1024 / 1024:.1f} MB")
   print(f"Peak memory usage: {peak / 1024 / 1024:.1f} MB")
   
   tracemalloc.stop()

**AI Model Performance**:
.. code-block:: python

   import time
   
   from spec_coder import OllamaClient
   
   client = OllamaClient()
   
   # Test model response times
   models = ["llama2", "llama3", "codellama"]
   prompt = "Write a simple Python function."
   
   for model in models:
       start_time = time.time()
       response = client.generate(model, prompt)
       end_time = time.time()
       
       print(f"{model}: {end_time - start_time:.2f}s ({len(response)} chars)")

Error Analysis
--------------

Common Error Types
~~~~~~~~~~~~~~~~~~

**Specification Errors**:
- Invalid YAML syntax
- Missing required fields
- Type mismatches
- Circular dependencies

**AI Model Errors**:
- Model not available
- Timeout exceeded
- Invalid response format
- Content policy violations

**Pipeline Errors**:
- Stage dependency failures
- Resource exhaustion
- File system issues
- Network connectivity problems

**Code Generation Errors**:
- Syntax errors
- Logic errors
- Import errors
- Type errors

Error Diagnosis Workflow
~~~~~~~~~~~~~~~~~~~~~~~

**1. Identify Error Location**:
.. code-block:: python

   # Check which stage failed
   result = orchestrator.run_pipeline("spec.yml", "./output")
   
   for stage_name, stage_result in result.stage_results.items():
       if not stage_result.success:
           print(f"Failed stage: {stage_name}")
           print(f"Error: {stage_result.error}")
           print(f"Traceback: {stage_result.traceback}")

**2. Analyze Error Context**:
.. code-block:: python

   # Get detailed error information
   failed_stage = result.get_failed_stage()
   
   print(f"Stage: {failed_stage.name}")
   print(f"Input: {failed_stage.input_data}")
   print(f"Configuration: {failed_stage.config}")
   print(f"Environment: {failed_stage.environment}")

**3. Reproduce Error**:
.. code-block:: python

   # Create minimal reproduction case
   minimal_spec = """
   project_name: "Test"
   functions:
     - name: "test_func"
       description: "Test function"
       parameters: []
       return_type: "str"
   """
   
   # Save minimal spec
   with open("minimal_spec.yml", "w") as f:
       f.write(minimal_spec)
   
   # Test with minimal spec
   result = orchestrator.run_pipeline("minimal_spec.yml", "./minimal_output")

**4. Test Fix**:
.. code-block:: python

   # Apply potential fix
   config_fix = {
       "model": {
           "timeout": 600,
           "temperature": 0.3
       }
   }
   
   orchestrator = IntegrationOrchestrator(config=config_fix)
   result = orchestrator.run_pipeline("spec.yml", "./fixed_output")

Debugging Checklist
-------------------

Pre-Execution Checklist
~~~~~~~~~~~~~~~~~~~~~~

- [ ] Ollama service is running
- [ ] Required models are pulled
- [ ] Specification file is valid
- [ ] Output directory exists and is writable
- [ ] Configuration is properly set
- [ ] Dependencies are installed
- [ ] Sufficient memory and disk space

Runtime Checklist
~~~~~~~~~~~~~~~~~

- [ ] Monitor memory usage
- [ ] Check network connectivity
- [ ] Watch for timeout errors
- [ ] Verify AI model responses
- [ ] Log all errors and warnings
- [ ] Track pipeline progress

Post-Execution Checklist
~~~~~~~~~~~~~~~~~~~~~~~

- [ ] Review generated code quality
- [ ] Run all tests successfully
- [ ] Check documentation completeness
- [ ] Verify performance metrics
- [ ] Analyze error logs
- [ ] Validate output structure

Advanced Debugging
-----------------

Custom Debug Hooks
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class DebugOrchestrator(IntegrationOrchestrator):
       def __init__(self, *args, **kwargs):
           super().__init__(*args, **kwargs)
           self.debug_data = {}
       
       def run_stage(self, stage_name, context):
           # Log stage start
           print(f"[DEBUG] Starting {stage_name}")
           print(f"[DEBUG] Context: {context}")
           
           # Run stage
           result = super().run_stage(stage_name, context)
           
           # Log stage result
           print(f"[DEBUG] {stage_name} result: {result.success}")
           if not result.success:
               print(f"[DEBUG] Error: {result.error}")
           
           # Store debug data
           self.debug_data[stage_name] = {
               "input": context,
               "output": result,
               "timestamp": time.time()
           }
           
           return result

Remote Debugging
~~~~~~~~~~~~~~~~

.. code-block:: python

   # Enable remote debugging
   import debugpy
   
   debugpy.listen(5678)
   print("Waiting for debugger attach...")
   debugpy.wait_for_client()
   
   # Run pipeline with debugger
   orchestrator = IntegrationOrchestrator()
   result = orchestrator.run_pipeline("spec.yml", "./output")

Automated Testing
~~~~~~~~~~~~~~~~~

.. code-block:: python

   import pytest
   
   class TestSpecCoderDebugging:
       def test_pipeline_with_debug_spec(self):
           """Test pipeline with known good specification."""
           spec_file = "tests/fixtures/debug_spec.yml"
           output_dir = "/tmp/debug_output"
           
           orchestrator = IntegrationOrchestrator()
           result = orchestrator.run_pipeline(spec_file, output_dir)
           
           assert result.success
           assert result.functions_created > 0
           assert result.all_tests_passed
       
       def test_error_handling(self):
           """Test error handling with invalid specification."""
           spec_file = "tests/fixtures/invalid_spec.yml"
           
           orchestrator = IntegrationOrchestrator()
           result = orchestrator.run_pipeline(spec_file, "/tmp/error_output")
           
           assert not result.success
           assert "ValidationError" in result.error

This debugging guide provides comprehensive strategies for identifying, diagnosing, and resolving issues in the spec-coder system. Use these tools and techniques to maintain system reliability and performance.