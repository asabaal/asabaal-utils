"""
Layout optimization algorithms for FlowScope graphs.

This module provides layout optimization algorithms for improving the
readability of function call graphs by minimizing edge crossings
and optimizing node positioning.
"""

from .graph_layout_optimizer import optimize_graph_layout

__all__ = ['optimize_graph_layout']