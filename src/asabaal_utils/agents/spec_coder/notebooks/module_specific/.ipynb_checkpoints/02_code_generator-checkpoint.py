# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.18.1
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Module 2: CodeGenerator - Understanding the AI-Powered Code Generation Engine
#
# ## 🎯 Educational Philosophy: From Black Box to Transparent Machine
#
# This notebook transforms you from a **user** who pushes buttons to an **expert** who understands how the machine works. We'll deconstruct the CodeGenerator piece by piece, then rebuild it with full understanding.
#
# ## 📚 4-Phase Learning Journey
#
# ### **Phase 1: Deconstruct the CodeGenerator** 🔍
# Explore the class structure, understand every component, and see how they fit together.
#
# ### **Phase 2: Build Up Understanding** 🧱
# Test individual methods gradually, understand their inputs/outputs, and see the data flow.
#
# ### **Phase 3: Reconstruct the Master Function** 🏗️
# Follow the orchestration of `generate_from_spec()` step-by-step with real data.
#
# ### **Phase 4: Make it Interactive** 🎮
# Add debugging tools, experiment with different configurations, and become a CodeGenerator expert.
#
# ---
#
# **🎯 GOAL**: By the end, you won't just USE CodeGenerator - you'll UNDERSTAND it completely!
#

# %% [markdown]
# ## 🚀 Phase 1: Deconstruct the CodeGenerator
#
# Let's start by understanding what the CodeGenerator IS before we learn what it DOES.

# %%
# Cell 1.1: Import and Explore the CodeGenerator Architecture
import sys
from pathlib import Path
import inspect

# Add the asabaal_utils package to Python path for proper package imports
current_dir = Path.cwd()
repo_root = current_dir.parent.parent.parent.parent
sys.path.insert(0, str(repo_root))

# Import the actual CodeGenerator and related classes
from asabaal_utils.agents.spec_coder.generator import CodeGenerator, GenerationConfig, GenerationResult

print("🔍 === CODEGENERATOR ARCHITECTURE ANALYSIS ===")
print(f"✅ CodeGenerator class: {CodeGenerator}")
print(f"✅ GenerationConfig class: {GenerationConfig}")
print(f"✅ GenerationResult class: {GenerationResult}")

# Let's understand the CLASS structure first
print("\n📋 === CLASS SIGNATURE ===")
print(f"CodeGenerator.__module__: {CodeGenerator.__module__}")
print(f"CodeGenerator.__doc__: {CodeGenerator.__doc__}")

# What methods does it have?
public_methods = [m for m in dir(CodeGenerator) if not m.startswith("_")]
private_methods = [m for m in dir(CodeGenerator) if m.startswith("_") and not m.startswith("__")]
dunder_methods = [m for m in dir(CodeGenerator) if m.startswith("__") and m.endswith("__")]

print(f"\n🔧 === METHOD BREAKDOWN ===")
print(f"Public methods ({len(public_methods)}): {public_methods}")
print(f"Private methods ({len(private_methods)}): {private_methods}")
print(f"Dunder methods ({len(dunder_methods)}): {dunder_methods}")

# %%
# Cell 1.2: Deep Dive into the Constructor - Understanding Initialization
print("🏗️ === CONSTRUCTOR ANALYSIS ===")

# Get the constructor signature
init_signature = inspect.signature(CodeGenerator.__init__)
print(f"Constructor signature: {init_signature}")

# Get the source code of the constructor
try:
    init_source = inspect.getsource(CodeGenerator.__init__)
    print(f"\n📝 Constructor source code:")
    print(init_source)
except Exception as e:
    print(f"Could not get source: {e}")

# Let's create an instance and see what gets initialized
print("\n🔧 === INSTANCE CREATION ANALYSIS ===")
generator = CodeGenerator()
print(f"✅ Created instance: {generator}")

# What attributes does this instance have?
instance_attrs = {}
for attr_name in dir(generator):
    if not attr_name.startswith("__"):
        attr_value = getattr(generator, attr_name)
        if not callable(attr_value):
            instance_attrs[attr_name] = type(attr_value)

print(f"\n📊 === INSTANCE ATTRIBUTES ===")
for attr_name, attr_type in instance_attrs.items():
    print(f"  {attr_name}: {attr_type}")

