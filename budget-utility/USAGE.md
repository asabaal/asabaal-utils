# Budget Utility Usage Guide

## Overview

This budget utility helps you manage your monthly finances by providing:

1. A clean, month-by-month view of your budget
2. Space for projections of upcoming months
3. Category-based spending tracking
4. Calculation of surplus/deficit

## Installation

```bash
# Navigate to the budget-utility directory
cd budget-utility

# Install dependencies
npm install

# Make the scripts executable (Unix/Linux/Mac)
chmod +x index.js
chmod +x scripts/*.js
```

## Basic Usage

To start the utility:

```bash
npm start
# or
node index.js
```

This will launch the interactive CLI interface with the following options:

1. **View monthly budget report** - Shows a formatted report of all your budget entries
2. **Add new budget entry** - Create a new monthly budget entry
3. **Edit existing budget entry** - Modify an existing entry
4. **Add projections for upcoming month** - Set income and spending projections for future planning
5. **Import budget data** - Import from raw text format
6. **Export budget data to CSV** - Export to CSV for use in spreadsheet applications
7. **Exit** - Exit the application

## Data Structure

The utility organizes budget data into monthly entries with the following components:

- **Accounts** - Sources of income (e.g., STCU, Wells Fargo)
- **Categories** - Spending categories (Investing, Saving, Spending)
- **Notes** - Any additional notes for the month
- **Totals** - Calculated totals including income, spending, and surplus/deficit
- **Projections** - Planned income and spending for future months

## Sample Data

To generate sample data based on your provided example:

```bash
node tools/sampleDataLoader.js
```

This will create a sample budget entry for March 2025 with the accounts and amounts from your example.

## Data Management

The utility saves your data in JSON format in the `data` directory. You can use the provided scripts for data management:

```bash
# Backup your budget data
node scripts/backup-data.js

# Reset/clean your budget data
node scripts/clean-data.js
```

## Importing Data

When importing data, the utility attempts to parse various formats, but for best results, try to structure your data clearly with:

- Month and year clearly indicated (e.g., "March 2025")
- Account names and amounts separated (e.g., "STCU 1794.82")
- Category amounts with dollar signs (e.g., "$211.25")

## Exporting Data

Exporting to CSV creates a file in the `data` directory that can be opened in any spreadsheet application like Excel or Google Sheets.

## Monthly View

The monthly view shows all your budget information organized by month, including:

- Income sources with amounts
- Category breakdown with amounts and percentages
- Surplus/deficit calculation
- Notes for the month
- Projections for upcoming months

## Customization

The code is modular and can be extended to add additional features:

- Add new categories beyond Investing, Saving, and Spending
- Implement data visualization
- Add historical trend analysis
- Include budget vs. actual comparisons

To modify the categories or add new features, edit the relevant files in the `models` directory.
