OllamaClient API
================

The ``OllamaClient`` class provides interface to Ollama AI models for code generation and analysis.

.. autoclass:: asabaal_utils.agents.spec_coder.ollama_client.OllamaClient
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Core Methods
------------

generate
~~~~~~~~~

.. automethod:: asabaal_utils.agents.spec_coder.ollama_client.OllamaClient.generate

Generates text using Ollama models.

**Parameters:**
- ``prompt`` (str): Input prompt for generation
- ``model`` (str, optional): Model to use
- ``options`` (dict, optional): Generation options

**Returns:**
- ``str``: Generated text

Examples
--------

.. code-block:: python

   from asabaal_utils.agents.spec_coder.ollama_client import OllamaClient
   
   client = OllamaClient()
   response = client.generate("Write a Python function", model="llama3")
   print(response)