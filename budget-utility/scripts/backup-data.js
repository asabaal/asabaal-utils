#!/usr/bin/env node

/**
 * Utility script to backup budget data
 */

const fs = require('fs-extra');
const path = require('path');
const dateFns = require('date-fns');

const DATA_DIR = path.join(process.cwd(), 'data');
const DEFAULT_DATA_FILE = path.join(DATA_DIR, 'budget-data.json');
const BACKUP_DIR = path.join(DATA_DIR, 'backups');

// Main function
const main = async () => {
  try {
    // Check if data directory exists
    const dataExists = await fs.pathExists(DATA_DIR);
    
    if (!dataExists) {
      console.log('No data directory found. Nothing to backup.');
      return;
    }
    
    // Check if the data file exists
    const fileExists = await fs.pathExists(DEFAULT_DATA_FILE);
    
    if (!fileExists) {
      console.log('No budget data file found. Nothing to backup.');
      return;
    }
    
    // Create backup directory if it doesn't exist
    await fs.ensureDir(BACKUP_DIR);
    
    // Create a timestamped filename
    const timestamp = dateFns.format(new Date(), 'yyyyMMdd-HHmmss');
    const backupFile = path.join(BACKUP_DIR, `budget-data-${timestamp}.json`);
    
    // Copy the file
    await fs.copy(DEFAULT_DATA_FILE, backupFile);
    
    console.log(`Budget data has been backed up to: ${backupFile}`);
    
  } catch (error) {
    console.error('Error backing up data:', error);
  }
};

// Run if called directly
if (require.main === module) {
  main();
}
