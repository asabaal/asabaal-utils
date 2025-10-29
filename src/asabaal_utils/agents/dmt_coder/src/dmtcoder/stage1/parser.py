
from __future__ import annotations
from typing import Any, Dict, Tuple, List
import yaml, pathlib, hashlib, datetime

def _sig_parts(signature: str) -> Tuple[str, str, str]:
    name = ""
    params = ""
    ret = ""
    if "(" in signature and ")" in signature:
        name = signature.split("(",1)[0].strip()
        params = signature.split("(",1)[1].rsplit(")",1)[0].strip()
    if "->" in signature:
        ret = signature.split("->",1)[1].strip()
    return name, params, ret

def load_spec(path: str) -> Dict[str, Any]:
    p = pathlib.Path(path)
    with p.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    data["_provenance"] = {
        "source_path": str(p.resolve()),
        "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
        "loaded_at_utc": datetime.datetime.utcnow().isoformat() + "Z",
    }
    for fn in data.get("functions", []) or []:
        sig = fn.get("signature","")
        sname, sparams, sret = _sig_parts(sig)
        fn.setdefault("_derived", {})
        fn["_derived"]["name_from_signature"] = sname
        fn["_derived"]["params_from_signature"] = [x.strip() for x in sparams.split(",")] if sparams else []
        fn["_derived"]["return_from_signature"] = sret
    return data
