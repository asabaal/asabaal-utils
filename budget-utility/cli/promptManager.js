const inquirer = require('inquirer');
const chalk = require('chalk');

/**
 * Show the main menu and get user selection
 * @returns {Promise<string>} Selected action
 */
const showMainMenu = async () => {
  const { action } = await inquirer.prompt([
    {
      type: 'list',
      name: 'action',
      message: 'Budget Utility - What would you like to do?',
      choices: [
        { name: 'View monthly budget report', value: 'viewReport' },
        { name: 'Add new budget entry', value: 'addEntry' },
        { name: 'Edit existing budget entry', value: 'editEntry' },
        { name: 'Add projections for upcoming month', value: 'addProjections' },
        { name: 'Import budget data', value: 'importData' },
        { name: 'Export budget data to CSV', value: 'exportCsv' },
        { name: 'Exit', value: 'exit' },
      ],
    },
  ]);

  return action;
};

/**
 * Get month and year input from the user
 * @returns {Promise<Object>} Object with month and year
 */
const getMonthYearInput = async (message = 'Select month and year') => {
  const months = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  const currentYear = new Date().getFullYear();
  const yearChoices = Array.from({ length: 5 }, (_, i) => currentYear - 2 + i);

  const answers = await inquirer.prompt([
    {
      type: 'list',
      name: 'month',
      message: 'Select month:',
      choices: months,
    },
    {
      type: 'list',
      name: 'year',
      message: 'Select year:',
      choices: yearChoices,
      default: currentYear,
    },
  ]);

  return {
    month: answers.month,
    year: parseInt(answers.year),
  };
};

/**
 * Get budget entry details from the user
 * @returns {Promise<Object>} Budget entry details
 */
const getBudgetEntryDetails = async () => {
  // Get accounts information
  const getAccounts = async () => {
    const accounts = [];
    let addMore = true;

    while (addMore) {
      const accountAnswers = await inquirer.prompt([
        {
          type: 'input',
          name: 'name',
          message: 'Account name:',
          validate: input => input.trim() !== '' ? true : 'Account name cannot be empty',
        },
        {
          type: 'number',
          name: 'amount',
          message: 'Amount:',
          validate: input => !isNaN(input) && input >= 0 ? true : 'Please enter a valid amount',
        },
      ]);

      accounts.push({
        name: accountAnswers.name,
        amount: parseFloat(accountAnswers.amount),
      });

      const { addMoreAccounts } = await inquirer.prompt([
        {
          type: 'confirm',
          name: 'addMoreAccounts',
          message: 'Add another account?',
          default: false,
        },
      ]);

      addMore = addMoreAccounts;
    }

    return accounts;
  };

  // Get category information
  const getCategories = async (totalIncome) => {
    console.log(chalk.blue(`\nTotal Income: $${totalIncome.toFixed(2)}`));
    console.log(chalk.yellow('Now let\'s allocate this income to categories:\n'));

    const categoryAnswers = await inquirer.prompt([
      {
        type: 'number',
        name: 'investing',
        message: 'Amount for Investing:',
        validate: input => !isNaN(input) && input >= 0 ? true : 'Please enter a valid amount',
      },
      {
        type: 'number',
        name: 'saving',
        message: 'Amount for Saving:',
        validate: input => !isNaN(input) && input >= 0 ? true : 'Please enter a valid amount',
      },
      {
        type: 'number',
        name: 'spending',
        message: 'Amount for Spending:',
        validate: input => !isNaN(input) && input >= 0 ? true : 'Please enter a valid amount',
      },
    ]);

    return {
      investing: parseFloat(categoryAnswers.investing),
      saving: parseFloat(categoryAnswers.saving),
      spending: parseFloat(categoryAnswers.spending),
    };
  };

  // Get notes
  const getNotes = async () => {
    const { notes } = await inquirer.prompt([
      {
        type: 'editor',
        name: 'notes',
        message: 'Enter any notes (opens in your default text editor):',
      },
    ]);

    return notes;
  };

  // Get all data
  console.log(chalk.green('\nLet\'s add the accounts for this budget entry:\n'));
  const accounts = await getAccounts();

  // Calculate total income
  const totalIncome = accounts.reduce((sum, account) => sum + account.amount, 0);

  const categories = await getCategories(totalIncome);
  const notes = await getNotes();

  return {
    accounts,
    categories,
    notes,
  };
};

/**
 * Get projection details from the user
 * @returns {Promise<Object>} Projection details
 */
const getProjectionDetails = async () => {
  const { projectedIncome } = await inquirer.prompt([
    {
      type: 'number',
      name: 'projectedIncome',
      message: 'Projected income for the month:',
      validate: input => !isNaN(input) && input >= 0 ? true : 'Please enter a valid amount',
    },
  ]);

  const income = parseFloat(projectedIncome);

  console.log(chalk.blue(`\nProjected Income: $${income.toFixed(2)}`));
  console.log(chalk.yellow('Now let\'s allocate this projected income to categories:\n'));

  const categoryAnswers = await inquirer.prompt([
    {
      type: 'number',
      name: 'investing',
      message: 'Projected amount for Investing:',
      validate: input => !isNaN(input) && input >= 0 ? true : 'Please enter a valid amount',
    },
    {
      type: 'number',
      name: 'saving',
      message: 'Projected amount for Saving:',
      validate: input => !isNaN(input) && input >= 0 ? true : 'Please enter a valid amount',
    },
    {
      type: 'number',
      name: 'spending',
      message: 'Projected amount for Spending:',
      validate: input => !isNaN(input) && input >= 0 ? true : 'Please enter a valid amount',
    },
  ]);

  return {
    income,
    categories: {
      investing: parseFloat(categoryAnswers.investing),
      saving: parseFloat(categoryAnswers.saving),
      spending: parseFloat(categoryAnswers.spending),
    },
  };
};

/**
 * Display monthly budget report
 * @param {string} report - Formatted report string
 */
const displayReport = async (report) => {
  console.log(chalk.green('\n=== Monthly Budget Report ===\n'));
  console.log(report);

  await inquirer.prompt([
    {
      type: 'input',
      name: 'continue',
      message: 'Press Enter to continue...',
    },
  ]);
};

/**
 * Get raw budget data input
 * @returns {Promise<string>} Raw budget data
 */
const getRawBudgetData = async () => {
  const { data } = await inquirer.prompt([
    {
      type: 'editor',
      name: 'data',
      message: 'Enter or paste your raw budget data (opens in your default text editor):',
    },
  ]);

  return data;
};

module.exports = {
  showMainMenu,
  getMonthYearInput,
  getBudgetEntryDetails,
  getProjectionDetails,
  displayReport,
  getRawBudgetData,
};
