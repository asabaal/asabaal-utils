const fs = require('fs-extra');
const path = require('path');

/**
 * Ensure the data directory exists
 * @param {string} dataDir - Path to data directory
 */
const ensureDataDir = async (dataDir) => {
  try {
    await fs.ensureDir(dataDir);
  } catch (error) {
    console.error('Error creating data directory:', error);
    throw error;
  }
};

/**
 * Save budget data to a JSON file
 * @param {Object} data - Budget data to save
 * @param {string} filePath - Path to save the file
 */
const saveBudgetData = async (data, filePath) => {
  try {
    // Make sure the directory exists
    await ensureDataDir(path.dirname(filePath));
    
    // Write the data to file
    await fs.writeJson(filePath, data, { spaces: 2 });
    console.log(`Budget data saved to ${filePath}`);
  } catch (error) {
    console.error('Error saving budget data:', error);
    throw error;
  }
};

/**
 * Load budget data from a JSON file
 * @param {string} filePath - Path to the file
 * @returns {Object} The loaded budget data
 */
const loadBudgetData = async (filePath) => {
  try {
    // Check if the file exists
    if (await fs.pathExists(filePath)) {
      // Read and parse the file
      const data = await fs.readJson(filePath);
      console.log(`Budget data loaded from ${filePath}`);
      return data;
    } else {
      console.log(`No existing budget data found at ${filePath}`);
      return null;
    }
  } catch (error) {
    console.error('Error loading budget data:', error);
    throw error;
  }
};

/**
 * Export budget data to CSV format
 * @param {Object} budget - Budget object
 * @param {string} filePath - Path to save the CSV file
 */
const exportToCsv = async (budget, filePath) => {
  try {
    // Get all budget entries
    const entries = budget.getAllEntries();
    
    // Create CSV header
    let csvContent = 'Month,Year,Account,Amount,Notes,Investing,Saving,Spending,Total Income,Categories Total,Surplus/Deficit,Investing %,Saving %,Spending %,Projected Income,Projected Investing,Projected Saving,Projected Spending\n';
    
    // Add data for each entry
    entries.forEach(entry => {
      const baseData = [
        entry.month,
        entry.year,
        '',  // Account placeholder
        '',  // Amount placeholder
        entry.notes.replace(/\n/g, ' '),
        entry.categories.investing,
        entry.categories.saving,
        entry.categories.spending,
        entry.totals.income,
        entry.totals.categoriesTotal,
        entry.totals.surplus,
        entry.percentages.investing,
        entry.percentages.saving,
        entry.percentages.spending,
        entry.projections.income,
        entry.projections.categories.investing,
        entry.projections.categories.saving,
        entry.projections.categories.spending
      ];
      
      // If there are accounts, add a row for each account
      if (entry.accounts.length > 0) {
        entry.accounts.forEach((account, index) => {
          const rowData = [...baseData];
          rowData[2] = account.name;  // Set account name
          rowData[3] = account.amount;  // Set account amount
          
          // Only include category data in the first row for this month
          if (index > 0) {
            for (let i = 5; i < rowData.length; i++) {
              rowData[i] = '';  // Clear category data for additional account rows
            }
          }
          
          csvContent += rowData.join(',') + '\n';
        });
      } else {
        // If no accounts, just add the base data
        csvContent += baseData.join(',') + '\n';
      }
    });
    
    // Write to file
    await ensureDataDir(path.dirname(filePath));
    await fs.writeFile(filePath, csvContent);
    console.log(`Budget data exported to CSV at ${filePath}`);
  } catch (error) {
    console.error('Error exporting to CSV:', error);
    throw error;
  }
};

module.exports = {
  ensureDataDir,
  saveBudgetData,
  loadBudgetData,
  exportToCsv
};