# %%
# Cell 1.3: Understanding the Three Core Components
print("🧩 === CORE COMPONENTS ANALYSIS ===")

# Let's examine each integrated component
components = {
    "ollama_client": generator.ollama_client,
    "templates": generator.templates,
    "spec_parser": generator.spec_parser,
    "config": generator.config
}

for comp_name, comp_obj in components.items():
    print(f"\n🔍 {comp_name.upper()}:")
    print(f"  Type: {type(comp_obj)}")
    print(f"  Module: {comp_obj.__class__.__module__}")
    
    # Get key methods/attributes for each component
    if hasattr(comp_obj, '__dict__'):
        key_attrs = [attr for attr in dir(comp_obj) if not attr.startswith("_")][:5]  # First 5
        print(f"  Key attributes/methods: {key_attrs}")

print("\n💡 === COMPONENT PURPOSES ===")
print("• ollama_client: Handles communication with the LLM (Ollama)")
print("• templates: Manages prompt templates for different generation tasks")
print("• spec_parser: Parses and validates specification files")
print("• config: Manages generation configuration and parameters")

# %% [markdown]
# ## 🧱 Phase 2: Build Up Understanding
#
# Now let's test individual methods and understand their inputs/outputs before we see them work together.

# %%
# Cell 2.1: Method-by-Method Analysis - Understanding Each Function
print("🔧 === METHOD SIGNATURE ANALYSIS ===")

# Let's examine each public method in detail
public_methods = [m for m in dir(generator) if not m.startswith("_")]

for method_name in public_methods:
    if hasattr(generator, method_name) and callable(getattr(generator, method_name)):
        method = getattr(generator, method_name)
        
        print(f"\n📋 Method: {method_name}")
        
        # Get signature
        try:
            sig = inspect.signature(method)
            print(f"  Signature: {sig}")
        except Exception as e:
            print(f"  Signature: Could not get ({e})")
        
        # Get docstring
        doc = method.__doc__ or "No documentation"
        print(f"  Purpose: {doc.strip()[:100]}...")
        
        # Get source if available
        try:
            source_lines = inspect.getsourcelines(method)
            print(f"  Lines of code: {len(source_lines[1])}")
        except Exception:
            print(f"  Lines of code: Not available")

# %%
# Cell 2.2: Understanding the Main Method - generate_from_spec
print("🎯 === MAIN METHOD DEEP DIVE: generate_from_spec ===")

# Get the full source code of the main method
try:
    source_lines = inspect.getsourcelines(generator.generate_from_spec)
    source_code = ''.join(source_lines[0])
    
    print("📝 Full source code:")
    print(source_code)
    
    print(f"\n📊 Code Analysis:")
    print(f"  Total lines: {len(source_lines[1])}")
    print(f"  Starting line: {source_lines[1]}")
    
except Exception as e:
    print(f"Could not get source: {e}")
    
    # Let's at least get the signature
    sig = inspect.signature(generator.generate_from_spec)
    print(f"\n📋 Method signature: {sig}")
    
    # Get docstring
    doc = generator.generate_from_spec.__doc__ or "No documentation"
    print(f"📖 Documentation: {doc}")

# %%
# Cell 2.3: Understanding Helper Methods - The Building Blocks
print("🧩 === HELPER METHODS ANALYSIS ===")

# Let's look at the private helper methods
private_methods = [m for m in dir(generator) if m.startswith("_") and not m.startswith("__")]

print(f"Found {len(private_methods)} helper methods: {private_methods}")

for method_name in private_methods:
    if hasattr(generator, method_name) and callable(getattr(generator, method_name)):
        method = getattr(generator, method_name)
        
        print(f"\n🔧 Helper: {method_name}")
        
        # Get signature
        try:
            sig = inspect.signature(method)
            print(f"  Signature: {sig}")
        except Exception as e:
            print(f"  Signature: Could not get ({e})")
        
        # Get docstring
        doc = method.__doc__ or "No documentation"
        print(f"  Purpose: {doc.strip()[:80]}...")
        
        # Try to get first few lines of source
        try:
            source_lines = inspect.getsourcelines(method)
            first_line = source_lines[0][0].strip() if source_lines[0] else "No source"
            print(f"  First line: {first_line}")
        except Exception:
            print(f"  First line: Not available")

