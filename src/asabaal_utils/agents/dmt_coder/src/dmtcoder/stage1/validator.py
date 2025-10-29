
from __future__ import annotations
from typing import Dict, Any, List
from .schema import validate_doc
from .model import ValidationReport

def validate_spec(doc: Dict[str, Any]) -> ValidationReport:
    messages: List[str] = []
    messages.extend(validate_doc(doc))

    for i, fn in enumerate(doc.get("functions", []) or []):
        path = f"functions[{i}]"
        name = fn.get("name","")
        sig_name = (fn.get("_derived") or {}).get("name_from_signature","")
        if name and sig_name and name != sig_name:
            messages.append(f"{path}.signature name '{sig_name}' does not match 'name' '{name}'")
        params = (fn.get("_derived") or {}).get("params_from_signature", [])
        io = fn.get("io", {})
        inps = [i.get('name') for i in io.get("inputs", []) if isinstance(i, dict)]
        for p in inps:
            if p and not any(p.split(':')[0].strip() == q.split(':')[0].strip() for q in params):
                messages.append(f"{path}.io.inputs contains '{p}' not present in signature params")
        for j, step in enumerate(fn.get("behavior", []) or []):
            if isinstance(step, dict):
                s = step.get("step","").strip()
            else:
                s = str(step).strip()
            if not s:
                messages.append(f"{path}.behavior[{j}] empty step")
        teach = (fn.get("dmt") or {}).get("teach") or {}
        seen_scripts = set()
        for k, lesson in enumerate(teach.get("lessons", []) or []):
            demo = (lesson or {}).get("demo") or {}
            script = demo.get("script")
            if script in seen_scripts:
                messages.append(f"{path}.dmt.teach.lessons[{k}].demo.script duplicate: {script}")
            if script: seen_scripts.add(script)
            expects = demo.get("expects") or []
            exp_paths = []
            for m, exp in enumerate(expects):
                if isinstance(exp, dict) and exp:
                    v = list(exp.values())[0]
                    if v in exp_paths:
                        messages.append(f"{path}.dmt.teach.lessons[{k}].demo.expects[{m}] duplicate path: {v}")
                    exp_paths.append(v)
    return ValidationReport(passed=(len(messages)==0), messages=messages)
