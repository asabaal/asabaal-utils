"""
spec_coder - OpenSpec-driven autonomous coding agent

This agent can autonomously:
- Parse OpenSpec specifications
- Generate structured code
- Test and validate it
- Self-patch errors
- Reorganize finalized modules
"""

from .orchestrator import IntegrationOrchestrator as Orchestrator
from .generator import CodeGenerator as Generator
from .tester import TestAnalyzer as Tester
from .healer import FailurePatcher as Healer
from .organizer import CodeOrganizer as Organizer

__all__ = ['Orchestrator', 'Generator', 'Tester', 'Healer', 'Organizer']