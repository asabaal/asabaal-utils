/**
 * BudgetEntry class represents a single month's budget data
 */
class BudgetEntry {
  constructor(month, year) {
    this.month = month;
    this.year = year;
    this.accounts = [];
    this.notes = '';
    this.categories = {
      investing: 0,
      saving: 0,
      spending: 0,
    };
    this.totals = {
      income: 0,
      categoriesTotal: 0,
      surplus: 0,
    };
    this.percentages = {
      investing: 0,
      saving: 0,
      spending: 0,
    };
    this.projections = {
      income: 0,
      categories: {
        investing: 0,
        saving: 0,
        spending: 0,
      },
    };
  }

  /**
   * Add an account entry to the budget
   * @param {string} name - Account name
   * @param {number} amount - Amount charged
   */
  addAccount(name, amount) {
    this.accounts.push({ name, amount });
    this.recalculateTotals();
  }

  /**
   * Add a note to the budget entry
   * @param {string} note - Note text
   */
  addNote(note) {
    this.notes += note + '\n';
  }

  /**
   * Set category amounts
   * @param {Object} categories - Object with category amounts
   */
  setCategories(categories) {
    if (categories.investing !== undefined) this.categories.investing = categories.investing;
    if (categories.saving !== undefined) this.categories.saving = categories.saving;
    if (categories.spending !== undefined) this.categories.spending = categories.spending;
    this.recalculateTotals();
  }

  /**
   * Set projections for the upcoming month
   * @param {Object} projections - Object with projection data
   */
  setProjections(projections) {
    if (projections.income !== undefined) this.projections.income = projections.income;
    if (projections.categories) {
      if (projections.categories.investing !== undefined) {
        this.projections.categories.investing = projections.categories.investing;
      }
      if (projections.categories.saving !== undefined) {
        this.projections.categories.saving = projections.categories.saving;
      }
      if (projections.categories.spending !== undefined) {
        this.projections.categories.spending = projections.categories.spending;
      }
    }
  }

  /**
   * Recalculate all totals and percentages
   */
  recalculateTotals() {
    // Calculate total income
    this.totals.income = this.accounts.reduce((sum, account) => sum + account.amount, 0);

    // Calculate categories total
    this.totals.categoriesTotal = (
      this.categories.investing +
      this.categories.saving +
      this.categories.spending
    );

    // Calculate surplus/deficit
    this.totals.surplus = this.totals.income - this.totals.categoriesTotal;

    // Calculate percentages if categories total is not zero
    if (this.totals.categoriesTotal > 0) {
      this.percentages.investing = (
        (this.categories.investing / this.totals.categoriesTotal) * 100
      ).toFixed(2);
      this.percentages.saving = (
        (this.categories.saving / this.totals.categoriesTotal) * 100
      ).toFixed(2);
      this.percentages.spending = (
        (this.categories.spending / this.totals.categoriesTotal) * 100
      ).toFixed(2);
    }
  }
}

module.exports = BudgetEntry;
