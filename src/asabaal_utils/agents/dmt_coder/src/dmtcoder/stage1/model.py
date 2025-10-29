
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class ValidationReport:
    passed: bool
    messages: List[str] = field(default_factory=list)

@dataclass
class FunctionUnit:
    id: str
    name: str
    signature: str
    io: Dict[str, Any]
    behavior: List[Any]
    validation: List[Any]
    dmt: Dict[str, Any]

@dataclass
class PlanItem:
    kind: str
    path: str
    function_id: str | None = None
    function_name: str | None = None
    template_id: str | None = None
    notes: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Plan:
    spec_name: str
    version: str
    items: List[PlanItem] = field(default_factory=list)
