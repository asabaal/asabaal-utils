# %% [markdown]
# # SpecCoder Educational Notebook 02 — CodeGenerator Deep Dive
# *Teach and demonstrate how CodeGenerator turns an OpenSpec into prompts and files.*
#
# **What you'll learn**
# - How to construct `CodeGenerator` correctly and parse a spec.
# - How prompt templates are **strings** that require `.format(...)` with spec data.
# - How to load a YAML spec that ships inside your package using `importlib.resources`.
# - How to build the **source code prompt** and inspect it before any AI calls.
# - How to guard AI generation so the notebook runs even if your local model is down.
#
# **Why this matters**
# Many previous notebooks treated templates like callables, which causes `TypeError: 'str' object is not callable`.
# This notebook fixes that and aligns with the current `generator.py` implementation.

# %%
from pathlib import Path
import sys
import logging
from importlib import resources

# === Repo-root resolution (preferred in your repo) ===
current_dir = Path(__file__).parent if '__file__' in globals() else Path.cwd()
repo_root = current_dir.parent.parent.parent.parent  # adjust if storing under notebooks/
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# === Preferred package imports with local fallbacks ===
try:
    from asabaal_utils.agents.spec_coder.generator import CodeGenerator
    USING_PACKAGE_IMPORT = True
except Exception:
    USING_PACKAGE_IMPORT = False
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    # Local module fallback for standalone execution here
    from generator import CodeGenerator  # noqa: E402

print("Using package import:", USING_PACKAGE_IMPORT)

# Verbose logs for clarity during demos
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(asctime)s | %(name)s | %(message)s"
)

# %% [markdown]
# ## Phase 1. Build the CodeGenerator and parse the spec
# We need the YAML shipped with the package. We use `importlib.resources` so it works
# both in editable installs and packaged wheels. If run as a plain script, we fall back
# to the file next to this notebook.

# %%
# Create the generator
generator = CodeGenerator()

# Determine package anchor for resource loading
package_name = __package__ or "asabaal_utils.agents.spec_coder"

# Resolve the YAML path in a package-safe way
def resolve_yaml_inside_package(filename: str = "rhythmic_pulse_generator.yml") -> Path:
    """
    Resolve a YAML file that ships with the package.
    Fallback: load from the same directory as this notebook script.
    """
    try:
        with resources.as_file(resources.files(package_name) / filename) as _p:
            return Path(_p)
    except Exception:
        # Fallback for direct script execution
        local_path = Path(__file__).with_name(filename)
        if not local_path.exists():
            raise FileNotFoundError(f"Could not find {filename} in package or next to this file.")
        return local_path

yaml_path = resolve_yaml_inside_package()
print("YAML path:", yaml_path)

# Parse the spec using the generator's parser
parsed_spec = generator.spec_parser.parse_file(yaml_path)
print("Spec parsed:", parsed_spec.spec_id, parsed_spec.title, f"requirements={len(parsed_spec.requirements)}")

# %% [markdown]
# ## Phase 2. Understand and build the source code prompt
# In this version of `generator.py`, prompt templates are **strings**, not callables.
# So we must call `.format(...)` with the required fields. This matches
# the reference logic inside `CodeGenerator._generate_source_code`.

# %%
# Prepare prompt fields exactly as the generator does internally
requirements_text = generator.spec_parser.format_requirements_for_prompt(parsed_spec)
interfaces_text = generator.spec_parser.format_interfaces_for_prompt(parsed_spec)

# Build the prompt from the string template with .format(...)
try:
    prompt_template = generator.templates.source_code_prompt  # this is a string template
except AttributeError as e:
    raise AttributeError("Prompt template `source_code_prompt` not found on generator.templates") from e

prompt = prompt_template.format(
    spec_id=parsed_spec.spec_id,
    title=parsed_spec.title,
    version=parsed_spec.version,
    requirements=requirements_text,
    interfaces=interfaces_text
)

print("Prompt length:", len(prompt))
print("\n=== Prompt Preview (first 800 chars) ===\n")
print(prompt[:800])

# %% [markdown]
# ## Phase 3. Guarded generation call
# We try the end-to-end generation, but we guard for cases where the local model is not running.
# This way the notebook remains executable in any environment.

# %%
def try_generation(generator: CodeGenerator, spec_path: Path, out_dir: Path | None = None):
    """Run guarded generation. If the model is unreachable, skip gracefully."""
    if out_dir is None:
        out_dir = current_dir / "output_demo"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Minimal check: call the client's connection test if available
    try:
        ok = generator.ollama_client.test_connection()
    except Exception:
        ok = False

    if not ok:
        print("⚠️  Model endpoint not reachable. Skipping actual generation. Prompt was built successfully.")
        return None

    result = generator.generate_from_spec(spec_path, out_dir)
    print("\nGeneration success:", result.success)
    print("Files generated:", len(result.files_generated))
    for f in result.files_generated[:10]:
        print("  •", f)
    if result.errors:
        print("Errors:", result.errors)
    if result.warnings:
        print("Warnings:", result.warnings)
    return result

_ = try_generation(generator, yaml_path)

# %% [markdown]
# ## Phase 4. Exercises and checks
# - Confirm that templates are strings by printing their type.
# - Try replacing `.format(...)` with a callable style to see the error again.
# - Add fields to the YAML and confirm they appear inside the prompt fields.

# %%
print("Type of source_code_prompt:", type(generator.templates.source_code_prompt))

# Deliberate error demo (commented out):
# generator.templates.source_code_prompt(parsed_spec)  # would raise TypeError: 'str' object is not callable

# %% [markdown]
# ### Summary
# - `source_code_prompt` is a string template. Use `.format(...)` with fields from `parsed_spec`.
# - Load YAML that ships inside your package with `importlib.resources` and a direct file fallback.
# - Guard AI calls so the notebook stays executable even if the local model is unavailable.
