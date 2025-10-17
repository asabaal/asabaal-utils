# String Utilities

## Project Overview

This project provides a set of utility functions for string manipulation. It includes functions for reversing strings and capitalizing the first letter of each word in a string. The implementation is designed to be simple, efficient, and well-tested.

## Installation Instructions

To use this project, simply include the source files in your project or install it as a dependency using your preferred package manager.

```bash
# Example installation command (replace with actual package manager command)
npm install string-utilities
```

## Usage Examples

```javascript
const { reverseString, capitalizeWords } = require('string-utilities');

// Reverse a string
const reversed = reverseString("hello world");
console.log(reversed); // Output: "dlrow olleh"

// Capitalize words
const capitalized = capitalizeWords("hello world");
console.log(capitalized); // Output: "Hello World"
```

## API Documentation

### `reverseString(str)`

Reverses the input string.

**Parameters:**
- `str` (string): The string to reverse.

**Returns:**
- (string): The reversed string.

### `capitalizeWords(str)`

Capitalizes the first letter of each word in the input string.

**Parameters:**
- `str` (string): The string to capitalize.

**Returns:**
- (string): The capitalized string.

## Requirements Traceability

| Requirement ID | Description                                      | Validation Method        |
|----------------|--------------------------------------------------|--------------------------|
| req-001        | String Reversal Function                         | unit test in             |
| req-002        | String Capitalization Function                   | unit test in             |