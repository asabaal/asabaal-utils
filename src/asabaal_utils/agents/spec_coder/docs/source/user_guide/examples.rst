Usage Examples
===============

This section provides practical examples of using the spec-coder agent for various scenarios and use cases.

Basic Usage
-----------

Software Generation from Specification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from spec_coder import IntegrationOrchestrator
   
   # Basic usage with default configuration
   orchestrator = IntegrationOrchestrator()
   
   result = orchestrator.run_pipeline(
       spec_file="calculator_spec.yml",
       output_dir="./generated_code"
   )
   
   if result.success:
       print(f"Generated {result.functions_created} functions")
       print(f"Code quality: {result.quality_score:.1f}%")
       print(f"All tests passing: {result.all_tests_passed}")
   else:
       print(f"Error: {result.error}")

Custom Model Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from spec_coder import IntegrationOrchestrator
   
   # Use a specific AI model for code generation
   orchestrator = IntegrationOrchestrator(
       model="codellama",
       base_url="http://localhost:11434",
       timeout=300
   )
   
   result = orchestrator.run_pipeline(
       spec_file="api_spec.yml",
       output_dir="./generated_api"
   )
   
   result = orchestrator.run_pipeline(
       spec_file="api_spec.yml",
       output_dir="./api_tests"
   )

Individual Component Usage
--------------------------

Using CodeGenerator Directly
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from spec_coder import CodeGenerator, SpecParser
   
   # Parse specification
   parser = SpecParser()
   spec_data = parser.parse_file("my_feature_spec.yml")
   
   # Generate software code
   generator = CodeGenerator(model="llama3")
   result = generator.generate_code(
       spec_data=spec_data,
       output_dir="./generated_feature"
   )
   
   print(f"Generated {len(result.files_created)} code files")
   for file_path in result.files_created:
       print(f"  - {file_path}")
   
   print(f"Functions created: {result.functions_created}")
   print(f"Classes created: {result.classes_created}")
   print(f"Tests generated: {result.tests_generated}")

Behavior Analysis Only
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from spec_coder import BehaviorComparator, SpecParser
   
   # Load specification and existing tests
   parser = SpecParser()
   spec = parser.parse_file("feature_spec.yml")
   
   comparator = BehaviorComparator()
   
   # Analyze existing test behaviors
   test_behaviors = comparator.load_test_behaviors(
       Path("test_analysis.json")
   )
   
   # Compare with specification
   comparison_result = comparator.compare_all_requirements(
       spec, test_behaviors
   )
   
   # Generate report
   report = comparator.generate_summary_report(comparison_result)
   
   print(f"Average alignment: {report['summary']['average_alignment_score']:.1%}")
   print(f"Critical gaps: {report['summary']['requirements_with_critical_issues']}")

Advanced Examples
-----------------

Custom Pipeline Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from spec_coder import IntegrationOrchestrator
   
   # Advanced configuration
   config = {
       "model": {
           "name": "codellama",
           "generation_config": {
               "temperature": 0.5,
               "max_tokens": 4096
           }
       },
       "pipeline": {
           "max_retries": 5,
           "parallel_stages": True,
           "continue_on_error": True
       },
       "stages": {
           "stage2": {
               "generate_edge_cases": True,
               "include_performance_tests": True
           },
           "stage4": {
               "analysis_depth": "comprehensive"
           }
       }
   }
   
   orchestrator = IntegrationOrchestrator(config=config)
   
    result = orchestrator.run_pipeline(
        spec_file="complex_feature_spec.yml",
        output_dir="./comprehensive_code"
    )

Batch Processing
~~~~~~~~~~~~~~~~

