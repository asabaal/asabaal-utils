CodeGenerator API
=================

The ``CodeGenerator`` class is responsible for generating comprehensive test suites from specifications.

.. autoclass:: asabaal_utils.agents.spec_coder.generator.CodeGenerator
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Core Methods
------------

generate_tests
~~~~~~~~~~~~~~

.. automethod:: asabaal_utils.agents.spec_coder.generator.CodeGenerator.generate_tests
   :no-index:

Generates pytest test files from a specification. This is the main entry point for test generation.

**Parameters:**
- ``spec_data`` (dict): The specification data containing function definitions
- ``output_dir`` (Path): Directory where test files will be saved
- ``model`` (str, optional): AI model to use for generation

**Returns:**
- ``GenerationResult``: Object containing generation results and metadata

**Example:**

.. code-block:: python

   from asabaal_utils.agents.spec_coder.generator import CodeGenerator
   from asabaal_utils.agents.spec_coder.spec_parser import SpecParser
   
   # Parse specification
   parser = SpecParser()
   spec_data = parser.parse_file("my_spec.yml")
   
   # Generate tests
   generator = CodeGenerator()
   result = generator.generate_tests(spec_data, Path("./tests"))
   
   if result.success:
       print(f"Generated {result.files_created} test files")
   else:
       print(f"Generation failed: {result.error}")

_strip_markdown_code_blocks
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: asabaal_utils.agents.spec_coder.generator.CodeGenerator._strip_markdown_code_blocks

Cleans AI-generated content by removing instructional text and fixing indentation issues. This method is crucial for handling the IndentationError that was previously encountered in Stage 2.

**Parameters:**
- ``content`` (str): Raw content from AI generation

**Returns:**
- ``str``: Cleaned Python code

**Features:**
- Removes instructional text like "pytest test code only"
- Fixes indentation issues
- Preserves valid Python code structure
- Handles various AI response formats

GenerationResult Class
----------------------

.. autoclass:: asabaal_utils.agents.spec_coder.generator.GenerationResult
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Configuration
-------------

The CodeGenerator can be configured through:

1. **Constructor parameters**:
   - ``model``: AI model to use
   - ``base_url``: Ollama server URL
   - ``timeout``: Request timeout

2. **Environment variables**:
   - ``SPEC_CODER_MODEL``: Default AI model
   - ``SPEC_CODER_OLLAMA_URL``: Ollama server URL

Error Handling
--------------

The CodeGenerator handles various error scenarios:

* **Network errors**: Automatic retry with exponential backoff
* **Model errors**: Fallback to alternative models
* **Content errors**: Cleaning and validation of generated content
* **File system errors**: Proper error reporting and recovery

Examples
--------

Basic Usage
~~~~~~~~~~~

.. code-block:: python

   from asabaal_utils.agents.spec_coder.generator import CodeGenerator
   
   generator = CodeGenerator(model="llama3")
   
   spec_data = {
       "project_name": "My Project",
       "functions": [
           {
               "name": "add",
               "description": "Adds two numbers",
               "parameters": [
                   {"name": "a", "type": "int"},
                   {"name": "b", "type": "int"}
               ],
               "return_type": "int",
               "behaviors": ["Returns a + b", "Handles positive numbers"]
           }
       ]
   }
   
   result = generator.generate_tests(spec_data, Path("./tests"))
   
   for test_file in result.files_created:
       print(f"Created: {test_file}")

Advanced Usage
~~~~~~~~~~~~~~

.. code-block:: python

   from asabaal_utils.agents.spec_coder.generator import CodeGenerator
   
   # Custom configuration
   generator = CodeGenerator(
       model="codellama",
       base_url="http://localhost:11434",
       timeout=300
   )
   
   # Generate with custom prompt template
   result = generator.generate_tests(
       spec_data, 
       Path("./tests"),
       prompt_template="custom_test_template"
   )
   
   # Handle results
   if result.success:
       print(f"Success: {result.execution_time:.2f}s")
       for file_path in result.files_created:
           print(f"  - {file_path}")
   else:
       print(f"Error: {result.error}")
       if result.retry_count > 0:
           print(f"Retried {result.retry_count} times")

Best Practices
--------------

1. **Specification Quality**: Ensure your specifications are detailed and accurate
2. **Error Handling**: Always check ``result.success`` before using generated files
3. **File Management**: Use unique output directories for different specifications
4. **Model Selection**: Choose appropriate models for your use case:
   - ``llama3``: General purpose
   - ``codellama``: Code-specific tasks
   - ``llama2``: Lightweight option

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**Issue**: Generated tests have syntax errors

**Solution**: The ``_strip_markdown_code_blocks`` method should handle this automatically. If issues persist:

.. code-block:: python

   # Manually clean content
   cleaned = generator._strip_markdown_code_blocks(raw_content)
   
   # Validate Python syntax
   import ast
   try:
       ast.parse(cleaned)
       print("Content is valid Python")
   except SyntaxError as e:
       print(f"Syntax error: {e}")

**Issue**: Generation is very slow

**Solution**: 
- Use a faster model (llama2 instead of llama3)
- Reduce specification complexity
- Check network connectivity to Ollama server

**Issue**: Out of memory errors

**Solution**:
- Use smaller models
- Process functions individually
- Increase system RAM or use cloud-based solutions

Performance Tips
----------------

1. **Model Selection**: Use ``llama2`` for faster generation, ``llama3`` for better quality
2. **Batch Processing**: Generate multiple functions in a single request when possible
3. **Caching**: Cache results for repeated specifications
4. **Parallel Processing**: Use multiple generator instances for large projects

See Also
--------

* :doc:`orchestrator` - Pipeline orchestration
* :doc:`tester` - Test execution and validation
* :doc:`spec_parser` - Specification parsing
* :doc:`ollama_client` - AI model interface