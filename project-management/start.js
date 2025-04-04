#!/usr/bin/env node

/**
 * Project Management System Starter
 * Initializes the system and starts the web server
 */

const path = require('path');
const { startServer } = require('./src/web/server');
const { ProjectManagementApp } = require('./src/index');
const seedDatabase = require('./scripts/seed-data');

// Configuration
const config = {
  dataDir: path.join(__dirname, 'data'),
  port: process.env.PORT || 3000,
  host: process.env.HOST || 'localhost'
};

/**
 * Main function to start the application
 */
async function main() {
  try {
    console.log('Starting Asabaal Music Business Project Management System...');
    
    // Initialize the core app
    const app = new ProjectManagementApp({
      dataDir: config.dataDir
    });
    
    await app.init();
    console.log('Core system initialized successfully');
    
    // Check if we need to seed data
    if (process.argv.includes('--seed')) {
      console.log('Seeding initial data...');
      await seedDatabase();
      console.log('Data seeded successfully');
    }
    
    // Start the web server
    const server = await startServer();
    
    console.log(`Server running at http://${config.host}:${config.port}`);
    console.log('Press Ctrl+C to stop');
    
    // Handle graceful shutdown
    process.on('SIGINT', async () => {
      console.log('\nShutting down...');
      server.close();
      process.exit(0);
    });
  } catch (error) {
    console.error('Failed to start application:', error);
    process.exit(1);
  }
}

// Run the main function
main();
