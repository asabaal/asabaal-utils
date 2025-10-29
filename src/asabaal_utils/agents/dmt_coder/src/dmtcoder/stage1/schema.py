
from __future__ import annotations
from typing import List, Dict, Any

REQUIRED_TOP = ["spec", "version", "description", "functions"]

def _is_list(x): return isinstance(x, list)
def _is_dict(x): return isinstance(x, dict)
def _is_str(x): return isinstance(x, str) and x.strip() != ""

def validate_top(doc: Dict[str, Any]) -> List[str]:
    errs = []
    for k in REQUIRED_TOP:
        if k not in doc:
            errs.append(f"missing top-level key: {k}")
    if "functions" in doc and not _is_list(doc["functions"]):
        errs.append("functions must be a list")
    return errs

def validate_function(fn: Dict[str, Any], idx: int) -> List[str]:
    path = f"functions[{idx}]"
    req = ["id","name","signature","description","io","behavior","validation"]
    errs: List[str] = []
    for k in req:
        if k not in fn:
            errs.append(f"{path}: missing key: {k}")
    if "io" in fn:
        io = fn["io"]
        if not _is_dict(io): errs.append(f"{path}.io must be a mapping")
        else:
            if "inputs" not in io or not _is_list(io["inputs"]):
                errs.append(f"{path}.io.inputs must be a list")
            if "output" not in io or not _is_dict(io["output"]):
                errs.append(f"{path}.io.output must be a mapping")
            else:
                if "type" not in io["output"]:
                    errs.append(f"{path}.io.output.type missing")
            if "inputs" in io and _is_list(io["inputs"]):
                for j,inp in enumerate(io["inputs"]):
                    if not _is_dict(inp):
                        errs.append(f"{path}.io.inputs[{j}] must be a mapping")
                        continue
                    if "name" not in inp: errs.append(f"{path}.io.inputs[{j}].name missing")
                    if "type" not in inp: errs.append(f"{path}.io.inputs[{j}].type missing")
    if "behavior" in fn and not _is_list(fn["behavior"]):
        errs.append(f"{path}.behavior must be a list of steps")
    if "validation" in fn and not _is_list(fn["validation"]):
        errs.append(f"{path}.validation must be a list of rules")
    if "dmt" not in fn:
        errs.append(f"{path}: missing key: dmt")
    else:
        dmt = fn["dmt"]
        if not _is_dict(dmt): errs.append(f"{path}.dmt must be a mapping")
        elif "teach" not in dmt:
            errs.append(f"{path}.dmt.teach missing")
        else:
            teach = dmt["teach"]
            if not _is_dict(teach): errs.append(f"{path}.dmt.teach must be a mapping")
            elif "lessons" not in teach or not _is_list(teach["lessons"]) or len(teach["lessons"]) == 0:
                errs.append(f"{path}.dmt.teach.lessons must be a non-empty list")
            else:
                for k, lesson in enumerate(teach["lessons"]):
                    lpath = f"{path}.dmt.teach.lessons[{k}]"
                    if not _is_dict(lesson):
                        errs.append(f"{lpath} must be a mapping")
                        continue
                    if "name" not in lesson: errs.append(f"{lpath}.name missing")
                    demo = lesson.get("demo")
                    if not _is_dict(demo):
                        errs.append(f"{lpath}.demo missing or not a mapping")
                    else:
                        if "script" not in demo or not _is_str(demo["script"]):
                            errs.append(f"{lpath}.demo.script missing or empty")
                        expects = demo.get("expects")
                        if not _is_list(expects) or len(expects)==0:
                            errs.append(f"{lpath}.demo.expects must be a non-empty list")
    return errs

def validate_doc(doc: Dict[str, Any]) -> List[str]:
    errs = validate_top(doc)
    if errs: return errs
    for i, fn in enumerate(doc.get("functions", [])):
        if not isinstance(fn, dict):
            errs.append(f"functions[{i}] must be a mapping")
            continue
        errs.extend(validate_function(fn, i))
    return errs
