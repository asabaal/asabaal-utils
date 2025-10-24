# CodeGenerator Notebook Educational Improvement Plan

## Current Problem
The `02_code_generator_part1.ipynb` notebook currently just calls `generator.generate_from_spec()` like it's magic, with NO BUILDUP to understand how the CodeGenerator actually works internally.

## The Educational Failure
This is like teaching calculus by showing `∫f(x)dx = F(x) + C` without explaining:
- What an integral IS
- How limits work  
- The fundamental theorem
- The step-by-step process

## Improvement Plan

### Phase 1: Deconstruct the CodeGenerator
1. **Explore the class structure** - what methods exist, what do they do?
2. **Examine each component separately**:
   - SpecParser: How does it parse YAML?
   - OllamaClient: How does it talk to AI?
   - PromptTemplates: What prompts does it use?
   - CodeGenerator: How do the methods connect?

### Phase 2: Build Up Understanding
1. **Start with individual methods** - call `_generate_source_code()` alone
2. **Add complexity gradually** - then `_generate_documentation()`, then `_generate_tests()`
3. **Show the data flow** - how spec → prompt → AI → cleaned output
4. **Debug each step** - what happens when things go wrong?

### Phase 3: Reconstruct the Master Function
1. **Show how `generate_from_spec()` orchestrates everything**
2. **Trace the execution path** - which method calls which
3. **Understand the error handling** - what fails when and why

### Phase 4: Make it Interactive
1. **Add debugging tools** - inspect prompts, see AI responses
2. **Show intermediate results** - not just final files
3. **Enable experimentation** - change prompts, see what happens

## Goal
Transform the notebook from "push button, get result" to "understand the machine, then use it."

## Implementation
This plan should be implemented in the `02_code_generator_part1.ipynb` notebook to build proper understanding of how CodeGenerator works step by step.