.. code-block:: python

   from spec_coder import IntegrationOrchestrator
   from pathlib import Path
   
   # Process multiple specifications
   spec_files = list(Path("specs/").glob("*.yml"))
   orchestrator = IntegrationOrchestrator()
   
   results = {}
   
   for spec_file in spec_files:
       print(f"Processing {spec_file.name}...")
       
        output_dir = f"./generated_code/{spec_file.stem}"
        result = orchestrator.run_pipeline(
            spec_file=str(spec_file),
            output_dir=output_dir
        )
        
        results[spec_file.name] = result
        
        if result.success:
            print(f"  ✓ Generated {result.functions_created} functions")
            print(f"  ✓ Code quality: {result.quality_score:.1f}%")
        else:
            print(f"  ✗ Failed: {result.error}")
   
   # Summary
   successful = sum(1 for r in results.values() if r.success)
   print(f"\nProcessed {len(spec_files)} specs, {successful} successful")

Real-World Scenarios
--------------------

Web API Testing
~~~~~~~~~~~~~~~

.. code-block:: python

   from spec_coder import IntegrationOrchestrator
   
   # API specification example
   api_spec = """
   project_name: "User Management API"
   functions:
     - name: "create_user"
       description: "Create a new user account"
       parameters:
         - name: "email"
           type: "string"
           validation: "email format"
         - name: "password"
           type: "string"
           validation: "min 8 characters"
       return_type: "User object"
       behaviors:
         - "Validates email format"
         - "Hashes password"
         - "Returns user ID"
         - "Handles duplicate emails"
   
     - name: "authenticate_user"
       description: "Authenticate user credentials"
       parameters:
         - name: "email"
           type: "string"
         - name: "password"
           type: "string"
       return_type: "Auth token"
       behaviors:
         - "Validates credentials"
         - "Returns JWT token"
         - "Handles invalid credentials"
         - "Handles account lockout"
   """
   
   # Save spec to file
   with open("user_api_spec.yml", "w") as f:
       f.write(api_spec)
   
    # Generate comprehensive API implementation
    orchestrator = IntegrationOrchestrator(
        model="codellama",
        config={
            "stages": {
                "stage2": {
                    "include_integration_tests": True,
                    "include_security_tests": True
                },
                "stage4": {
                    "code_style": "production",
                    "include_error_handling": True
                },
                "stage5": {
                    "auto_heal": True,
                    "max_heal_attempts": 3
                }
            }
        }
    )
    
    result = orchestrator.run_pipeline(
        spec_file="user_api_spec.yml",
        output_dir="./generated_api"
    )

Data Processing Pipeline
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from spec_coder import IntegrationOrchestrator
   
   # Data processing specification
   data_spec = """
   project_name: "Data Processing Pipeline"
   functions:
     - name: "process_csv_file"
       description: "Process CSV data file"
       parameters:
         - name: "file_path"
           type: "string"
         - name: "operations"
           type: "list of operations"
       return_type: "Processed data"
       behaviors:
         - "Validates file format"
         - "Handles missing data"
         - "Applies transformations"
         - "Handles large files"
         - "Logs processing steps"
   
     - name: "validate_data_quality"
       description: "Validate processed data quality"
       parameters:
         - name: "data"
           type: "DataFrame"
         - name: "quality_rules"
           type: "validation rules"
       return_type: "Quality report"
       behaviors:
         - "Checks data completeness"
         - "Validates data types"
         - "Detects outliers"
         - "Generates quality metrics"
   """
   
   orchestrator = IntegrationOrchestrator(
       model="llama3",
       config={
           "stages": {
               "stage2": {
                   "include_performance_tests": True,
                   "include_edge_case_tests": True
               }
           }
       }
   )
   
    result = orchestrator.run_pipeline(
        spec_file="data_pipeline_spec.yml",
        output_dir="./generated_data_pipeline"
    )

Error Handling Examples
-----------------------

