/**
 * Parse raw budget data text and convert to structured format
 * @param {string} rawData - Raw budget data text
 * @returns {Object} Structured budget data
 */
const parseRawBudgetData = (rawData) => {
  // This is a simplified parser for the example data
  // For a real implementation, you would need to handle various data formats
  
  // Example implementation for the format provided in the request
  const result = {
    entries: {}
  };
  
  // Split by lines and remove empty lines
  const lines = rawData.split('\n').filter(line => line.trim() !== '');
  
  // State variables for parsing
  let currentMonth = null;
  let currentYear = null;
  let currentEntry = null;
  
  // Very basic parser that looks for patterns in the text
  lines.forEach(line => {
    // Look for month and year pattern
    const monthYearMatch = line.match(/(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})/);
    
    if (monthYearMatch) {
      currentMonth = monthYearMatch[1];
      currentYear = parseInt(monthYearMatch[2]);
      
      const entryKey = `${currentMonth}-${currentYear}`;
      if (!result.entries[entryKey]) {
        result.entries[entryKey] = {
          month: currentMonth,
          year: currentYear,
          accounts: [],
          notes: '',
          categories: {
            investing: 0,
            saving: 0,
            spending: 0
          },
          projections: {
            income: 0,
            categories: {
              investing: 0,
              saving: 0,
              spending: 0
            }
          }
        };
      }
      
      currentEntry = result.entries[entryKey];
    }
    
    // If we've identified a month/year, try to parse other information
    if (currentEntry) {
      // Look for account information
      // This assumes a format like "AccountName Amount"
      const accountMatch = line.match(/(\w+\s*\w*)\s+(\d+\.\d+)/);
      if (accountMatch) {
        currentEntry.accounts.push({
          name: accountMatch[1].trim(),
          amount: parseFloat(accountMatch[2])
        });
      }
      
      // Look for category information
      // This assumes a format with dollar amounts
      const categoryMatch = line.match(/\$(\d+\.\d+)\$(\d+\.\d+)\$(\d+\.\d+)/);
      if (categoryMatch) {
        currentEntry.categories.investing = parseFloat(categoryMatch[1]);
        currentEntry.categories.saving = parseFloat(categoryMatch[2]);
        currentEntry.categories.spending = parseFloat(categoryMatch[3]);
      }
      
      // Look for notes
      if (line.includes('NOTES') || line.toLowerCase().includes('note')) {
        // Extract text after NOTES
        const noteMatch = line.match(/NOTES[^a-zA-Z0-9]*(.+)/i);
        if (noteMatch) {
          currentEntry.notes += noteMatch[1].trim() + '\n';
        }
      }
    }
  });
  
  return result;
};

/**
 * Generate a formatted text report of the budget
 * @param {Object} budget - Budget object
 * @returns {string} Formatted budget report
 */
const generateBudgetReport = (budget) => {
  const entries = budget.getAllEntries();
  let report = 'BUDGET REPORT\n=============\n\n';
  
  entries.forEach(entry => {
    report += `${entry.month} ${entry.year}\n`;
    report += '='.repeat(entry.month.length + entry.year.toString().length + 1) + '\n\n';
    
    // Accounts section
    report += 'ACCOUNTS:\n';
    entry.accounts.forEach(account => {
      report += `  ${account.name}: $${account.amount.toFixed(2)}\n`;
    });
    report += `  TOTAL INCOME: $${entry.totals.income.toFixed(2)}\n\n`;
    
    // Categories section
    report += 'CATEGORIES:\n';
    report += `  Investing: $${entry.categories.investing.toFixed(2)} (${entry.percentages.investing}%)\n`;
    report += `  Saving: $${entry.categories.saving.toFixed(2)} (${entry.percentages.saving}%)\n`;
    report += `  Spending: $${entry.categories.spending.toFixed(2)} (${entry.percentages.spending}%)\n`;
    report += `  TOTAL: $${entry.totals.categoriesTotal.toFixed(2)}\n\n`;
    
    // Surplus/Deficit
    report += `SURPLUS/DEFICIT: $${entry.totals.surplus.toFixed(2)}\n\n`;
    
    // Notes
    if (entry.notes.trim()) {
      report += 'NOTES:\n';
      report += `  ${entry.notes.trim().replace(/\n/g, '\n  ')}\n\n`;
    }
    
    // Projections
    report += 'PROJECTIONS:\n';
    report += `  Projected Income: $${entry.projections.income.toFixed(2)}\n`;
    report += `  Projected Investing: $${entry.projections.categories.investing.toFixed(2)}\n`;
    report += `  Projected Saving: $${entry.projections.categories.saving.toFixed(2)}\n`;
    report += `  Projected Spending: $${entry.projections.categories.spending.toFixed(2)}\n\n`;
    
    report += '\n'; // Extra line between months
  });
  
  return report;
};

module.exports = {
  parseRawBudgetData,
  generateBudgetReport
};
