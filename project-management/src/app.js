/**
 * Main Application Class
 * Orchestrates all components of the project management system
 */

const path = require('path');
const Storage = require('./utils/storage');
const ProjectRepository = require('./repositories/projectRepository');
const TaskRepository = require('./repositories/taskRepository');
const ProjectService = require('./services/projectService');
const ReminderService = require('./services/reminderService');
const NotificationService = require('./services/notificationService');

class ProjectManagementApp {
  constructor(options = {}) {
    // Set up configuration
    this.config = {
      dataDir: options.dataDir || path.join(process.cwd(), 'data'),
      reminderCheckInterval: options.reminderCheckInterval || 3600000, // 1 hour
      ...options
    };
    
    // Initialize storage
    this.storage = new Storage({
      dataDir: this.config.dataDir
    });
    
    // Initialize repositories
    this.projectRepository = new ProjectRepository(this.storage);
    this.taskRepository = new TaskRepository(this.storage);
    
    // Initialize services
    this.notificationService = new NotificationService({
      channels: this.config.notificationChannels || ['console']
    });
    
    this.projectService = new ProjectService(
      this.projectRepository,
      this.taskRepository
    );
    
    this.reminderService = new ReminderService(
      this.taskRepository,
      this.projectRepository,
      this.notificationService
    );
    
    // Reminder check timer
    this.reminderCheckTimer = null;
  }

  /**
   * Initialize the application
   */
  async init() {
    try {
      // Initialize storage
      await this.storage.init();
      
      // Initialize repositories
      await this.projectRepository.init();
      await this.taskRepository.init();
      
      console.log('Project Management System initialized successfully.');
      return true;
    } catch (error) {
      console.error('Failed to initialize application:', error);
      throw error;
    }
  }

  /**
   * Start the reminder check service
   */
  startReminderChecks() {
    if (this.reminderCheckTimer) {
      clearInterval(this.reminderCheckTimer);
    }
    
    this.reminderCheckTimer = setInterval(async () => {
      try {
        const results = await this.reminderService.checkReminders();
        console.log('Reminder check completed:', results);
      } catch (error) {
        console.error('Reminder check failed:', error);
      }
    }, this.config.reminderCheckInterval);
    
    console.log(`Reminder checks started. Will check every ${this.config.reminderCheckInterval / 60000} minutes.`);
  }

  /**
   * Stop the reminder check service
   */
  stopReminderChecks() {
    if (this.reminderCheckTimer) {
      clearInterval(this.reminderCheckTimer);
      this.reminderCheckTimer = null;
      console.log('Reminder checks stopped.');
    }
  }

  /**
   * Configure notification channels
   * @param {Object} config - Notification configuration
   */
  configureNotifications(config) {
    this.notificationService.configure(config);
  }

  /**
   * Get the project service
   * @returns {ProjectService} Project service instance
   */
  getProjectService() {
    return this.projectService;
  }

  /**
   * Get the reminder service
   * @returns {ReminderService} Reminder service instance
   */
  getReminderService() {
    return this.reminderService;
  }

  /**
   * Get the notification service
   * @returns {NotificationService} Notification service instance
   */
  getNotificationService() {
    return this.notificationService;
  }

  /**
   * Seed initial data
   * @param {Object} seedData - Initial data to seed
   */
  async seedData(seedData) {
    try {
      // Seed projects
      if (seedData.projects && Array.isArray(seedData.projects)) {
        for (const projectData of seedData.projects) {
          await this.projectRepository.create(projectData);
        }
      }
      
      // Seed tasks
      if (seedData.tasks && Array.isArray(seedData.tasks)) {
        for (const taskData of seedData.tasks) {
          await this.taskRepository.create(taskData);
        }
      }
      
      console.log('Data seeded successfully.');
      return true;
    } catch (error) {
      console.error('Failed to seed data:', error);
      throw error;
    }
  }

  /**
   * Get dashboard summary
   * @returns {Promise<Object>} Dashboard data
   */
  async getDashboardSummary() {
    return await this.projectService.getDashboardSummary();
  }

  /**
   * Export all data
   * @returns {Promise<Object>} All system data
   */
  async exportData() {
    try {
      const projects = await this.projectRepository.getAll();
      const tasks = await this.taskRepository.getAll();
      
      return {
        projects,
        tasks,
        exportedAt: new Date().toISOString()
      };
    } catch (error) {
      console.error('Failed to export data:', error);
      throw error;
    }
  }

  /**
   * Import data
   * @param {Object} data - Data to import
   */
  async importData(data) {
    try {
      // Clear existing data
      const collections = await this.storage.listCollections();
      for (const collection of collections) {
        await this.storage.delete(collection);
      }
      
      // Re-initialize repositories
      await this.projectRepository.init();
      await this.taskRepository.init();
      
      // Import data
      if (data.projects && Array.isArray(data.projects)) {
        await this.storage.save('projects', data.projects);
      }
      
      if (data.tasks && Array.isArray(data.tasks)) {
        await this.storage.save('tasks', data.tasks);
      }
      
      console.log('Data imported successfully.');
      return true;
    } catch (error) {
      console.error('Failed to import data:', error);
      throw error;
    }
  }
}

module.exports = ProjectManagementApp;
