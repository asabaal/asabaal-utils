/**
 * This utility loads sample budget data based on the provided example
 */

const Budget = require('../models/Budget');
const { saveBudgetData } = require('../utils/fileOperations');
const path = require('path');

// Sample data from the example
const sampleData = `
**MonthCharged OnAmountNOTES***extra added*Amount/PercentMarch 2025STCU1794.82
There is a VERY large We Energies Charge - I should call them
817.79LOWER TOTALInvestingSavingSpending**TOTAL**March 2025Wells Fargo1037.13
SURPLUS/DEFECIT
2014.16$211.25$192.04$174.58$577.87**TOTAL**2831.95-239.92
Adjusted SURPLUS/DEFECIT
577.8736.56%33.23%30.21%100.00%
`;

// Function to create sample data
const createSampleData = () => {
  const budget = new Budget();

  // Create March 2025 entry
  const marchEntry = budget.getEntry('March', 2025);
  
  // Add accounts
  marchEntry.addAccount('STCU', 1794.82);
  marchEntry.addAccount('Wells Fargo', 1037.13);
  
  // Add categories
  marchEntry.setCategories({
    investing: 211.25,
    saving: 192.04,
    spending: 174.58
  });
  
  // Add note
  marchEntry.addNote('There is a VERY large We Energies Charge - I should call them');
  
  // Add projections for April 2025
  const aprilEntry = budget.getEntry('April', 2025);
  aprilEntry.setProjections({
    income: 2900.00,
    categories: {
      investing: 250.00,
      saving: 210.00,
      spending: 180.00
    }
  });

  return budget;
};

// Main function
const main = async () => {
  try {
    console.log('Creating sample budget data...');
    
    const budget = createSampleData();
    
    // Save to a sample file
    const dataFile = path.join(process.cwd(), 'data', 'sample-budget-data.json');
    await saveBudgetData(budget.exportToObject(), dataFile);
    
    console.log(`Sample data has been saved to ${dataFile}`);
    console.log('You can load this data in the main application or use it as a reference.');
  } catch (error) {
    console.error('Error creating sample data:', error);
  }
};

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = { createSampleData };
