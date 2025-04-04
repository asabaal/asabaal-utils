/**
 * Project Management System
 * Main entry point and module exports
 */

const ProjectManagementApp = require('./app');
const { 
  Project, 
  Task, 
  Timeline,
  PROJECT_CATEGORIES,
  PROJECT_STATUS,
  TASK_PRIORITY,
  TASK_STATUS
} = require('./models');
const Storage = require('./utils/storage');
const ProjectRepository = require('./repositories/projectRepository');
const TaskRepository = require('./repositories/taskRepository');
const ProjectService = require('./services/projectService');
const ReminderService = require('./services/reminderService');
const NotificationService = require('./services/notificationService');

// Export all components
module.exports = {
  ProjectManagementApp,
  
  // Models
  Project,
  Task,
  Timeline,
  PROJECT_CATEGORIES,
  PROJECT_STATUS,
  TASK_PRIORITY,
  TASK_STATUS,
  
  // Utilities
  Storage,
  
  // Repositories
  ProjectRepository,
  TaskRepository,
  
  // Services
  ProjectService,
  ReminderService,
  NotificationService
};

/**
 * Usage Example:
 * 
 * -------------------------------------------------------
 * const {
 *   ProjectManagementApp,
 *   PROJECT_CATEGORIES
 * } = require('./index');
 * 
 * async function main() {
 *   // Initialize the application
 *   const app = new ProjectManagementApp({
 *     dataDir: './data',
 *     notificationChannels: ['console']
 *   });
 *   
 *   await app.init();
 *   
 *   // Get the project service
 *   const projectService = app.getProjectService();
 *   
 *   // Create a new project with tasks
 *   const result = await projectService.createProject(
 *     {
 *       name: 'Dapper Demos Vol. 3 EP',
 *       description: 'Content cycle for EP released in February',
 *       category: PROJECT_CATEGORIES.MUSIC_PRODUCTION,
 *       startDate: '2025-06-01',
 *       endDate: '2025-07-31'
 *     },
 *     [
 *       {
 *         name: 'Create social media content plan',
 *         description: 'Develop schedule for content promotion',
 *         priority: 'high',
 *         dueDate: '2025-06-05'
 *       },
 *       {
 *         name: 'Design promotional assets',
 *         description: 'Create visuals for social media',
 *         priority: 'medium',
 *         dueDate: '2025-06-10'
 *       }
 *     ]
 *   );
 *   
 *   console.log('Created project:', result.project.name);
 *   console.log('Created tasks:', result.tasks.length);
 *   
 *   // Start reminder checks
 *   app.startReminderChecks();
 *   
 *   // Get dashboard summary
 *   const summary = await app.getDashboardSummary();
 *   console.log('Dashboard Summary:', summary);
 * }
 * 
 * main().catch(console.error);
 * -------------------------------------------------------
 */
