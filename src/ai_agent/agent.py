"""
Main agent implementation for the AI Agent Framework.

This module provides the core Agent class that coordinates the autonomous operation
of AI agents, managing the cycle of analyzing, planning, implementing, and validating.
"""

import os
import time
import json
import logging
import asyncio
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Any, Callable

from .models.base import BaseModel
from .project import Project
from .monitoring import CostMonitor
from .tools.code import CodeGenerator, UnitTestGenerator
from .tools.validation import CodeValidator, TestRunner


class TaskType(Enum):
    """Types of tasks that the agent can perform."""
    ANALYZE = auto()
    PLAN = auto()
    IMPLEMENT = auto()
    VALIDATE = auto()
    DOCUMENT = auto()


class Agent:
    """The main agent class for autonomous AI operation.
    
    This class coordinates the autonomous operation of an AI agent,
    managing the cycle of analyzing, planning, implementing, and validating.
    """
    
    def __init__(
        self,
        model: BaseModel,
        project: Project,
        budget: float = 10.0,
        session_dir: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the agent.
        
        Args:
            model: The LLM to use for the agent
            project: The project to work on
            budget: Maximum budget in USD
            session_dir: Directory to save session data
            config: Additional configuration options
        """
        self.model = model
        self.project = project
        self.budget = budget
        
        # Set up session directory
        if session_dir:
            self.session_dir = Path(session_dir)
            self.session_dir.mkdir(parents=True, exist_ok=True)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.session_dir = Path(f"agent_sessions/{timestamp}")
            self.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize the cost monitor
        self.cost_monitor = CostMonitor(self.session_dir)
        
        # Set up tools
        self.code_generator = CodeGenerator(model)
        self.test_generator = UnitTestGenerator(model)
        self.code_validator = CodeValidator(model)
        self.test_runner = TestRunner()
        
        # Initialize state
        self.current_task = None
        self.task_history = []
        self.is_running = False
        self.start_time = None
        self.last_task_time = None
        
        # Configuration
        self.config = {
            "max_consecutive_failures": 3,
            "task_timeout_seconds": 300,
            "sleep_between_tasks_seconds": 2,
            "verbose_logging": True,
            "auto_commit": True,
            "max_iterations": 100,
        }
        
        # Update with user config if provided
        if config:
            self.config.update(config)
        
        # Set up logging
        log_level = logging.DEBUG if self.config["verbose_logging"] else logging.INFO
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(self.session_dir / "agent.log"),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger("AIAgent")
        self.logger.info(f"Agent initialized with model: {model.name}")
        self.logger.info(f"Project: {project.path}")
        self.logger.info(f"Budget: ${budget:.2f}")
    
    async def run(
        self,
        max_runtime_hours: float = 1.0,
        goal_description: Optional[str] = None,
        callback: Optional[Callable[[Dict], None]] = None,
    ) -> Dict[str, Any]:
        """Run the agent autonomously.
        
        Args:
            max_runtime_hours: Maximum runtime in hours
            goal_description: Optional description of the project goal
            callback: Optional callback function for progress updates
            
        Returns:
            Dictionary containing results and statistics
        """
        self.is_running = True
        self.start_time = time.time()
        max_runtime_seconds = max_runtime_hours * 3600
        iteration_count = 0
        consecutive_failures = 0
        
        self.logger.info(f"Starting agent run with max runtime of {max_runtime_hours} hours")
        if goal_description:
            self.logger.info(f"Goal: {goal_description}")
        
        try:
            while self.is_running:
                # Check if we've exceeded max runtime
                elapsed_seconds = time.time() - self.start_time
                if elapsed_seconds >= max_runtime_seconds:
                    self.logger.info(f"Maximum runtime of {max_runtime_hours} hours reached")
                    break
                
                # Check if we've exceeded max iterations
                iteration_count += 1
                if iteration_count > self.config["max_iterations"]:
                    self.logger.info(f"Maximum iterations ({self.config['max_iterations']}) reached")
                    break
                
                # Check if we're still under budget
                cost, remaining, under_budget = self.cost_monitor.get_budget_status(self.budget)
                if not under_budget:
                    self.logger.warning(f"Budget limit of ${self.budget:.2f} exceeded")
                    break
                
                self.logger.info(f"Iteration {iteration_count} | Elapsed: {elapsed_seconds:.1f}s | " +
                               f"Cost: ${cost:.4f} | Remaining: ${remaining:.4f}")
                
                # Run a single iteration of the agent loop
                success, result = await self._run_iteration(goal_description)
                
                # Track consecutive failures
                if success:
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1
                    self.logger.warning(f"Iteration failed. Consecutive failures: {consecutive_failures}")
                    
                    if consecutive_failures >= self.config["max_consecutive_failures"]:
                        self.logger.error(f"Too many consecutive failures ({consecutive_failures}). Stopping.")
                        break
                
                # Call the callback if provided
                if callback:
                    callback_data = {
                        "iteration": iteration_count,
                        "elapsed_seconds": elapsed_seconds,
                        "cost": cost,
                        "remaining_budget": remaining,
                        "success": success,
                        "result": result
                    }
                    callback(callback_data)
                
                # Sleep between iterations
                await asyncio.sleep(self.config["sleep_between_tasks_seconds"])
        
        except Exception as e:
            self.logger.error(f"Agent run failed with error: {e}", exc_info=True)
        
        finally:
            self.is_running = False
            
            # End monitoring session and get final stats
            stats = self.cost_monitor.end_session()
            
            # Save run summary
            summary = {
                "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
                "end_time": datetime.fromtimestamp(time.time()).isoformat(),
                "duration_hours": (time.time() - self.start_time) / 3600,
                "iterations": iteration_count,
                "goal": goal_description,
                "model": self.model.name,
                "total_cost": stats.total_cost,
                "budget": self.budget,
                "remaining_budget": self.budget - stats.total_cost,
                "task_history": self.task_history,
            }
            
            summary_path = self.session_dir / "run_summary.json"
            with open(summary_path, "w") as f:
                json.dump(summary, f, indent=2)
            
            self.logger.info(f"Agent run completed. Summary saved to {summary_path}")
            return summary
    
    async def _run_iteration(self, goal_description: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
        """Run a single iteration of the agent loop.
        
        An iteration consists of:
        1. Analyzing the current project state
        2. Planning the next steps
        3. Implementing the planned changes
        4. Validating the implementation
        
        Args:
            goal_description: Optional description of the project goal
            
        Returns:
            Tuple of (success, result_dict)
        """
        result = {}
        
        try:
            # Step 1: Analyze the current project state
            analysis = await self._analyze_project(goal_description)
            result["analysis"] = analysis
            
            # Step 2: Plan the next steps based on the analysis
            plan = await self._plan_next_steps(analysis, goal_description)
            result["plan"] = plan
            
            # If there's nothing to do, we're done
            if plan.get("is_complete", False):
                self.logger.info("Project is complete according to the plan")
                return True, result
            
            # Step 3: Implement the planned changes
            implementation = await self._implement_changes(plan)
            result["implementation"] = implementation
            
            # Step 4: Validate the implementation
            validation = await self._validate_changes(implementation)
            result["validation"] = validation
            
            # Determine overall success based on validation
            success = validation.get("success", False)
            
            # If implementation succeeded, perform additional steps
            if success:
                # Generate documentation if needed
                if plan.get("needs_documentation", False):
                    documentation = await self._generate_documentation(implementation)
                    result["documentation"] = documentation
                
                # Commit changes if auto_commit is enabled
                if self.config["auto_commit"] and implementation.get("files_changed", []):
                    # This would integrate with git in a real implementation
                    self.logger.info("Changes would be committed here if integrated with git")
            
            return success, result
            
        except Exception as e:
            self.logger.error(f"Iteration failed with error: {e}", exc_info=True)
            return False, {"error": str(e)}
    
    async def _analyze_project(self, goal_description: Optional[str] = None) -> Dict[str, Any]:
        """Analyze the current project state.
        
        Args:
            goal_description: Optional description of the project goal
            
        Returns:
            Analysis results
        """
        self.logger.info("Starting project analysis...")
        self.current_task = TaskType.ANALYZE
        
        # Scan the project to get updated state
        self.project.scan()
        
        # Build context for the model
        context = self.project.build_context(include_all_changed=True)
        
        # Create the prompt for analysis
        prompt_parts = [
            "# Project Analysis Task",
            "Analyze the current state of the project and identify what needs to be done next.",
            "\n## Project Context",
            context
        ]
        
        if goal_description:
            prompt_parts.extend([
                "\n## Project Goal",
                goal_description
            ])
        
        prompt_parts.extend([
            "\n## Instructions",
            "1. Analyze the current state of the project",
            "2. Identify what components or features need to be implemented or improved",
            "3. Identify any issues, bugs, or areas that need attention",
            "4. Provide a high-level assessment of project progress",
            "\nReturn your analysis in JSON format with the following structure:",
            "```json",
            "{",
            '  "project_state": "brief description of current state",',
            '  "components": ["list of main components/modules"],',
            '  "implemented_features": ["list of implemented features"],',
            '  "missing_features": ["list of features that should be implemented"],',
            '  "issues": ["list of issues or bugs found"],',
            '  "progress_percent": 0-100,',
            '  "next_steps": ["list of recommended next steps in priority order"]',
            "}",
            "```"
        ])
        
        prompt = "\n".join(prompt_parts)
        
        # Set up system prompt
        system_prompt = (
            "You are an expert software developer and architect performing project analysis. "
            "Analyze the provided project files and context to understand the current state and structure. "
            "Provide a detailed analysis focusing on what exists, what's missing, and what needs improvement. "
            "Be specific and actionable in your recommendations."
        )
        
        # Track the start time for latency measurement
        start_time = time.time()
        
        # Generate the analysis
        response = await self.model.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.2,
        )
        
        # Record the usage
        latency_ms = (time.time() - start_time) * 1000
        self.cost_monitor.record_usage(
            usage=response.usage,
            model_name=self.model.name,
            latency_ms=latency_ms,
            task_type="analyze",
        )
        
        # Extract the JSON result
        try:
            # Find JSON in the response
            import re
            json_match = re.search(r"{.*}", response.content, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group(0))
            else:
                # Fallback if no JSON format is found
                analysis = {
                    "project_state": "Unknown",
                    "error": "Failed to extract JSON from response",
                    "raw_response": response.content
                }
        except json.JSONDecodeError:
            analysis = {
                "project_state": "Unknown",
                "error": "Invalid JSON format in response",
                "raw_response": response.content
            }
        
        # Log the analysis
        self.logger.info(f"Analysis complete. Project at {analysis.get('progress_percent', 0)}% completion")
        self.logger.debug(f"Analysis details: {analysis}")
        
        # Save the task to history
        self.task_history.append({
            "task_type": "analyze",
            "timestamp": datetime.now().isoformat(),
            "result": analysis
        })
        
        self.current_task = None
        return analysis
    
    async def _plan_next_steps(
        self,
        analysis: Dict[str, Any],
        goal_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Plan the next steps based on the analysis.
        
        Args:
            analysis: Analysis results from _analyze_project
            goal_description: Optional description of the project goal
            
        Returns:
            Plan details
        """
        self.logger.info("Planning next steps...")
        self.current_task = TaskType.PLAN
        
        # Check if the project is already complete
        if analysis.get("progress_percent", 0) >= 100 and not analysis.get("missing_features") and not analysis.get("issues"):
            return {
                "is_complete": True,
                "message": "Project is complete. No further action needed."
            }
        
        # Create the prompt for planning
        prompt_parts = [
            "# Project Planning Task",
            "Based on the project analysis, create a detailed plan for the next implementation steps.",
            "\n## Project Analysis",
            json.dumps(analysis, indent=2)
        ]
        
        if goal_description:
            prompt_parts.extend([
                "\n## Project Goal",
                goal_description
            ])
        
        prompt_parts.extend([
            "\n## Instructions",
            "1. Identify the highest priority task to implement next",
            "2. Create a detailed plan for implementing this task",
            "3. Specify what files need to be created or modified",
            "4. Provide specific implementation details",
            "\nReturn your plan in JSON format with the following structure:",
            "```json",
            "{",
            '  "priority_task": "description of the highest priority task",',
            '  "task_type": "feature|bugfix|refactor|test|documentation",',
            '  "files_to_modify": ["list of files to modify"],',
            '  "files_to_create": ["list of files to create"],',
            '  "implementation_details": "detailed description of what to implement",',
            '  "acceptance_criteria": ["list of criteria to determine if task is complete"],',
            '  "needs_documentation": true|false,',
            '  "estimated_complexity": 1-10',
            "}",
            "```"
        ])
        
        prompt = "\n".join(prompt_parts)
        
        # Set up system prompt
        system_prompt = (
            "You are an expert software developer and project manager creating implementation plans. "
            "Based on the project analysis, determine the highest priority task and create a detailed plan. "
            "Focus on one specific task rather than trying to solve everything at once. "
            "Be specific about what needs to be implemented and how to verify it's correct."
        )
        
        # Track the start time for latency measurement
        start_time = time.time()
        
        # Generate the plan
        response = await self.model.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,
        )
        
        # Record the usage
        latency_ms = (time.time() - start_time) * 1000
        self.cost_monitor.record_usage(
            usage=response.usage,
            model_name=self.model.name,
            latency_ms=latency_ms,
            task_type="plan",
        )
        
        # Extract the JSON result
        try:
            # Find JSON in the response
            import re
            json_match = re.search(r"{.*}", response.content, re.DOTALL)
            if json_match:
                plan = json.loads(json_match.group(0))
            else:
                # Fallback if no JSON format is found
                plan = {
                    "priority_task": "Unknown",
                    "error": "Failed to extract JSON from response",
                    "raw_response": response.content
                }
        except json.JSONDecodeError:
            plan = {
                "priority_task": "Unknown",
                "error": "Invalid JSON format in response",
                "raw_response": response.content
            }
        
        # Log the plan
        self.logger.info(f"Planning complete. Priority task: {plan.get('priority_task', 'Unknown')}")
        self.logger.debug(f"Plan details: {plan}")
        
        # Save the task to history
        self.task_history.append({
            "task_type": "plan",
            "timestamp": datetime.now().isoformat(),
            "result": plan
        })
        
        self.current_task = None
        return plan
    
    async def _implement_changes(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Implement the changes according to the plan.
        
        Args:
            plan: Plan details from _plan_next_steps
            
        Returns:
            Implementation details
        """
        self.logger.info(f"Implementing changes: {plan.get('priority_task', 'Unknown task')}")
        self.current_task = TaskType.IMPLEMENT
        
        implementation_results = {
            "task": plan.get("priority_task", "Unknown"),
            "success": False,
            "files_changed": [],
            "new_files": [],
            "errors": []
        }
        
        # Handle different task types
        task_type = plan.get("task_type", "").lower()
        
        try:
            # First, process files to modify
            for file_path in plan.get("files_to_modify", []):
                try:
                    # Get the current content of the file
                    file_state = self.project.get_file(file_path)
                    
                    if file_state:
                        existing_code = file_state.content
                        language = self._detect_language(file_path)
                        
                        # Generate the implementation
                        if task_type == "bugfix":
                            new_code = await self.code_generator.fix_bug(
                                bug_description=plan.get("implementation_details", ""),
                                problematic_code=existing_code,
                                language=language,
                                file_path=file_path
                            )
                        elif task_type == "refactor":
                            new_code = await self.code_generator.refactor_code(
                                existing_code=existing_code,
                                refactoring_goal=plan.get("implementation_details", ""),
                                language=language,
                                file_path=file_path
                            )
                        else:  # feature or other
                            new_code = await self.code_generator.implement_feature(
                                feature_description=plan.get("implementation_details", ""),
                                existing_code=existing_code,
                                language=language,
                                file_path=file_path
                            )
                        
                        # Save the modified file
                        self.project.save_file(file_path, new_code)
                        implementation_results["files_changed"].append(file_path)
                    else:
                        error_msg = f"File not found: {file_path}"
                        self.logger.error(error_msg)
                        implementation_results["errors"].append(error_msg)
                
                except Exception as e:
                    error_msg = f"Error modifying file {file_path}: {str(e)}"
                    self.logger.error(error_msg)
                    implementation_results["errors"].append(error_msg)
            
            # Then, process files to create
            for file_path in plan.get("files_to_create", []):
                try:
                    # Check if file already exists
                    file_state = self.project.get_file(file_path)
                    
                    if file_state:
                        warning_msg = f"File already exists: {file_path}, will be modified instead"
                        self.logger.warning(warning_msg)
                    
                    language = self._detect_language(file_path)
                    
                    # Generate new code
                    new_code = await self.code_generator.implement_feature(
                        feature_description=plan.get("implementation_details", ""),
                        language=language,
                        file_path=file_path
                    )
                    
                    # Save the new file
                    self.project.save_file(file_path, new_code)
                    implementation_results["new_files"].append(file_path)
                
                except Exception as e:
                    error_msg = f"Error creating file {file_path}: {str(e)}"
                    self.logger.error(error_msg)
                    implementation_results["errors"].append(error_msg)
            
            # Mark as successful if no errors occurred
            if not implementation_results["errors"]:
                implementation_results["success"] = True
        
        except Exception as e:
            error_msg = f"Implementation failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            implementation_results["errors"].append(error_msg)
        
        # Log the implementation results
        if implementation_results["success"]:
            self.logger.info(f"Implementation successful. Changed {len(implementation_results['files_changed'])} files, " +
                           f"created {len(implementation_results['new_files'])} files.")
        else:
            self.logger.error(f"Implementation failed with {len(implementation_results['errors'])} errors.")
        
        # Save the task to history
        self.task_history.append({
            "task_type": "implement",
            "timestamp": datetime.now().isoformat(),
            "result": implementation_results
        })
        
        self.current_task = None
        return implementation_results
    
    async def _validate_changes(self, implementation: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the implemented changes.
        
        Args:
            implementation: Implementation details from _implement_changes
            
        Returns:
            Validation results
        """
        self.logger.info("Validating changes...")
        self.current_task = TaskType.VALIDATE
        
        validation_results = {
            "task": implementation.get("task", "Unknown"),
            "success": False,
            "validation_details": [],
            "test_results": [],
            "errors": []
        }
        
        if not implementation.get("success", False):
            error_msg = "Skipping validation as implementation was not successful"
            self.logger.warning(error_msg)
            validation_results["errors"].append(error_msg)
            return validation_results
        
        try:
            # Re-scan the project to get fresh state
            self.project.scan()
            
            # Validate each changed file
            for file_path in implementation["files_changed"] + implementation["new_files"]:
                try:
                    file_state = self.project.get_file(file_path)
                    
                    if not file_state:
                        error_msg = f"File not found for validation: {file_path}"
                        self.logger.error(error_msg)
                        validation_results["errors"].append(error_msg)
                        continue
                    
                    # Detect language and validate accordingly
                    language = self._detect_language(file_path)
                    
                    if language == "python":
                        validation = await self.code_validator.validate_python(file_state.content)
                    elif language == "javascript":
                        validation = await self.code_validator.validate_javascript(file_state.content)
                    else:
                        # Basic syntax check for unsupported languages
                        validation = ValidationResult(
                            is_valid=True,
                            errors=[],
                            warnings=[f"No specific validation available for {language}"],
                            suggestions=[],
                            metrics={"total_lines": len(file_state.content.split('\n'))}
                        )
                    
                    # Record validation results
                    validation_details = {
                        "file": file_path,
                        "is_valid": validation.is_valid,
                        "errors": validation.errors,
                        "warnings": validation.warnings,
                        "suggestions": validation.suggestions,
                        "metrics": validation.metrics
                    }
                    
                    validation_results["validation_details"].append(validation_details)
                    
                    # If any file is invalid, the overall validation is invalid
                    if not validation.is_valid:
                        validation_results["success"] = False
                        self.logger.warning(f"Validation failed for {file_path}: {validation.errors}")
                
                except Exception as e:
                    error_msg = f"Error validating file {file_path}: {str(e)}"
                    self.logger.error(error_msg)
                    validation_results["errors"].append(error_msg)
            
            # If we have Python files, we should generate and run tests
            python_files = [f for f in implementation["files_changed"] + implementation["new_files"] 
                           if f.endswith(".py") and not f.startswith("test_")]
            
            if python_files:
                for file_path in python_files:
                    try:
                        file_state = self.project.get_file(file_path)
                        
                        if not file_state:
                            continue
                        
                        # Generate tests
                        test_code = await self.test_generator.generate_unit_tests(
                            code_to_test=file_state.content,
                            language="python",
                            test_framework="pytest",
                            file_path=file_path
                        )
                        
                        # Save the test file
                        test_file_path = os.path.join(os.path.dirname(file_path), f"test_{os.path.basename(file_path)}")
                        self.project.save_file(test_file_path, test_code)
                        
                        # Run the tests
                        test_result = self.test_runner.run_python_tests(
                            code=file_state.content,
                            test_code=test_code,
                            test_framework="pytest"
                        )
                        
                        # Record test results
                        test_details = {
                            "file": file_path,
                            "test_file": test_file_path,
                            "success": test_result.success,
                            "passing_tests": test_result.passing_tests,
                            "failing_tests": test_result.failing_tests,
                            "error_messages": test_result.error_messages
                        }
                        
                        validation_results["test_results"].append(test_details)
                        
                        # Log test results
                        if test_result.success:
                            self.logger.info(f"Tests passed for {file_path}: {test_result.passing_tests} tests passed")
                        else:
                            self.logger.warning(f"Tests failed for {file_path}: {test_result.failing_tests} tests failed")
                    
                    except Exception as e:
                        error_msg = f"Error testing file {file_path}: {str(e)}"
                        self.logger.error(error_msg)
                        validation_results["errors"].append(error_msg)
            
            # Determine overall success
            if len(validation_results["errors"]) == 0:
                # Check if any validations failed
                validation_failures = any(not detail["is_valid"] for detail in validation_results["validation_details"])
                
                # Check if any tests failed
                test_failures = any(not result["success"] for result in validation_results["test_results"])
                
                validation_results["success"] = not validation_failures and not test_failures
        
        except Exception as e:
            error_msg = f"Validation failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            validation_results["errors"].append(error_msg)
        
        # Log the validation results
        if validation_results["success"]:
            self.logger.info("Validation successful.")
        else:
            self.logger.warning("Validation failed.")
        
        # Save the task to history
        self.task_history.append({
            "task_type": "validate",
            "timestamp": datetime.now().isoformat(),
            "result": validation_results
        })
        
        self.current_task = None
        return validation_results
    
    async def _generate_documentation(self, implementation: Dict[str, Any]) -> Dict[str, Any]:
        """Generate documentation for the implemented changes.
        
        Args:
            implementation: Implementation details from _implement_changes
            
        Returns:
            Documentation generation results
        """
        self.logger.info("Generating documentation...")
        self.current_task = TaskType.DOCUMENT
        
        documentation_results = {
            "task": implementation.get("task", "Unknown"),
            "success": False,
            "files_documented": [],
            "errors": []
        }
        
        # Implement documentation generation logic here
        # For now, this is a stub
        
        self.current_task = None
        return documentation_results
    
    def _detect_language(self, file_path: str) -> str:
        """Detect the programming language based on file extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Programming language name
        """
        extension = os.path.splitext(file_path)[1].lower()
        
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "cpp",
            ".cs": "csharp",
            ".go": "go",
            ".rb": "ruby",
            ".php": "php",
            ".swift": "swift",
            ".kt": "kotlin",
            ".rs": "rust",
            ".html": "html",
            ".css": "css",
            ".json": "json",
            ".xml": "xml",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".md": "markdown",
            ".sh": "bash",
        }
        
        return language_map.get(extension, "text")
    
    def stop(self) -> None:
        """Stop the agent's execution."""
        if self.is_running:
            self.logger.info("Stopping agent execution...")
            self.is_running = False