# %% [markdown]
# ## 🏗️ Phase 3: Reconstruct the Master Function
#
# Now let's follow `generate_from_spec()` step-by-step with real data to understand the orchestration.

# %%
with resources.as_file(resources.files(package_name) / "rhythmic_pulse_generator.yml") as _p:
    yaml_path = Path(_p)
yaml_path    

# %%
# Call the spec parser directly
parsed_spec = generator.spec_parser.parse_file(yaml_path)

print(f"\n✅ Parsing successful!")
print(f"Parsed spec type: {type(parsed_spec)}")

# Examine the parsed structure
if hasattr(parsed_spec, '__dict__'):
    print(f"\n📊 === PARSED SPEC STRUCTURE ===")
    for attr, value in parsed_spec.__dict__.items():
        print(f"  {attr}: {type(value)} = {value}")

# Let's understand what the generator will work with
print(f"\n🎯 === KEY DATA FOR GENERATION ===")
if hasattr(parsed_spec, 'name'):
    print(f"  Spec name: {parsed_spec.name}")
if hasattr(parsed_spec, 'description'):
    print(f"  Description: {parsed_spec.description}")
if hasattr(parsed_spec, 'interfaces'):
    print(f"  Interfaces: {len(parsed_spec.interfaces) if parsed_spec.interfaces else 0}")
if hasattr(parsed_spec, 'requirements'):
    print(f"  Requirements: {len(parsed_spec.requirements) if parsed_spec.requirements else 0}")

# %%
# Cell 3.3: Step 2 - Prompt Generation - Understanding AI Communication
print("💬 === STEP 2: PROMPT GENERATION ===")

# Let's see what prompt gets generated for our spec
# First, we need the parsed spec from previous step
parsed_spec = generator.spec_parser.parse_file(yaml_path)

print("Input to prompt generation:")
print(f"  Parsed spec: {type(parsed_spec)}")
print(f"  Spec name: {getattr(parsed_spec, 'name', 'Unknown')}")

# Generate the prompt (this is what gets sent to the AI)
if hasattr(generator.templates, 'source_code_prompt'):
    prompt = generator.templates.source_code_prompt(parsed_spec)
    
    print(f"\n✅ Prompt generated successfully!")
    print(f"Prompt length: {len(prompt)} characters")
    print(f"Prompt lines: {len(prompt.split(chr(10)))} lines")
    
    print(f"\n📝 === GENERATED PROMPT (First 500 chars) ===")
    print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
    
    # Let's understand the prompt structure
    print(f"\n🔍 === PROMPT ANALYSIS ===")
    if "```" in prompt:
        code_blocks = prompt.count("```")
        print(f"  Code blocks: {code_blocks // 2}")
    if "requirements:" in prompt.lower():
        print(f"  Contains requirements: ✅")
    if "interfaces:" in prompt.lower():
        print(f"  Contains interfaces: ✅")
        
else:
    print("❌ Could not find source_code_prompt method")

# %%
# Cell 3.4: Step 3 - AI Communication - Understanding LLM Interaction
print("🤖 === STEP 3: AI COMMUNICATION ===")

# Let's understand what happens when the generator talks to the AI
try:
    # Get the prompt we generated earlier
    parsed_spec = generator.spec_parser.parse_file(Path(test_spec_path))
    prompt = generator.templates.source_code_prompt(parsed_spec)
    
    print("Input to ollama_client.generate():")
    print(f"  Prompt length: {len(prompt)} characters")
    print(f"  Model: {generator.config.model if hasattr(generator.config, 'model') else 'default'}")
    
    # Let's examine the ollama client configuration
    print(f"\n🔧 === OLLAMA CLIENT CONFIGURATION ===")
    ollama = generator.ollama_client
    print(f"  Client type: {type(ollama)}")
    
    # Check what methods are available
    ollama_methods = [m for m in dir(ollama) if not m.startswith("_")]
    print(f"  Available methods: {ollama_methods}")
    
    # Try to understand the generate method
    if hasattr(ollama, 'generate'):
        sig = inspect.signature(ollama.generate)
        print(f"  generate() signature: {sig}")
        
        # Get docstring
        doc = ollama.generate.__doc__ or "No documentation"
        print(f"  Purpose: {doc.strip()[:100]}...")
    
    print(f"\n💡 === AI COMMUNICATION FLOW ===")
    print("1. CodeGenerator creates a prompt from the spec")
    print("2. CodeGenerator calls ollama_client.generate(prompt)")
    print("3. OllamaClient sends the prompt to the LLM")
    print("4. LLM processes the prompt and returns generated code")
    print("5. OllamaClient returns the response to CodeGenerator")
    
