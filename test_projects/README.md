# Test Projects for PR Analyzer

This directory contains test mini-projects designed to validate and improve the PR analyzer agent.

## Project Structure

### 1. E-commerce API (`ecommerce_api/`)
**Purpose**: Test duplicate detection and SQL injection vulnerability detection

**Good Code** (`good/`):
- `services/product_service.py`: Secure product search with parameterized queries
- `models/product.py`: Proper data model with type hints

**Bad Code** (`bad/`):
- `services/product_search.py`: SQL injection vulnerabilities
- `services/product_finder.py`: Duplicate logic with same SQL injection issues

**Expected Analyzer Detection**:
- Functional duplicates between `product_search.py` and `product_finder.py`
- SQL injection vulnerabilities in both bad files
- Missing type hints and error handling
- Inconsistent naming conventions

---

### 2. Data Processing Pipeline (`data_pipeline/`)
**Purpose**: Test performance anti-pattern and memory efficiency detection

**Good Code** (`good/`):
- `processors/data_transformer.py`: Memory-efficient batch processing with generators

**Bad Code** (`bad/`):
- `utils/data_helper.py`: Memory-intensive processing loading entire datasets
- `helpers/data_processor.py`: Duplicate logic with same memory issues

**Expected Analyzer Detection**:
- Performance anti-patterns: Loading entire datasets into memory
- Duplicate transformation logic across files
- Missing batch processing patterns
- Memory leaks in caching implementations

---

### 3. Authentication Service (`auth_service/`)
**Purpose**: Test security vulnerability detection

**Good Code** (`good/`):
- `auth/auth_service.py`: Secure authentication with bcrypt and JWT

**Bad Code** (`bad/`):
- `security/user_auth.py`: Plain text password storage
- `auth/login_handler.py`: Duplicate authentication with same security flaws

**Expected Analyzer Detection**:
- Critical security vulnerabilities: Plain text passwords
- Authentication logic duplicates
- Missing password hashing
- Insecure token generation

---

## Test Scenarios

### Scenario 1: New Feature Addition
Simulate adding search functionality to e-commerce API:
- Add good secure implementation
- Analyzer should approve and detect no issues

### Scenario 2: Bug Fix with Bad Code
Simulate fixing a bug but introducing security issues:
- Add vulnerable SQL injection code
- Analyzer should flag security vulnerabilities

### Scenario 3: Performance Optimization
Simulate data processing improvements:
- Add memory-efficient batch processing
- Analyzer should recognize performance improvements

### Scenario 4: Refactoring with Duplicates
Simulate code refactoring that creates duplicates:
- Add duplicate authentication logic
- Analyzer should detect functional duplicates

## Expected PR Analyzer Behaviors

### Stages 1-6 (Current Working Parts):
- ✅ Correctly categorize files (API, Database, Security, Performance)
- ✅ Detect file changes and calculate impact scores
- ✅ Identify potential duplicates based on function signatures

### Stages 7-10 (Need Improvement):
- ❌ **Stage 7**: Should detect functional duplicates, not just filename patterns
- ❌ **Stage 8**: Should flag security vulnerabilities and performance issues
- ❌ **Stage 9**: Should provide actionable recommendations, not generic advice
- ❌ **Stage 10**: Should learn from feedback about false positives/negatives

## Success Criteria

The PR analyzer should be able to:

1. **Detect Functional Duplicates**: Identify that `product_search.py` and `product_finder.py` are functionally identical
2. **Flag Security Issues**: Detect SQL injection and plain text password storage
3. **Identify Performance Problems**: Recognize memory-intensive anti-patterns
4. **Provide Specific Recommendations**: Suggest concrete fixes instead of generic advice
5. **Learn from Feedback**: Improve detection accuracy based on user corrections

## Usage

```bash
# Test the PR analyzer against these projects
cd /path/to/pr_analyzer
python -m pr_analyzer.analyzer /path/to/test_projects
```

The analyzer should generate reports that specifically identify the intentional issues in each bad code file while recognizing the quality improvements in the good code files.