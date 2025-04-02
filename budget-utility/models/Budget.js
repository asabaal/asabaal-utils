const BudgetEntry = require('./BudgetEntry');

/**
 * Budget class manages a collection of BudgetEntry objects
 */
class Budget {
  constructor() {
    this.entries = {};
  }

  /**
   * Get a budget entry for a specific month and year
   * Creates a new entry if one doesn't exist
   * @param {string} month - Month name
   * @param {number} year - Year
   * @returns {BudgetEntry} The budget entry
   */
  getEntry(month, year) {
    const key = `${month}-${year}`;
    if (!this.entries[key]) {
      this.entries[key] = new BudgetEntry(month, year);
    }
    return this.entries[key];
  }

  /**
   * Get all budget entries sorted by date
   * @returns {Array} Sorted budget entries
   */
  getAllEntries() {
    const months = [
      'January', 'February', 'March', 'April', 'May', 'June',
      'July', 'August', 'September', 'October', 'November', 'December'
    ];

    return Object.values(this.entries).sort((a, b) => {
      // Sort by year first
      if (a.year !== b.year) {
        return a.year - b.year;
      }
      // Then by month
      return months.indexOf(a.month) - months.indexOf(b.month);
    });
  }

  /**
   * Import data from a simple object representation
   * @param {Object} data - Budget data object
   */
  importFromObject(data) {
    if (!data || !data.entries) return;

    Object.keys(data.entries).forEach(key => {
      const entryData = data.entries[key];
      const [month, year] = key.split('-');
      const entry = this.getEntry(month, parseInt(year));

      // Import account data
      if (entryData.accounts) {
        entryData.accounts.forEach(account => {
          entry.addAccount(account.name, account.amount);
        });
      }

      // Import notes
      if (entryData.notes) {
        entry.addNote(entryData.notes);
      }

      // Import categories
      if (entryData.categories) {
        entry.setCategories(entryData.categories);
      }

      // Import projections
      if (entryData.projections) {
        entry.setProjections(entryData.projections);
      }

      // Force recalculation of totals
      entry.recalculateTotals();
    });
  }

  /**
   * Export the budget to a simple object representation
   * @returns {Object} Budget data object
   */
  exportToObject() {
    return {
      entries: this.entries
    };
  }
}

module.exports = Budget;