except Exception as e:
    print(f"❌ AI communication analysis failed: {e}")
    print(f"Error type: {type(e)}")

# %%
# Cell 3.5: Step 4 - Full Orchestration - Putting It All Together
print("🎯 === STEP 4: FULL ORCHESTRATION ===")

# Now let's trace the complete generate_from_spec flow
print("📋 === COMPLETE FLOW ANALYSIS ===")
print("Input: test_spec_path (YAML file)")
print("Output: GenerationResult (with generated code)")

print("\n🔄 === STEP-BY-STEP EXECUTION ===")

# Step 1: Parse the spec
print("\n1️⃣ Parsing specification...")
parsed_spec = generator.spec_parser.parse_file(Path(test_spec_path))
print(f"   ✅ Parsed: {parsed_spec.name if hasattr(parsed_spec, 'name') else 'Unknown'}")

# Step 2: Generate prompt
print("\n2️⃣ Generating prompt...")
prompt = generator.templates.source_code_prompt(parsed_spec)
print(f"   ✅ Generated: {len(prompt)} character prompt")

# Step 3: Generate code (this is where AI happens)
print("\n3️⃣ Generating code with AI...")
try:
    # This is the actual AI call
    generated_code = generator.ollama_client.generate(prompt)
    print(f"   ✅ Generated: {len(generated_code)} character response")
    
    # Step 4: Create result
    print("\n4️⃣ Creating result object...")
    result = GenerationResult(
        spec_name=parsed_spec.name if hasattr(parsed_spec, 'name') else 'unknown',
        generated_code=generated_code,
        success=True,
        message="Code generated successfully"
    )
    print(f"   ✅ Result: {type(result)}")
    
    # Let's examine the result
    print(f"\n📊 === FINAL RESULT ANALYSIS ===")
    print(f"Result type: {type(result)}")
    if hasattr(result, '__dict__'):
        for attr, value in result.__dict__.items():
            if attr == 'generated_code':
                print(f"  {attr}: {type(value)} ({len(str(value))} chars)")
            else:
                print(f"  {attr}: {value}")
    
    print(f"\n🎉 === ORCHESTRATION COMPLETE! ===")
    print("You've now seen the complete flow of CodeGenerator!")
    
except Exception as e:
    print(f"   ❌ AI generation failed: {e}")
    print(f"   This is expected if Ollama is not running")
    print(f"   But you now understand the complete orchestration!")

# %% [markdown]
# ## 🎮 Phase 4: Make it Interactive
#
# Now let's add debugging tools and experiment with different configurations to become CodeGenerator experts.

# %%
# Cell 4.1: Interactive Debugging Tools - Inspect the Inner Workings
print("🔍 === INTERACTIVE DEBUGGING TOOLS ===")

