#!/usr/bin/env node

/**
 * Utility script to load sample data into the main application
 */

const fs = require('fs-extra');
const path = require('path');
const DATA_DIR = path.join(process.cwd(), 'data');
const DEFAULT_DATA_FILE = path.join(DATA_DIR, 'budget-data.json');
const SAMPLE_DATA_FILE = path.join(DATA_DIR, 'sample-budget-data.json');

// Main function
const main = async () => {
  try {
    // Check if sample data exists
    const sampleExists = await fs.pathExists(SAMPLE_DATA_FILE);
    
    if (!sampleExists) {
      console.log('No sample data found. Please run the sample data generator first:');
      console.log('npm run sample');
      return;
    }
    
    // Create data directory if it doesn't exist
    await fs.ensureDir(DATA_DIR);
    
    // Copy sample data to default data file
    await fs.copy(SAMPLE_DATA_FILE, DEFAULT_DATA_FILE);
    
    console.log(`Sample data has been loaded to ${DEFAULT_DATA_FILE}`);
    console.log('You can now run the main application to see the data.');
    
  } catch (error) {
    console.error('Error loading sample data:', error);
  }
};

// Run if called directly
if (require.main === module) {
  main();
}
