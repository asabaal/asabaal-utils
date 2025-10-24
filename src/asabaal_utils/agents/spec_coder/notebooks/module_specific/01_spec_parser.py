# %% [markdown]
# # SpecCoder Educational Notebook 01 — Understanding the SpecParser
# *Learn how the SpecParser module transforms OpenSpec YAML into structured Python dataclasses.*
#
# **What you'll learn**
# - How the SpecParser loads YAML and produces typed Python dataclasses (OpenSpec, Requirement, etc.).
# - The purpose of key methods: `parse_file`, `parse_string`, `_parse_data`, `_parse_requirement`, `validate_spec`.
# - How to run the parser on a real spec (we'll use `rhythmic_pulse_generator.yml`) and inspect results.
# - How to format requirements and function signatures for downstream prompts.
#
# **Educational approach – DONE MEANS TAUGHT**
# We alternate: *Explain → Show real source → Run a concrete example*.
#
# > Note: In your repo, prefer the full package import path per the Notebook Development Guide.
# > Here we include a small fallback so this tutorial can execute standalone if the package path isn't available.

# %%
from pathlib import Path
import sys
import inspect
from textwrap import indent

# --- Repo-root resolution (preferred pattern in your repo) ---
current_dir = Path(__file__).parent if '__file__' in globals() else Path.cwd()
repo_root = current_dir.parent.parent.parent.parent  # adjust if storing under notebooks/
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# --- Preferred import: package path ---
# In your repo, this should succeed:
try:
    from asabaal_utils.agents.spec_coder.spec_parser import SpecParser
    USING_PACKAGE_IMPORT = True
except Exception:
    # Fallback for standalone execution in this environment only
    USING_PACKAGE_IMPORT = False
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    # Local module fallback
    from spec_parser import SpecParser  # noqa: E402

print("Using package import:", USING_PACKAGE_IMPORT)

# %% [markdown]
# ## Phase 1. Conceptual overview
# The SpecParser converts **OpenSpec-style YAML** into structured Python objects:
#
# - **OpenSpec**: overall metadata and a list of **Requirement** items.
# - **Requirement**: id, title, description, optional interface and validation.
# - **ValidationCriteria**: type, file, target of tests.
# - **FunctionInterface**: function name, parameters, returns, and optional example.
#
# We will parse a real file: `rhythmic_pulse_generator.yml`.
# This spec lists high-level requirements (generate pulse, apply envelope, export audio)
# and a separate `interfaces` block that describes a class API.

# %% [markdown]
# ## Phase 2. Code walkthrough (selected methods)
# We'll peek at key methods directly from the loaded class and annotate what they do.

# %%
def show_source(obj, header: str):
    print(f"### {header}\n")
    try:
        src = inspect.getsource(obj)
        print(src)
    except OSError:
        print("Source unavailable (possibly C-accelerated or dynamically defined).")

show_source(SpecParser.__init__, "SpecParser.__init__")

# %%
show_source(SpecParser.parse_file, "SpecParser.parse_file")

# %%
show_source(SpecParser.parse_string, "SpecParser.parse_string")

# %%
show_source(SpecParser._parse_data, "SpecParser._parse_data")

# %%
show_source(SpecParser._parse_requirement, "SpecParser._parse_requirement")

# %%
show_source(SpecParser.validate_spec, "SpecParser.validate_spec")

# %% [markdown]
# **Notes:**
# - `_parse_data` extracts top-level fields `name/spec_id`, `title/description`, `version`,
#   then iterates over `requirements` to build `Requirement` instances.
# - `_parse_requirement` pulls id/title/description and optionally parses `interface` and `validation` fields
#   **when those are provided inside each requirement**.
# - If your spec declares `interfaces` at the top level (separate from each requirement),
#   the current parser will not automatically attach those to requirements — it expects per-requirement `interface` data.
#
# We'll see the effect of that in the live demo.

# %% [markdown]
# ## Phase 3. Practical demonstration with your YAML
# Let's parse `/mnt/data/rhythmic_pulse_generator.yml` and explore.

# %%
yaml_path = Path("/mnt/data/rhythmic_pulse_generator.yml")
assert yaml_path.exists(), f"Missing file: {yaml_path}"

parser = SpecParser()
spec = parser.parse_file(yaml_path)

print("Spec ID:", spec.spec_id)
print("Title  :", spec.title)
print("Version:", spec.version)
print("Num requirements:", len(spec.requirements))

# %%
# Inspect first requirement (if present)
if spec.requirements:
    first = spec.requirements[0]
    print("First requirement:")
    print("  id         :", first.id)
    print("  title      :", first.title)
    print("  description:", first.description)
    print("  interface  :", getattr(first, 'interface', None))
    print("  validation :", getattr(first, 'validation', None))

# %% [markdown]
# ### Format helpers
# The parser includes helpers to format content for prompts or scaffolding.

# %%
# Show the prompt-formatted summary of requirements (if any)
try:
    print("=== format_requirements_for_prompt ===")
    print(parser.format_requirements_for_prompt(spec))
except Exception as e:
    print("format_requirements_for_prompt error:", e)

# %%
# Demonstrate format_function_signature on each requirement.
# Because this YAML does not embed 'interface' blocks per requirement,
# the function will fall back to a placeholder signature.
for req in spec.requirements:
    sig = parser.format_function_signature(req)
    print(f"\nSignature for requirement {req.id}:\n{sig}")

# %%
# Show validate_spec results
issues = parser.validate_spec(spec)
print("\nValidation issues:", issues if issues else "No issues found.")

# %% [markdown]
# ### Discussion
# - Your YAML separates `interfaces` at the top level. The current parser expects any interface data
#   to live **inside each requirement**. Therefore, `format_function_signature` will produce a placeholder
#   unless `requirement.interface` is present.
#
# **Options:**
# 1. **Keep parser as-is** and embed an `interface` block inside each requirement that needs one.
# 2. **Extend SpecParser** to map top-level `interfaces` into the corresponding requirements by name.
#
# We'll include a short exercise below for approach 2.

# %% [markdown]
# ## Phase 4. Reflection & exercises
#
# **Exercise A (Parser extension):**
# - Modify `_parse_data` to read a top-level `interfaces` list.
# - Build a mapping by interface `name`.
# - When constructing each requirement in `_parse_requirement`, if there is a matching interface by name,
#   attach a `FunctionInterface` with parameters/returns/signature parsed from that interface.
#
# **Exercise B (Validation enhancement):**
# - Update `validate_spec` to ensure each requirement has either a `description` or an attached `interface`.
#
# **Exercise C (Signature enrichment):**
# - Extend `format_function_signature` so that if a requirement has an attached interface,
#   you parse the interface's `signature` string into `function` + typed parameters + return type (if present).
#
# **Your turn:** Try Exercise A, then re-run the demo cells to observe improved signatures.