# Let's create a debugging function that shows us exactly what's happening
def debug_generate_from_spec(spec_path, verbose=True):
    """Debug version of generate_from_spec that shows every step."""
    
    print(f"🚀 Starting debug generation for: {spec_path}")
    
    # Step 1: Parse spec
    print("\n📋 === STEP 1: PARSING SPEC ===")
    try:
        parsed_spec = generator.spec_parser.parse_file(Path(spec_path))
        print(f"✅ Spec parsed successfully")
        if verbose:
            print(f"   Name: {getattr(parsed_spec, 'name', 'Unknown')}")
            print(f"   Description: {getattr(parsed_spec, 'description', 'No description')}")
            print(f"   Requirements: {len(getattr(parsed_spec, 'requirements', []))}")
            print(f"   Interfaces: {len(getattr(parsed_spec, 'interfaces', []))}")
    except Exception as e:
        print(f"❌ Spec parsing failed: {e}")
        return None
    
    # Step 2: Generate prompt
    print("\n💬 === STEP 2: GENERATING PROMPT ===")
    try:
        prompt = generator.templates.source_code_prompt(parsed_spec)
        print(f"✅ Prompt generated ({len(prompt)} chars)")
        if verbose:
            print(f"   First 200 chars: {prompt[:200]}...")
            print(f"   Contains 'requirements': {'requirements' in prompt.lower()}")
            print(f"   Contains 'interfaces': {'interfaces' in prompt.lower()}")
    except Exception as e:
        print(f"❌ Prompt generation failed: {e}")
        return None
    
    # Step 3: AI generation
    print("\n🤖 === STEP 3: AI GENERATION ===")
    try:
        response = generator.ollama_client.generate(prompt)
        print(f"✅ AI response received ({len(response)} chars)")
        if verbose:
            print(f"   First 200 chars: {response[:200]}...")
            print(f"   Contains 'def': {'def' in response}")
            print(f"   Contains 'class': {'class' in response}")
    except Exception as e:
        print(f"❌ AI generation failed: {e}")
        print(f"   This is expected if Ollama is not running")
        return None
    
    # Step 4: Create result
    print("\n📦 === STEP 4: CREATING RESULT ===")
    result = GenerationResult(
        spec_name=getattr(parsed_spec, 'name', 'unknown'),
        generated_code=response,
        success=True,
        message="Debug generation completed"
    )
    print(f"✅ Result created: {type(result)}")
    
    return result

# Test our debugging function
print("🧪 Testing debug function...")
debug_result = debug_generate_from_spec(str(test_spec_path), verbose=True)

if debug_result:
    print(f"\n🎉 Debug completed successfully!")
else:
    print(f"\n⚠️ Debug completed with expected failures (Ollama not running)")

# %%
# Cell 4.2: Configuration Exploration - Understanding Customization
print("⚙️ === CONFIGURATION EXPLORATION ===")

# Let's deeply understand GenerationConfig
config = GenerationConfig()
print(f"Default config: {config}")

# Get all configuration options
config_attrs = [attr for attr in dir(config) if not attr.startswith("_")]
print(f"\n📋 Available configuration options ({len(config_attrs)}):")

for attr in config_attrs:
    value = getattr(config, attr)
    print(f"  {attr}: {value} ({type(value).__name__})")

# Let's create custom configurations
print(f"\n🔧 === CUSTOM CONFIGURATION EXPERIMENTS ===")

# Experiment 1: Different models
config1 = GenerationConfig()
if hasattr(config1, 'model'):
    config1.model = "llama2"
    print(f"Experiment 1 - Model: {config1.model}")

# Experiment 2: Different temperature
config2 = GenerationConfig()
if hasattr(config2, 'temperature'):
    config2.temperature = 0.1  # More deterministic
    print(f"Experiment 2 - Temperature: {config2.temperature}")

# Experiment 3: Different max tokens
config3 = GenerationConfig()
if hasattr(config3, 'max_tokens'):
    config3.max_tokens = 500  # Shorter responses
    print(f"Experiment 3 - Max tokens: {config3.max_tokens}")

print(f"\n💡 === CONFIGURATION IMPACT ===")
print("• Model: Different LLMs have different capabilities")
print("• Temperature: Controls creativity vs determinism")
print("• Max tokens: Controls response length")
print("• These settings directly affect the generated code quality!")

# %%
# Cell 4.3: Experimentation Lab - Try Different Specifications
print("🧪 === EXPERIMENTATION LAB ===")

# Let's create musical variations to see how the generator handles them
# Use REAL spec files instead of hardcoded content
real_spec_files = [
    {
        "name": "rhythmic_pulse_generator",
        "path": Path(__file__).parent.parent.parent.parent / "asabaal_utils" / "agents" / "spec_coder" / "rhythmic_pulse_generator.yml"
    },
    {
        "name": "test_calculator", 
        "path": Path(__file__).parent.parent.parent.parent / "asabaal_utils" / "agents" / "spec_coder" / "rhythmic_pulse_generator.yml"
    }
]

