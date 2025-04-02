# Budget Utility

A command-line utility to help manage monthly budgets and projections.

## Features

- Clean month-by-month view of budget data
- Space for projections of upcoming months
- Calculation of surplus/deficit
- Category-based spending tracking

## Installation

```bash
npm install
```

## Usage

```bash
npm start
```

## Data Structure

The utility uses a structured JSON format to store budget data with the following fields:

- Month: The month of the budget data
- Accounts: List of accounts with charged amounts
- Categories: Spending breakdown by category (Investing, Saving, Spending)
- Totals: Total amounts and surplus/deficit calculations
- Projections: Planned budget for upcoming months
