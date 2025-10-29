
from __future__ import annotations
from .parser import load_spec
from .validator import validate_spec
from .planner import build_plan
from .renderer import render_plan_to_disk
from .model import Plan, ValidationReport

class StageOneRunner:
    @staticmethod
    def check(spec_path: str) -> ValidationReport:
        doc = load_spec(spec_path)
        report = validate_spec(doc)
        return report

    @staticmethod
    def plan(spec_path: str) -> Plan:
        doc = load_spec(spec_path)
        report = validate_spec(doc)
        if not report.passed:
            raise ValueError("Spec failed validation:\n- " + "\n- ".join(report.messages))
        return build_plan(doc)

    @staticmethod
    def generate(spec_path: str, out_dir: str) -> Plan:
        plan = StageOneRunner.plan(spec_path)
        render_plan_to_disk(plan, out_dir)
        return plan