# Load real spec content
experiments = []
for spec_info in real_spec_files:
    if spec_info["path"].exists():
        with open(spec_info["path"], 'r') as f:
            content = f.read()
        experiments.append({
            "name": spec_info["name"],
            "content": content
        })
        print(f"✅ Loaded REAL spec: {spec_info['name']}")
    else:
        print(f"❌ Spec file not found: {spec_info['path']}")

# If no real specs found, create minimal fallback
if not experiments:
    print("❌ No real specs found, using fallback")
    experiments = [
        {
            "name": "rhythmic_pulse_generator",
            "path": Path(__file__).parent.parent.parent.parent / "rhythmic_pulse_generator.yml"
        }
    ]

# Run experiments
for i, experiment in enumerate(experiments, 1):
    print(f"\n🔬 Experiment {i}: {experiment['name']}")
    
    # Create spec file
    spec_path = Path(f"experiment_{experiment['name']}.yml")
    with open(spec_path, "w") as f:
        f.write(experiment['content'])
    
    # Parse and analyze
    try:
        parsed = generator.spec_parser.parse_file(Path(spec_path))
        print(f"   ✅ Parsed: {parsed.name}")
        print(f"   📋 Requirements: {len(getattr(parsed, 'requirements', []))}")
        print(f"   🔧 Interfaces: {len(getattr(parsed, 'interfaces', []))}")
        
        # Generate prompt
        prompt = generator.templates.source_code_prompt(parsed)
        print(f"   💬 Prompt: {len(prompt)} chars")
        
        # Clean up
        spec_path.unlink()
        
    except Exception as e:
        print(f"   ❌ Failed: {e}")

print(f"\n🎉 Experimentation complete!")
print("You can see how different specs create different prompts and would generate different code.")

# %%
# Cell 4.4: Performance Analysis - Understanding Efficiency
print("⚡ === PERFORMANCE ANALYSIS ===")

import time

# Let's measure how long each step takes
def measure_performance(spec_path):
    """Measure performance of each generation step."""
    
    times = {}
    
    # Measure parsing
    start = time.time()
    parsed_spec = generator.spec_parser.parse_file(Path(spec_path))
    times['parsing'] = time.time() - start
    
    # Measure prompt generation
    start = time.time()
    prompt = generator.templates.source_code_prompt(parsed_spec)
    times['prompt_generation'] = time.time() - start
    
    # Measure AI generation (this will fail without Ollama, but we can measure the attempt)
    start = time.time()
    try:
        response = generator.ollama_client.generate(prompt)
        times['ai_generation'] = time.time() - start
        times['ai_success'] = True
    except Exception as e:
        times['ai_generation'] = time.time() - start
        times['ai_success'] = False
        times['ai_error'] = str(e)
    
    return times

# Run performance measurement
print("🏃‍♂️ Measuring performance...")
perf_times = measure_performance(str(test_spec_path))

print(f"\n📊 === PERFORMANCE RESULTS ===")
total_time = 0
for step, duration in perf_times.items():
    if step != 'ai_success' and step != 'ai_error':
        print(f"  {step}: {duration:.4f} seconds")
        total_time += duration

print(f"  Total (excluding AI): {total_time:.4f} seconds")

if perf_times.get('ai_success'):
    print(f"  AI generation: {perf_times['ai_generation']:.4f} seconds")
    print(f"  Total with AI: {total_time + perf_times['ai_generation']:.4f} seconds")
else:
    print(f"  AI generation: Failed ({perf_times.get('ai_error', 'Unknown error')})")

print(f"\n💡 === PERFORMANCE INSIGHTS ===")
print("• Spec parsing is typically very fast (< 0.01s)")
print("• Prompt generation is also fast (< 0.01s)")
print("• AI generation is the bottleneck (seconds to minutes)")
print("• Most optimization effort should focus on prompt quality!")

# %% [markdown]
# ## 🎓 Educational Summary: From Black Box to Expert
#
# Let's consolidate what we've learned about the CodeGenerator.

# %%
# Cell 5.1: Knowledge Consolidation - What We've Learned
print("🎓 === KNOWLEDGE CONSOLIDATION ===")

