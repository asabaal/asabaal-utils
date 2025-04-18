# asabaal-utils

A collection of personal utilities for asabaal.

## Budget Utility

A command-line utility to help manage monthly budgets and projections.

### Installation

```bash
# Clone the repository
git clone https://github.com/asabaal/asabaal-utils.git
cd asabaal-utils

# Install dependencies
npm install
```

### Usage

```bash
# Start the budget utility
npm start

# Or use the shorthand command
npm run budget
```

#### Helper Commands

```bash
# Generate sample data
npm run sample

# Load sample data into the application
npm run load-sample

# Backup your data
npm run backup

# Clean/reset your data
npm run clean
```

### Quick Start with Sample Data

To quickly get started with sample data:

```bash
# Generate sample data
npm run sample

# Load the sample data into the application
npm run load-sample

# Run the application
npm start
```

### Features

- Clean month-by-month view of budget data
- Space for projections of upcoming months
- Calculation of surplus/deficit
- Category-based spending tracking
- Import/export functionality

### Data Privacy and Storage

All data is stored locally on your machine and is not committed to the repository. The application uses the following techniques to protect your data:

- `.gitignore` rules to exclude data files from Git
- Local file storage only (no cloud or remote storage)
- Backup functionality for data protection

For detailed information on data handling, see the [Data Handling Guidelines](budget-utility/DATA_HANDLING.md).

### Documentation

- [Budget Utility Usage Guide](budget-utility/USAGE.md)
- [Data Handling Guidelines](budget-utility/DATA_HANDLING.md)