Robust Error Handling
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from spec_coder import IntegrationOrchestrator
   import logging
   
   # Configure logging
   logging.basicConfig(level=logging.INFO)
   logger = logging.getLogger(__name__)
   
   def safe_pipeline_execution(spec_file, output_dir, max_retries=3):
       """Execute pipeline with robust error handling."""
       
       for attempt in range(max_retries):
           try:
               orchestrator = IntegrationOrchestrator(
                   max_retries=2,
                   continue_on_error=True,
                   fallback_models=["llama2", "llama3"]
               )
               
               result = orchestrator.run_pipeline(
                   spec_file=spec_file,
                   output_dir=output_dir
               )
               
               if result.success:
                   logger.info(f"Successfully processed {spec_file}")
                   return result
               else:
                   logger.warning(f"Attempt {attempt + 1} failed: {result.error}")
                   
           except Exception as e:
               logger.error(f"Attempt {attempt + 1} error: {str(e)}")
               
           if attempt == max_retries - 1:
               logger.error(f"Failed to process {spec_file} after {max_retries} attempts")
               raise
       
       return None
   
   # Usage
   try:
        result = safe_pipeline_execution(
            "complex_spec.yml",
            "./generated_robust_code"
        )
   except Exception as e:
       print(f"Pipeline failed: {e}")
       # Implement fallback logic

Partial Success Handling
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from spec_coder import IntegrationOrchestrator
   
   orchestrator = IntegrationOrchestrator(continue_on_error=True)
   
    result = orchestrator.run_pipeline(
        spec_file="problematic_spec.yml",
        output_dir="./partial_generated_code"
    )
   
   # Handle partial success
   if result.success:
       print("Complete success!")
   elif result.partial_success:
       print(f"Partial success: {result.successful_stages}/4 stages completed")
       
       # Check which stages succeeded
       for stage_name, stage_result in result.stage_results.items():
           if stage_result.success:
               print(f"  ✓ {stage_name}")
           else:
               print(f"  ✗ {stage_name}: {stage_result.error}")
   else:
       print(f"Complete failure: {result.error}")

Integration Examples
--------------------

CI/CD Integration
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # ci_test_generation.py
   from spec_coder import IntegrationOrchestrator
   import os
   import sys
   
   def main():
        spec_file = os.environ.get("SPEC_FILE")
        output_dir = os.environ.get("OUTPUT_DIR", "./generated_code")
       
       if not spec_file:
           print("ERROR: SPEC_FILE environment variable required")
           sys.exit(1)
       
       orchestrator = IntegrationOrchestrator(
           model=os.environ.get("MODEL", "llama3"),
           timeout=int(os.environ.get("TIMEOUT", "300"))
       )
       
       result = orchestrator.run_pipeline(
           spec_file=spec_file,
           output_dir=output_dir
       )
       
        if result.success:
            print(f"✓ Generated {result.functions_created} functions")
            print(f"✓ Code quality: {result.quality_score:.1f}%")
            print(f"✓ All tests passing: {result.all_tests_passed}")
            sys.exit(0)
        else:
            print(f"✗ Failed: {result.error}")
            sys.exit(1)
   
   if __name__ == "__main__":
       main()

GitHub Actions Example
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

    # .github/workflows/generate-code.yml
    name: Generate Code from Specifications
   
   on:
     push:
       paths:
         - 'specs/**/*.yml'
     pull_request:
       paths:
         - 'specs/**/*.yml'
   
   jobs:
     generate-tests:
       runs-on: ubuntu-latest
       
       steps:
       - uses: actions/checkout@v3
       
       - name: Set up Python
         uses: actions/setup-python@v4
         with:
           python-version: '3.11'
       
       - name: Install dependencies
         run: |
           pip install spec-coder
           pip install ollama
       
       - name: Start Ollama
         run: |
           ollama serve &
           sleep 10
           ollama pull llama3
       
        - name: Generate code
          env:
            SPEC_FILE: specs/api/user_management.yml
            OUTPUT_DIR: generated_code
            MODEL: llama3
          run: python ci_code_generation.py
        
        - name: Run generated tests
          run: |
            pip install pytest
            pytest generated_code/tests/ -v
        
        - name: Upload generated code
          uses: actions/upload-artifact@v3
          with:
            name: generated-code
            path: generated_code/

Performance Optimization
------------------------

Caching Results
~~~~~~~~~~~~~~~