print("\n🔍 === PHASE 1: DECONSTRUCTION ===")
print("✅ Understood CodeGenerator class structure")
print("✅ Identified all public and private methods")
print("✅ Examined constructor and initialization")
print("✅ Analyzed the three core components:")
print("   • OllamaClient: AI communication")
print("   • PromptTemplates: Prompt engineering")
print("   • SpecParser: Specification handling")

print("\n🧱 === PHASE 2: BUILDING UNDERSTANDING ===")
print("✅ Analyzed method signatures and purposes")
print("✅ Deep-dived into generate_from_spec() method")
print("✅ Examined helper methods and their roles")
print("✅ Understood input/output data flows")

print("\n🏗️ === PHASE 3: RECONSTRUCTION ===")
print("✅ Traced complete generation flow step-by-step")
print("✅ Understood spec parsing → prompt generation → AI communication")
print("✅ Saw how GenerationResult objects are created")
print("✅ Identified data transformations at each stage")

print("\n🎮 === PHASE 4: INTERACTIVE MASTERY ===")
print("✅ Created debugging tools for inspection")
print("✅ Experimented with different specifications")
print("✅ Analyzed performance characteristics")
print("✅ Understood configuration options")

# %%
# Cell 5.2: Expert-Level Understanding - Key Insights
print("💡 === EXPERT-LEVEL INSIGHTS ===")

print("\n🎯 === ARCHITECTURAL INSIGHTS ===")
print("• CodeGenerator is an orchestrator, not a monolith")
print("• It follows a clear pipeline: Parse → Prompt → Generate → Package")
print("• Each component has a single responsibility")
print("• Configuration drives behavior, not hard-coded values")

print("\n⚡ === PERFORMANCE INSIGHTS ===")
print("• Spec parsing and prompt generation are negligible (< 0.01s)")
print("• AI generation is the primary bottleneck (seconds to minutes)")
print("• Prompt quality directly affects output quality")
print("• Caching could dramatically improve performance")

print("\n🔧 === DEBUGGING INSIGHTS ===")
print("• Most failures occur in AI communication step")
print("• Prompt inspection is crucial for debugging")
print("• Spec validation catches issues early")
print("• Error handling preserves partial results")

print("\n🎨 === DESIGN INSIGHTS ===")
print("• Separation of concerns enables testing")
print("• Template system allows prompt customization")
print("• Configuration system enables flexibility")
print("• Result objects provide structured feedback")

# %%
# Cell 5.3: Practical Applications - What You Can Do Now
print("🛠️ === PRACTICAL APPLICATIONS ===")

print("\n✅ === WHAT YOU CAN NOW DO ===")
print("• Create CodeGenerator instances with custom configurations")
print("• Debug generation issues step-by-step")
print("• Write custom specifications for different use cases")
print("• Analyze and optimize generation performance")
print("• Extend the system with new prompt templates")
print("• Integrate with different LLM providers")

print("\n🚀 === ADVANCED POSSIBILITIES ===")
print("• Implement prompt caching for performance")
print("• Add validation layers for generated code")
print("• Create specialized generators for different languages")
print("• Build testing pipelines for generated code")
print("• Implement progressive enhancement strategies")

print("\n🎯 === NEXT STEPS IN YOUR JOURNEY ===")
print("• Study the other modules (SpecParser, Orchestrator, etc.)")
print("• Understand how CodeGenerator fits in the larger pipeline")
print("• Experiment with real-world specifications")
print("• Contribute improvements to the codebase")
print("• Build your own AI-powered code generation tools")

# %%
# Cell 6.1: Final Challenge - Test Your Understanding
print("🏆 === FINAL CHALLENGE ===")

# Create a complex musical specification to test your understanding
challenge_spec = """
name: music_production_suite
version: 2.0.0
description: A comprehensive music production suite
requirements:
  - name: audio_processing
    description: Advanced audio processing and effects
    validation:
      type: integration
  - name: midi_support
    description: MIDI file import/export and editing
    validation:
      type: functional
  - name: real_time_processing
    description: Real-time audio processing capabilities
    validation:
      type: performance
interfaces:
  - name: MusicProductionSuite
    type: class
    methods:
      - name: load_audio_file
        signature: "load_audio_file(file_path: str) -> AudioTrack"
      - name: apply_effect
        signature: "apply_effect(track: AudioTrack, effect: Effect) -> bool"
      - name: export_project
        signature: "export_project(format: str, quality: str) -> str"
      - name: add_midi_track
        signature: "add_midi_track(midi_data: dict) -> MidiTrack"
  - name: AudioTrack
    type: class
    attributes:
      - name: id
        type: str
      - name: name
        type: str
      - name: duration
        type: float
      - name: sample_rate
        type: int
  - name: Effect
    type: class
    methods:
      - name: apply_reverb
        signature: "apply_reverb(audio_data: list, room_size: float) -> list"
      - name: apply_delay
        signature: "apply_delay(audio_data: list, delay_time: float) -> list"
"""

