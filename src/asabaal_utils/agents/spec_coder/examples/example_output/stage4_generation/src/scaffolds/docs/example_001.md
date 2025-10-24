```markdown
# Example: Multiply by 2 Function

## Project Overview

This project implements a basic function that multiplies an integer by 2. The function is designed to be simple and focused, with no additional functionality beyond the core requirement.

## Installation Instructions

To use this project, simply clone the repository and ensure you have Python 3.6 or higher installed. No additional dependencies are required.

```bash
git clone <repository-url>
cd <project-directory>
```

## Usage Examples

### Example 1: Basic Function Usage

```python
result = multiply_by_2(5)
print(result)
```
```output
10
```

This example demonstrates the basic functionality of the multiply_by_2 function with an input of 5, which should return 10.

### Example 2: Negative Number Input

```python
result = multiply_by_2(-3)
print(result)
```
```output
-6
```

This example shows how the function handles negative numbers, where -3 multiplied by 2 equals -6.

### Example 3: Zero Input

```python
result = multiply_by_2(0)
print(result)
```
```output
0
```

This example demonstrates the function's behavior with zero as input, which correctly returns 0.

## API Documentation

### `multiply_by_2(number)`

Multiplies an integer by 2 and returns the result.

**Parameters:**
- `number` (int): The integer to be multiplied by 2.

**Returns:**
- `int`: The result of multiplying the input number by 2.

## Requirements Traceability

| Requirement ID | Description |
|----------------|-------------|
| req-001 | Basic Multiply Function: Implement a function that takes an integer and returns the same integer multiplied by 2. This is the ONLY function that should be implemented. |
```