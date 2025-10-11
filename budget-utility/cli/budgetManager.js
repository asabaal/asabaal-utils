const path = require('path');
const chalk = require('chalk');
const Budget = require('../models/Budget');
const { 
  saveBudgetData, 
  loadBudgetData,
  exportToCsv 
} = require('../utils/fileOperations');
const { 
  parseRawBudgetData, 
  generateBudgetReport 
} = require('../utils/dataTransformer');
const promptManager = require('./promptManager');

// Default data paths
const DATA_DIR = path.join(process.cwd(), 'data');
const DEFAULT_DATA_FILE = path.join(DATA_DIR, 'budget-data.json');
const DEFAULT_CSV_FILE = path.join(DATA_DIR, 'budget-data.csv');

class BudgetManager {
  constructor() {
    this.budget = new Budget();
    this.dataFile = DEFAULT_DATA_FILE;
  }

  /**
   * Initialize the budget manager
   */
  async initialize() {
    try {
      // Try to load existing data
      const data = await loadBudgetData(this.dataFile);
      if (data) {
        this.budget.importFromObject(data);
      }
    } catch (error) {
      console.error('Error initializing budget manager:', error);
    }
  }

  /**
   * Run the budget utility CLI
   */
  async run() {
    try {
      await this.initialize();

      let running = true;
      console.log(chalk.green('\nWelcome to the Budget Utility!\n'));

      while (running) {
        const action = await promptManager.showMainMenu();

        switch (action) {
          case 'viewReport':
            await this.viewReport();
            break;

          case 'addEntry':
            await this.addEntry();
            break;

          case 'editEntry':
            await this.editEntry();
            break;

          case 'addProjections':
            await this.addProjections();
            break;

          case 'importData':
            await this.importData();
            break;

          case 'exportCsv':
            await this.exportToCsv();
            break;

          case 'exit':
            running = false;
            console.log(chalk.blue('\nThank you for using the Budget Utility. Goodbye!\n'));
            break;

          default:
            console.log(chalk.red('\nInvalid action selected.\n'));
        }
      }
    } catch (error) {
      console.error('Error running budget utility:', error);
    }
  }

  /**
   * Save the current budget data
   */
  async saveData() {
    try {
      const data = this.budget.exportToObject();
      await saveBudgetData(data, this.dataFile);
    } catch (error) {
      console.error('Error saving budget data:', error);
    }
  }

  /**
   * View the monthly budget report
   */
  async viewReport() {
    const report = generateBudgetReport(this.budget);
    await promptManager.displayReport(report);
  }

  /**
   * Add a new budget entry
   */
  async addEntry() {
    try {
      // Get month and year
      const { month, year } = await promptManager.getMonthYearInput('Select month and year for the new entry');

      // Get entry details
      const { accounts, categories, notes } = await promptManager.getBudgetEntryDetails();

      // Create or update the entry
      const entry = this.budget.getEntry(month, year);

      // Clear existing accounts (in case we're updating)
      entry.accounts = [];

      // Add accounts
      accounts.forEach(account => {
        entry.addAccount(account.name, account.amount);
      });

      // Set categories
      entry.setCategories(categories);

      // Set notes
      entry.notes = notes;

      // Force recalculation
      entry.recalculateTotals();

      // Save data
      await this.saveData();

      console.log(chalk.green(`\nBudget entry for ${month} ${year} has been saved.\n`));
    } catch (error) {
      console.error('Error adding budget entry:', error);
    }
  }

  /**
   * Edit an existing budget entry
   */
  async editEntry() {
    try {
      // Get all entries
      const entries = this.budget.getAllEntries();

      if (entries.length === 0) {
        console.log(chalk.yellow('\nNo budget entries found. Please add an entry first.\n'));
        return;
      }

      // Create choices for selection
      const entryChoices = entries.map(entry => ({
        name: `${entry.month} ${entry.year}`,
        value: `${entry.month}-${entry.year}`,
      }));

      // Add a cancel option
      entryChoices.push({ name: 'Cancel', value: 'cancel' });

      // Get user selection
      const { entryKey } = await promptManager.prompt([
        {
          type: 'list',
          name: 'entryKey',
          message: 'Select a budget entry to edit:',
          choices: entryChoices,
        },
      ]);

      if (entryKey === 'cancel') {
        return;
      }

      // Extract month and year from the key
      const [month, year] = entryKey.split('-');

      // Now proceed similar to addEntry but with the selected entry
      const { accounts, categories, notes } = await promptManager.getBudgetEntryDetails();

      // Get the entry
      const entry = this.budget.getEntry(month, parseInt(year));

      // Clear existing accounts
      entry.accounts = [];

      // Add accounts
      accounts.forEach(account => {
        entry.addAccount(account.name, account.amount);
      });

      // Set categories
      entry.setCategories(categories);

      // Set notes
      entry.notes = notes;

      // Force recalculation
      entry.recalculateTotals();

      // Save data
      await this.saveData();

      console.log(chalk.green(`\nBudget entry for ${month} ${year} has been updated.\n`));
    } catch (error) {
      console.error('Error editing budget entry:', error);
    }
  }

  /**
   * Add projections for an upcoming month
   */
  async addProjections() {
    try {
      // Get month and year
      const { month, year } = await promptManager.getMonthYearInput('Select month and year for projections');

      // Get projection details
      const projections = await promptManager.getProjectionDetails();

      // Create or update the entry
      const entry = this.budget.getEntry(month, year);

      // Set projections
      entry.setProjections(projections);

      // Save data
      await this.saveData();

      console.log(chalk.green(`\nProjections for ${month} ${year} have been saved.\n`));
    } catch (error) {
      console.error('Error adding projections:', error);
    }
  }

  /**
   * Import budget data from raw text
   */
  async importData() {
    try {
      // Get raw data
      const rawData = await promptManager.getRawBudgetData();

      // Parse the raw data
      const parsedData = parseRawBudgetData(rawData);

      // Import into budget
      this.budget.importFromObject(parsedData);

      // Save data
      await this.saveData();

      console.log(chalk.green('\nBudget data has been imported successfully.\n'));
    } catch (error) {
      console.error('Error importing budget data:', error);
    }
  }

  /**
   * Export budget data to CSV
   */
  async exportToCsv() {
    try {
      await exportToCsv(this.budget, DEFAULT_CSV_FILE);
      console.log(chalk.green(`\nBudget data has been exported to ${DEFAULT_CSV_FILE}\n`));
    } catch (error) {
      console.error('Error exporting to CSV:', error);
    }
  }
}

module.exports = BudgetManager;
