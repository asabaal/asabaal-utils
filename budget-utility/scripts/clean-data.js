#!/usr/bin/env node

/**
 * Utility script to clean/reset budget data
 */

const fs = require('fs-extra');
const path = require('path');
const inquirer = require('inquirer');

const DATA_DIR = path.join(process.cwd(), 'data');
const DEFAULT_DATA_FILE = path.join(DATA_DIR, 'budget-data.json');

// Main function
const main = async () => {
  try {
    // Check if data directory exists
    const dataExists = await fs.pathExists(DATA_DIR);
    
    if (!dataExists) {
      console.log('No data directory found. Nothing to clean.');
      return;
    }
    
    // Check if the data file exists
    const fileExists = await fs.pathExists(DEFAULT_DATA_FILE);
    
    if (!fileExists) {
      console.log('No budget data file found. Nothing to clean.');
      return;
    }
    
    // Ask for confirmation
    const { confirm } = await inquirer.prompt([
      {
        type: 'confirm',
        name: 'confirm',
        message: 'This will delete your budget data. Are you sure?',
        default: false,
      },
    ]);
    
    if (!confirm) {
      console.log('Operation cancelled.');
      return;
    }
    
    // Delete the file
    await fs.remove(DEFAULT_DATA_FILE);
    console.log('Budget data has been cleaned.');
    
  } catch (error) {
    console.error('Error cleaning data:', error);
  }
};

// Run if called directly
if (require.main === module) {
  main();
}
