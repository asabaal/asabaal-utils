"""
Code generation tools for the AI Agent Framework.

This module provides tools for generating code, including implementing features,
refactoring existing code, and creating tests.
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any

from ..models.base import BaseModel, ModelResponse


@dataclass
class CodeBlock:
    """Represents a block of code extracted from a model response."""
    language: str
    code: str
    starting_line: int
    ending_line: int


class CodeGenerator:
    """Tool for generating code using LLMs.
    
    This class provides methods for generating various types of code,
    including implementing features, fixing bugs, and refactoring.
    """
    
    def __init__(self, model: BaseModel):
        """Initialize the code generator.
        
        Args:
            model: The model to use for code generation
        """
        self.model = model
    
    async def implement_feature(
        self, 
        feature_description: str,
        existing_code: Optional[str] = None,
        language: str = "python",
        file_path: Optional[str] = None,
    ) -> str:
        """Generate code to implement a new feature.
        
        Args:
            feature_description: Description of the feature to implement
            existing_code: Optional existing code to extend
            language: Programming language to generate code in
            file_path: Optional path to the file being modified
            
        Returns:
            Generated code for the feature
        """
        context_parts = []
        
        # Add file path information if available
        if file_path:
            context_parts.append(f"File: {file_path}")
        
        # Add existing code if available
        if existing_code:
            context_parts.append(f"Existing code:\n```{language}\n{existing_code}\n```")
        
        # Construct the prompt
        prompt = (
            f"Generate {language} code to implement the following feature:\n\n"
            f"{feature_description}\n\n"
        )
        
        if context_parts:
            prompt += "Context:\n" + "\n".join(context_parts) + "\n\n"
        
        prompt += (
            f"Please provide only the code implementation without explanations. "
            f"The code should be well-structured, idiomatic {language}, with appropriate "
            f"comments and error handling."
        )
        
        # Set up the system prompt
        system_prompt = (
            f"You are an expert {language} developer. Your task is to write high-quality "
            f"code to implement features as requested. Follow best practices for {language} "
            f"including proper error handling, documentation, and testing. Use modern, "
            f"idiomatic {language} code style."
        )
        
        # Generate the code
        response = await self.model.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.2,  # Lower temperature for more deterministic code
        )
        
        # Extract the code blocks from the response
        code_blocks = self._extract_code_blocks(response.content, language)
        
        # If no code blocks were found, return the whole response
        if not code_blocks:
            return response.content
        
        # Otherwise, return just the code
        return code_blocks[0].code
    
    async def fix_bug(
        self,
        bug_description: str,
        problematic_code: str,
        error_message: Optional[str] = None,
        language: str = "python",
        file_path: Optional[str] = None,
    ) -> str:
        """Generate code to fix a bug in existing code.
        
        Args:
            bug_description: Description of the bug to fix
            problematic_code: The code containing the bug
            error_message: Optional error message or stack trace
            language: Programming language of the code
            file_path: Optional path to the file being fixed
            
        Returns:
            Fixed code
        """
        context_parts = []
        
        # Add file path information if available
        if file_path:
            context_parts.append(f"File: {file_path}")
        
        # Add error message if available
        if error_message:
            context_parts.append(f"Error:\n{error_message}")
        
        # Construct the prompt
        prompt = (
            f"Fix the following {language} code that has a bug:\n\n"
            f"```{language}\n{problematic_code}\n```\n\n"
            f"Bug description: {bug_description}\n\n"
        )
        
        if context_parts:
            prompt += "Context:\n" + "\n".join(context_parts) + "\n\n"
        
        prompt += (
            f"Please provide only the fixed code without explanations. "
            f"The code should maintain the same structure and style as the original "
            f"when possible, only changing what's necessary to fix the bug."
        )
        
        # Set up the system prompt
        system_prompt = (
            f"You are an expert {language} developer specializing in debugging. "
            f"Your task is to identify and fix bugs in {language} code while making "
            f"minimal changes to preserve the original code structure and style."
        )
        
        # Generate the fixed code
        response = await self.model.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.1,  # Even lower temperature for more deterministic fixes
        )
        
        # Extract the code blocks from the response
        code_blocks = self._extract_code_blocks(response.content, language)
        
        # If no code blocks were found, return the whole response
        if not code_blocks:
            return response.content
        
        # Otherwise, return just the code
        return code_blocks[0].code
    
    async def refactor_code(
        self,
        existing_code: str,
        refactoring_goal: str,
        language: str = "python",
        file_path: Optional[str] = None,
    ) -> str:
        """Generate refactored code based on existing code.
        
        Args:
            existing_code: Code to be refactored
            refactoring_goal: Description of the refactoring goal
            language: Programming language of the code
            file_path: Optional path to the file being refactored
            
        Returns:
            Refactored code
        """
        context_parts = []
        
        # Add file path information if available
        if file_path:
            context_parts.append(f"File: {file_path}")
        
        # Construct the prompt
        prompt = (
            f"Refactor the following {language} code according to this goal:\n\n"
            f"Refactoring goal: {refactoring_goal}\n\n"
            f"Original code:\n```{language}\n{existing_code}\n```\n\n"
        )
        
        if context_parts:
            prompt += "Context:\n" + "\n".join(context_parts) + "\n\n"
        
        prompt += (
            f"Please provide only the refactored code without explanations. "
            f"The code should maintain the same functionality as the original "
            f"while improving its structure, readability, or performance based on "
            f"the refactoring goal."
        )
        
        # Set up the system prompt
        system_prompt = (
            f"You are an expert {language} developer specializing in refactoring. "
            f"Your task is to improve code quality while preserving functionality. "
            f"Apply best practices and design patterns appropriate for {language}."
        )
        
        # Generate the refactored code
        response = await self.model.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,  # Moderate temperature for creativity in refactoring
        )
        
        # Extract the code blocks from the response
        code_blocks = self._extract_code_blocks(response.content, language)
        
        # If no code blocks were found, return the whole response
        if not code_blocks:
            return response.content
        
        # Otherwise, return just the code
        return code_blocks[0].code
    
    def _extract_code_blocks(self, text: str, preferred_language: Optional[str] = None) -> List[CodeBlock]:
        """Extract code blocks from a text string.
        
        Args:
            text: Text containing code blocks
            preferred_language: If specified, prioritize blocks in this language
            
        Returns:
            List of CodeBlock objects
        """
        # Pattern to match code blocks with language specifier (```python)
        # or without (```)
        pattern = r"```(?P<language>\w*)\n(?P<code>[\s\S]*?)```"
        matches = re.finditer(pattern, text)
        
        code_blocks = []
        line_count = 1
        
        for match in matches:
            language = match.group("language").strip().lower() or "text"
            code = match.group("code").strip()
            
            # Calculate line numbers
            text_before_match = text[:match.start()]
            starting_line = line_count + text_before_match.count("\n")
            ending_line = starting_line + code.count("\n") + 1
            line_count = ending_line
            
            code_blocks.append(
                CodeBlock(
                    language=language,
                    code=code,
                    starting_line=starting_line,
                    ending_line=ending_line,
                )
            )
        
        # If a preferred language is specified and multiple blocks exist,
        # prioritize blocks in that language
        if preferred_language and code_blocks:
            preferred_blocks = [b for b in code_blocks if b.language.lower() == preferred_language.lower()]
            if preferred_blocks:
                return preferred_blocks
        
        return code_blocks


class UnitTestGenerator:
    """Tool for generating unit tests for code.
    
    This class provides methods for generating different types of tests
    for existing code.
    """
    
    def __init__(self, model: BaseModel):
        """Initialize the test generator.
        
        Args:
            model: The model to use for test generation
        """
        self.model = model
    
    async def generate_unit_tests(
        self,
        code_to_test: str,
        language: str = "python",
        test_framework: Optional[str] = None,
        file_path: Optional[str] = None,
    ) -> str:
        """Generate unit tests for the given code.
        
        Args:
            code_to_test: Code to generate tests for
            language: Programming language of the code
            test_framework: Specific test framework to use (e.g., pytest, jest)
            file_path: Optional path to the file being tested
            
        Returns:
            Generated unit tests
        """
        context_parts = []
        
        # Add file path information if available
        if file_path:
            context_parts.append(f"File to test: {file_path}")
        
        # Choose appropriate test framework if not specified
        if not test_framework:
            if language.lower() == "python":
                test_framework = "pytest"
            elif language.lower() in ["javascript", "typescript"]:
                test_framework = "jest"
            elif language.lower() == "java":
                test_framework = "junit"
            else:
                test_framework = "a standard testing framework"
        
        # Construct the prompt
        prompt = (
            f"Generate unit tests using {test_framework} for the following {language} code:\n\n"
            f"```{language}\n{code_to_test}\n```\n\n"
        )
        
        if context_parts:
            prompt += "Context:\n" + "\n".join(context_parts) + "\n\n"
        
        prompt += (
            f"Please provide only the test code without explanations. "
            f"The tests should be comprehensive, covering edge cases and various scenarios. "
            f"Include appropriate assertions and follow best practices for {test_framework}."
        )
        
        # Set up the system prompt
        system_prompt = (
            f"You are an expert in testing {language} code using {test_framework}. "
            f"Your task is to write comprehensive unit tests that validate functionality "
            f"and catch potential edge cases. Follow best practices for {test_framework}."
        )
        
        # Generate the tests
        response = await self.model.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.2,
        )
        
        # Extract the code blocks from the response
        code_generator = CodeGenerator(self.model)
        code_blocks = code_generator._extract_code_blocks(response.content, language)
        
        # If no code blocks were found, return the whole response
        if not code_blocks:
            return response.content
        
        # Otherwise, return just the code
        return code_blocks[0].code
