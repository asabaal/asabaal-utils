SpecParser API
==============

The ``SpecParser`` class handles parsing and validation of specification files in various formats.

.. autoclass:: asabaal_utils.agents.spec_coder.spec_parser.SpecParser
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Core Methods
------------

parse_file
~~~~~~~~~~

.. automethod:: asabaal_utils.agents.spec_coder.spec_parser.SpecParser.parse_file

Parses a specification file and returns structured data.

**Parameters:**
- ``file_path`` (Path): Path to the specification file

**Returns:**
- ``dict``: Parsed specification data

validate_spec
~~~~~~~~~~~~~

.. automethod:: asabaal_utils.agents.spec_coder.spec_parser.SpecParser.validate_spec

Validates specification structure and content.

**Parameters:**
- ``spec_data`` (dict): Specification data to validate

**Returns:**
- ``ValidationResult``: Validation results

Examples
--------

.. code-block:: python

   from asabaal_utils.agents.spec_coder.spec_parser import SpecParser
   
   parser = SpecParser()
   spec_data = parser.parse_file("my_spec.yml")
   
   if parser.validate_spec(spec_data).valid:
       print("Specification is valid")
   else:
       print("Specification has errors")