# Write challenge spec
challenge_path = Path("music_production_suite_spec.yml")
with open(challenge_path, "w") as f:
    f.write(challenge_spec)

print(f"✅ Created musical challenge specification: {challenge_path}")
print("🎵 This is a complex music production example!")

# Now test your understanding - predict what will happen
print("\n🤔 === MUSICAL PREDICTION CHALLENGE ===")
print("Before running the next cell, predict:")
print("1. How many requirements will be parsed?")
print("2. How many interfaces will be parsed?")
print("3. How many methods will be in MusicProductionSuite?")
print("4. Approximately how long will the prompt be?")
print("5. What will be the main bottleneck in generation?")

# Run the analysis
print("\n🔍 === RUNNING ANALYSIS ===")
try:
    # Parse the spec
    parsed = generator.spec_parser.parse_file(Path(challenge_path))
    print(f"✅ Parsed spec: {parsed.name}")
    print(f"   Requirements: {len(getattr(parsed, 'requirements', []))}")
    print(f"   Interfaces: {len(getattr(parsed, 'interfaces', []))}")
    
    # Count methods
    total_methods = 0
    for interface in getattr(parsed, 'interfaces', []):
        if hasattr(interface, 'methods'):
            total_methods += len(interface.methods)
    print(f"   Total methods: {total_methods}")
    
    # Generate prompt
    prompt = generator.templates.source_code_prompt(parsed)
    print(f"   Prompt length: {len(prompt)} characters")
    
    # Performance test
    perf = measure_performance(str(challenge_path))
    print(f"   Parsing time: {perf['parsing']:.4f}s")
    print(f"   Prompt generation time: {perf['prompt_generation']:.4f}s")
    print(f"   AI generation time: {perf['ai_generation']:.4f}s (failed expected)")
    
    print(f"\n🎉 === CHALLENGE COMPLETE ===")
    print("You've successfully analyzed a complex specification!")
    
except Exception as e:
    print(f"❌ Challenge failed: {e}")

# Clean up
if challenge_path.exists():
    challenge_path.unlink()
    print(f"✅ Cleaned up challenge file")

# %%
# Cell 6.2: Course Completion - You're Now a CodeGenerator Expert!
print("🎓 === COURSE COMPLETION ===")

print("\n🏆 === YOUR ACHIEVEMENTS ===")
print("✅ Deconstructed CodeGenerator architecture")
print("✅ Understood every method and component")
print("✅ Traced complete generation pipeline")
print("✅ Built debugging and analysis tools")
print("✅ Experimented with different specifications")
print("✅ Analyzed performance characteristics")
print("✅ Completed expert-level challenge")

print("\n🧠 === YOUR NEW EXPERTISE ===")
print("• You understand CodeGenerator from inside out")
print("• You can debug generation issues systematically")
print("• You can optimize performance and quality")
print("• You can extend and customize the system")
print("• You can integrate CodeGenerator into larger systems")

print("\n🚀 === WHAT'S NEXT ===")
print("• Apply this knowledge to other SpecCoder modules")
print("• Build your own AI-powered development tools")
print("• Contribute to the SpecCoder codebase")
print("• Share your expertise with others")

print("\n💡 === FINAL INSIGHT ===")
print("CodeGenerator is more than just a tool - it's a pattern")
print("for how AI can be integrated into software development.")
print("You now understand this pattern deeply.")

print("\n🎉 === CONGRATULATIONS! ===")
print("You've transformed from a user who pushes buttons")
print("to an expert who understands the machine!")
print("\n" + "="*50)
print("   YOU ARE NOW A CODEGENERATOR EXPERT!")
print("="*50)
