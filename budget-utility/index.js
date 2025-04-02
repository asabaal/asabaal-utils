#!/usr/bin/env node

const BudgetManager = require('./cli/budgetManager');

// Run the budget utility
const budgetManager = new BudgetManager();
budgetManager.run().catch(error => {
  console.error('Error running budget utility:', error);
  process.exit(1);
});
