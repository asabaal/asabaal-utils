```markdown
# Example: Multiply by 2 Function

## Project Overview

This project implements a basic function that multiplies an integer by 2. The function is designed to be simple and straightforward, focusing on a single core functionality as specified in the requirements.

## Installation Instructions

To use this project, simply clone the repository and ensure you have Python installed. The project does not require any external dependencies beyond standard Python libraries.

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

This example demonstrates the basic usage of the multiply_by_2 function with an input of 5, which should return 10.

### Example 2: Negative Number Input

```python
result = multiply_by_2(-3)
print(result)
```
```output
-6
```

This example shows how the function handles negative numbers, multiplying -3 by 2 to produce -6.

### Example 3: Zero Input

```python
result = multiply_by_2(0)
print(result)
```
```output
0
```

This example demonstrates the function's behavior when given zero as input, returning zero as expected.

## API Documentation

### `multiply_by_2(x)`

- **Description**: Takes an integer and returns the same integer multiplied by 2.
- **Parameters**: 
  - `x` (int): The integer to be multiplied by 2.
- **Returns**: 
  - `int`: The result of multiplying `x` by 2.

## Requirements Traceability

| Requirement ID | Description                                      | Implementation Status |
|----------------|--------------------------------------------------|-----------------------|
| req-001        | Basic Multiply Function                          | Implemented           |
```