.. code-block:: python

   from spec_coder import IntegrationOrchestrator
   import hashlib
   import json
   from pathlib import Path
   
   class CachedOrchestrator:
       def __init__(self, cache_dir="./cache"):
           self.cache_dir = Path(cache_dir)
           self.cache_dir.mkdir(exist_ok=True)
           self.orchestrator = IntegrationOrchestrator()
       
       def _get_cache_key(self, spec_file, config):
           """Generate cache key based on spec content and config."""
           spec_content = Path(spec_file).read_text()
           content = spec_content + json.dumps(config, sort_keys=True)
           return hashlib.md5(content.encode()).hexdigest()
       
       def run_pipeline_cached(self, spec_file, output_dir, config=None):
           """Run pipeline with caching."""
           cache_key = self._get_cache_key(spec_file, config or {})
           cache_file = self.cache_dir / f"{cache_key}.json"
           
           # Check cache
           if cache_file.exists():
               print(f"Loading from cache: {cache_key}")
               cached_result = json.loads(cache_file.read_text())
               return cached_result
           
           # Run pipeline
           result = self.orchestrator.run_pipeline(
               spec_file=spec_file,
               output_dir=output_dir
           )
           
            # Cache result
            if result.success:
                cache_file.write_text(json.dumps({
                    'success': True,
                    'functions_created': result.functions_created,
                    'quality_score': result.quality_score,
                    'all_tests_passed': result.all_tests_passed,
                    'execution_time': result.execution_time
                }))
           
           return result
   
    # Usage
    cached_orchestrator = CachedOrchestrator()
    result = cached_orchestrator.run_pipeline_cached(
        "api_spec.yml",
        "./cached_generated_code"
    )

Parallel Processing
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from spec_coder import IntegrationOrchestrator
   from concurrent.futures import ThreadPoolExecutor, as_completed
   from pathlib import Path
   
   def process_specification(spec_file, output_base_dir):
       """Process a single specification."""
       try:
           orchestrator = IntegrationOrchestrator()
           output_dir = output_base_dir / spec_file.stem
           
           result = orchestrator.run_pipeline(
               spec_file=str(spec_file),
               output_dir=str(output_dir)
           )
           
            return {
                'spec_file': spec_file.name,
                'success': result.success,
                'functions_created': getattr(result, 'functions_created', 0),
                'quality_score': getattr(result, 'quality_score', 0),
                'error': getattr(result, 'error', None)
            }
       except Exception as e:
           return {
               'spec_file': spec_file.name,
               'success': False,
               'error': str(e)
           }
   
   def batch_process_specifications(spec_dir, output_dir, max_workers=4):
       """Process multiple specifications in parallel."""
       spec_files = list(Path(spec_dir).glob("*.yml"))
       output_base_dir = Path(output_dir)
       output_base_dir.mkdir(exist_ok=True)
       
       results = []
       
       with ThreadPoolExecutor(max_workers=max_workers) as executor:
           # Submit all jobs
           future_to_spec = {
               executor.submit(process_specification, spec_file, output_base_dir): spec_file
               for spec_file in spec_files
           }
           
           # Collect results
           for future in as_completed(future_to_spec):
               spec_file = future_to_spec[future]
               try:
                   result = future.result()
                   results.append(result)
                   
                   status = "✓" if result['success'] else "✗"
                   print(f"{status} {result['spec_file']}")
                   
               except Exception as e:
                   print(f"✗ {spec_file.name}: {e}")
       
       return results
   
    # Usage
    results = batch_process_specifications(
        "./specs",
        "./parallel_generated_code",
        max_workers=4
    )
   
   successful = sum(1 for r in results if r['success'])
   print(f"\nProcessed {len(results)} specs, {successful} successful")

Next Steps
----------

* :doc:`../getting_started` - Basic setup and quick start
* :doc:`configuration` - Detailed configuration options
* :doc:`../api/modules` - Complete API reference
* :doc:`../testing/overview` - Testing strategies and best practices