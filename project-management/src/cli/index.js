#!/usr/bin/env node

/**
 * CLI Interface for Project Management System
 */

const { program } = require('commander');
const inquirer = require('inquirer');
const chalk = require('chalk');
const path = require('path');
const fs = require('fs').promises;
const { 
  ProjectManagementApp,
  PROJECT_CATEGORIES,
  PROJECT_STATUS,
  TASK_PRIORITY,
  TASK_STATUS
} = require('../index');

// Initialize the app
const app = new ProjectManagementApp({
  dataDir: path.join(process.cwd(), 'data')
});

// Setup CLI
program
  .name('project-management')
  .description('Music Business Project Management CLI')
  .version('1.0.0');

// Initialize command
program
  .command('init')
  .description('Initialize the project management system')
  .action(async () => {
    try {
      await app.init();
      console.log(chalk.green('✓ Project management system initialized successfully.'));
    } catch (error) {
      console.error(chalk.red('Failed to initialize:'), error);
      process.exit(1);
    }
  });

// Project commands
program
  .command('project')
  .description('Project management commands')
  .option('-l, --list', 'List all projects')
  .option('-c, --create', 'Create a new project')
  .option('-g, --get <id>', 'Get project by ID')
  .option('-u, --update <id>', 'Update project by ID')
  .option('-d, --delete <id>', 'Delete project by ID')
  .option('-s, --status <id>', 'Get project status')
  .action(async (options) => {
    try {
      await app.init();
      const projectService = app.getProjectService();
      
      if (options.list) {
        // List all projects
        const projects = await projectService.projectRepository.getAll();
        
        if (projects.length === 0) {
          console.log(chalk.yellow('No projects found.'));
          return;
        }
        
        console.log(chalk.bold('\nProjects:'));
        projects.forEach(project => {
          const status = getStatusColor(project.status);
          console.log(`  ${chalk.cyan(project.id)} - ${chalk.white(project.name)} [${status}]`);
          console.log(`    ${chalk.gray(project.description)}`);
          console.log(`    ${chalk.gray(`${project.startDate} to ${project.endDate}`)}`);
          console.log();
        });
      } 
      else if (options.create) {
        // Create a new project
        const projectData = await promptForProject();
        const tasksData = await promptForTasks();
        
        const result = await projectService.createProject(projectData, tasksData);
        
        console.log(chalk.green(`✓ Project created: ${result.project.name}`));
        console.log(chalk.green(`✓ ${result.tasks.length} task(s) created`));
      } 
      else if (options.get) {
        // Get project by ID
        const result = await projectService.getProjectWithTasks(options.get);
        
        if (!result) {
          console.log(chalk.red(`Project with ID ${options.get} not found.`));
          return;
        }
        
        const { project, tasks } = result;
        const status = getStatusColor(project.status);
        
        console.log(chalk.bold(`\nProject: ${project.name} [${status}]`));
        console.log(chalk.gray(`ID: ${project.id}`));
        console.log(chalk.gray(`Description: ${project.description}`));
        console.log(chalk.gray(`Category: ${project.category}`));
        console.log(chalk.gray(`Timeline: ${project.startDate} to ${project.endDate}`));
        console.log(chalk.gray(`Revenue Target: $${project.revenue.target}`));
        console.log(chalk.gray(`Revenue Actual: $${project.revenue.actual}`));
        
        console.log(chalk.bold('\nTasks:'));
        if (tasks.length === 0) {
          console.log(chalk.yellow('  No tasks found for this project.'));
        } else {
          tasks.forEach(task => {
            const taskStatus = getTaskStatusColor(task.status);
            const priority = getTaskPriorityColor(task.priority);
            
            console.log(`  ${chalk.cyan(task.id)} - ${chalk.white(task.name)} [${taskStatus}] [${priority}]`);
            console.log(`    ${chalk.gray(task.description)}`);
            if (task.dueDate) {
              console.log(`    ${chalk.gray(`Due: ${task.dueDate}`)}`);
            }
            console.log();
          });
        }
      } 
      else if (options.update) {
        // Update project by ID
        const result = await projectService.getProjectWithTasks(options.update);
        
        if (!result) {
          console.log(chalk.red(`Project with ID ${options.update} not found.`));
          return;
        }
        
        const { project } = result;
        const updatedData = await promptForProject(project);
        
        const updateResult = await projectService.updateProject(options.update, updatedData);
        
        console.log(chalk.green(`✓ Project updated: ${updateResult.project.name}`));
      } 
      else if (options.delete) {
        // Delete project by ID
        const confirm = await inquirer.prompt([
          {
            type: 'confirm',
            name: 'confirm',
            message: `Are you sure you want to delete project with ID ${options.delete}?`,
            default: false
          }
        ]);
        
        if (!confirm.confirm) {
          console.log(chalk.yellow('Delete canceled.'));
          return;
        }
        
        const deleted = await projectService.deleteProject(options.delete);
        
        if (deleted) {
          console.log(chalk.green('✓ Project deleted successfully.'));
        } else {
          console.log(chalk.red(`Project with ID ${options.delete} not found.`));
        }
      } 
      else if (options.status) {
        // Get project status
        const status = await projectService.getProjectStatus(options.status);
        
        if (!status) {
          console.log(chalk.red(`Project with ID ${options.status} not found.`));
          return;
        }
        
        console.log(chalk.bold(`\nProject Status: ${status.project.name}`));
        console.log(chalk.gray(`Progress: ${status.progress}%`));
        console.log(chalk.gray(`On Schedule: ${status.isOnSchedule ? chalk.green('Yes') : chalk.red('No')}`));
        console.log(chalk.bold('\nTask Counts:'));
        console.log(chalk.gray(`  Total: ${status.taskCounts.total}`));
        console.log(chalk.gray(`  To Do: ${status.taskCounts.todo}`));
        console.log(chalk.gray(`  In Progress: ${status.taskCounts.inProgress}`));
        console.log(chalk.gray(`  Review: ${status.taskCounts.review}`));
        console.log(chalk.gray(`  Done: ${status.taskCounts.done}`));
        console.log(chalk.gray(`  Overdue: ${status.overdueTasks}`));
      } 
      else {
        // Show help if no option specified
        program.help();
      }
    } catch (error) {
      console.error(chalk.red('Error:'), error);
      process.exit(1);
    }
  });

// Task commands
program
  .command('task')
  .description('Task management commands')
  .option('-l, --list', 'List all tasks')
  .option('-p, --project <id>', 'List tasks for a project')
  .option('-c, --create', 'Create a new task')
  .option('-g, --get <id>', 'Get task by ID')
  .option('-u, --update <id>', 'Update task by ID')
  .option('-d, --delete <id>', 'Delete task by ID')
  .option('-m, --mark-complete <id>', 'Mark task as complete')
  .option('-o, --overdue', 'List overdue tasks')
  .option('-u, --upcoming [days]', 'List upcoming tasks (default: 7 days)')
  .action(async (options) => {
    try {
      await app.init();
      const taskRepository = app.taskRepository;
      
      if (options.list) {
        // List all tasks
        const tasks = await taskRepository.getAll();
        
        if (tasks.length === 0) {
          console.log(chalk.yellow('No tasks found.'));
          return;
        }
        
        console.log(chalk.bold('\nTasks:'));
        tasks.forEach(task => {
          const status = getTaskStatusColor(task.status);
          const priority = getTaskPriorityColor(task.priority);
          
          console.log(`  ${chalk.cyan(task.id)} - ${chalk.white(task.name)} [${status}] [${priority}]`);
          console.log(`    ${chalk.gray(`Project: ${task.projectId}`)}`);
          if (task.dueDate) {
            console.log(`    ${chalk.gray(`Due: ${task.dueDate}`)}`);
          }
          console.log();
        });
      } 
      else if (options.project) {
        // List tasks for a project
        const tasks = await taskRepository.getTasksByProject(options.project);
        
        if (tasks.length === 0) {
          console.log(chalk.yellow(`No tasks found for project ${options.project}.`));
          return;
        }
        
        console.log(chalk.bold(`\nTasks for project ${options.project}:`));
        tasks.forEach(task => {
          const status = getTaskStatusColor(task.status);
          const priority = getTaskPriorityColor(task.priority);
          
          console.log(`  ${chalk.cyan(task.id)} - ${chalk.white(task.name)} [${status}] [${priority}]`);
          console.log(`    ${chalk.gray(task.description)}`);
          if (task.dueDate) {
            console.log(`    ${chalk.gray(`Due: ${task.dueDate}`)}`);
          }
          console.log();
        });
      } 
      else if (options.create) {
        // Create a new task
        const projectId = await promptForProjectId();
        const taskData = await promptForTask({ projectId });
        
        const task = await taskRepository.create(taskData);
        
        console.log(chalk.green(`✓ Task created: ${task.name}`));
      } 
      else if (options.get) {
        // Get task by ID
        const task = await taskRepository.getById(options.get);
        
        if (!task) {
          console.log(chalk.red(`Task with ID ${options.get} not found.`));
          return;
        }
        
        const status = getTaskStatusColor(task.status);
        const priority = getTaskPriorityColor(task.priority);
        
        console.log(chalk.bold(`\nTask: ${task.name} [${status}] [${priority}]`));
        console.log(chalk.gray(`ID: ${task.id}`));
        console.log(chalk.gray(`Project: ${task.projectId}`));
        console.log(chalk.gray(`Description: ${task.description}`));
        if (task.dueDate) {
          console.log(chalk.gray(`Due Date: ${task.dueDate}`));
        }
        if (task.assignee) {
          console.log(chalk.gray(`Assignee: ${task.assignee}`));
        }
        if (task.dependencies.length > 0) {
          console.log(chalk.gray(`Dependencies: ${task.dependencies.join(', ')}`));
        }
        console.log(chalk.gray(`Created: ${task.createdAt}`));
        console.log(chalk.gray(`Updated: ${task.updatedAt}`));
      } 
      else if (options.update) {
        // Update task by ID
        const task = await taskRepository.getById(options.update);
        
        if (!task) {
          console.log(chalk.red(`Task with ID ${options.update} not found.`));
          return;
        }
        
        const updatedData = await promptForTask(task);
        
        const updatedTask = await taskRepository.update(options.update, updatedData);
        
        console.log(chalk.green(`✓ Task updated: ${updatedTask.name}`));
      } 
      else if (options.delete) {
        // Delete task by ID
        const confirm = await inquirer.prompt([
          {
            type: 'confirm',
            name: 'confirm',
            message: `Are you sure you want to delete task with ID ${options.delete}?`,
            default: false
          }
        ]);
        
        if (!confirm.confirm) {
          console.log(chalk.yellow('Delete canceled.'));
          return;
        }
        
        const deleted = await taskRepository.delete(options.delete);
        
        if (deleted) {
          console.log(chalk.green('✓ Task deleted successfully.'));
        } else {
          console.log(chalk.red(`Task with ID ${options.delete} not found.`));
        }
      } 
      else if (options.markComplete) {
        // Mark task as complete
        const task = await taskRepository.getById(options.markComplete);
        
        if (!task) {
          console.log(chalk.red(`Task with ID ${options.markComplete} not found.`));
          return;
        }
        
        const updatedTask = await taskRepository.markAsComplete(options.markComplete);
        
        console.log(chalk.green(`✓ Task marked as complete: ${updatedTask.name}`));
      } 
      else if (options.overdue) {
        // List overdue tasks
        const tasks = await taskRepository.getOverdueTasks();
        
        if (tasks.length === 0) {
          console.log(chalk.green('No overdue tasks found.'));
          return;
        }
        
        console.log(chalk.bold('\nOverdue Tasks:'));
        tasks.forEach(task => {
          const priority = getTaskPriorityColor(task.priority);
          
          console.log(`  ${chalk.cyan(task.id)} - ${chalk.white(task.name)} [${priority}]`);
          console.log(`    ${chalk.gray(`Project: ${task.projectId}`)}`);
          console.log(`    ${chalk.red(`Due: ${task.dueDate}`)}`);
          console.log();
        });
      } 
      else if (options.upcoming !== undefined) {
        // List upcoming tasks
        const days = options.upcoming === true ? 7 : parseInt(options.upcoming);
        const tasks = await taskRepository.getTasksDueInDays(days);
        
        if (tasks.length === 0) {
          console.log(chalk.yellow(`No tasks due in the next ${days} days.`));
          return;
        }
        
        console.log(chalk.bold(`\nTasks due in the next ${days} days:`));
        tasks.forEach(task => {
          const priority = getTaskPriorityColor(task.priority);
          
          console.log(`  ${chalk.cyan(task.id)} - ${chalk.white(task.name)} [${priority}]`);
          console.log(`    ${chalk.gray(`Project: ${task.projectId}`)}`);
          console.log(`    ${chalk.yellow(`Due: ${task.dueDate}`)}`);
          console.log();
        });
      } 
      else {
        // Show help if no option specified
        program.help();
      }
    } catch (error) {
      console.error(chalk.red('Error:'), error);
      process.exit(1);
    }
  });

// Dashboard command
program
  .command('dashboard')
  .description('View project management dashboard')
  .action(async () => {
    try {
      await app.init();
      const summary = await app.getDashboardSummary();
      
      console.log(chalk.bold('\n=== Project Management Dashboard ==='));
      
      // Projects section
      console.log(chalk.bold('\nProjects:'));
      console.log(chalk.gray(`  Total: ${summary.projects.total}`));
      console.log(chalk.gray(`  Active: ${summary.projects.active}`));
      console.log(chalk.gray(`  Completed: ${summary.projects.completed}`));
      
      // Categories section
      console.log(chalk.bold('\nProject Categories:'));
      Object.entries(summary.projects.byCategory).forEach(([category, count]) => {
        console.log(chalk.gray(`  ${category}: ${count}`));
      });
      
      // Tasks section
      console.log(chalk.bold('\nTasks:'));
      console.log(chalk.gray(`  Total: ${summary.tasks.total}`));
      console.log(chalk.gray(`  Completed: ${summary.tasks.completed}`));
      console.log(chalk.gray(`  Overdue: ${summary.tasks.overdue}`));
      console.log(chalk.gray(`  Upcoming (7 days): ${summary.tasks.upcoming}`));
      
      // Priorities section
      console.log(chalk.bold('\nTask Priorities:'));
      console.log(chalk.gray(`  Low: ${summary.tasks.byPriority.low}`));
      console.log(chalk.gray(`  Medium: ${summary.tasks.byPriority.medium}`));
      console.log(chalk.gray(`  High: ${summary.tasks.byPriority.high}`));
      console.log(chalk.gray(`  Urgent: ${summary.tasks.byPriority.urgent}`));
      
      console.log(chalk.gray(`\nLast updated: ${new Date(summary.updated).toLocaleString()}`));
    } catch (error) {
      console.error(chalk.red('Error:'), error);
      process.exit(1);
    }
  });

// Export command
program
  .command('export [filename]')
  .description('Export all data to a JSON file')
  .action(async (filename = 'project-management-export.json') => {
    try {
      await app.init();
      const data = await app.exportData();
      
      await fs.writeFile(filename, JSON.stringify(data, null, 2), 'utf8');
      
      console.log(chalk.green(`✓ Data exported to ${filename}`));
    } catch (error) {
      console.error(chalk.red('Error:'), error);
      process.exit(1);
    }
  });

// Import command
program
  .command('import <filename>')
  .description('Import data from a JSON file')
  .action(async (filename) => {
    try {
      await app.init();
      
      const fileContent = await fs.readFile(filename, 'utf8');
      const data = JSON.parse(fileContent);
      
      await app.importData(data);
      
      console.log(chalk.green(`✓ Data imported from ${filename}`));
    } catch (error) {
      console.error(chalk.red('Error:'), error);
      process.exit(1);
    }
  });

// Helper functions
function getStatusColor(status) {
  switch (status) {
    case 'planned':
      return chalk.blue('Planned');
    case 'in_progress':
      return chalk.yellow('In Progress');
    case 'on_hold':
      return chalk.magenta('On Hold');
    case 'completed':
      return chalk.green('Completed');
    case 'cancelled':
      return chalk.red('Cancelled');
    default:
      return chalk.gray(status);
  }
}

function getTaskStatusColor(status) {
  switch (status) {
    case 'todo':
      return chalk.blue('To Do');
    case 'in_progress':
      return chalk.yellow('In Progress');
    case 'review':
      return chalk.magenta('Review');
    case 'done':
      return chalk.green('Done');
    default:
      return chalk.gray(status);
  }
}

function getTaskPriorityColor(priority) {
  switch (priority) {
    case 'low':
      return chalk.blue('Low');
    case 'medium':
      return chalk.yellow('Medium');
    case 'high':
      return chalk.magenta('High');
    case 'urgent':
      return chalk.red('Urgent');
    default:
      return chalk.gray(priority);
  }
}

async function promptForProject(defaults = {}) {
  const questions = [
    {
      type: 'input',
      name: 'name',
      message: 'Project name:',
      default: defaults.name || '',
      validate: input => input ? true : 'Project name is required'
    },
    {
      type: 'input',
      name: 'description',
      message: 'Project description:',
      default: defaults.description || ''
    },
    {
      type: 'list',
      name: 'category',
      message: 'Project category:',
      choices: Object.values(PROJECT_CATEGORIES),
      default: defaults.category || PROJECT_CATEGORIES.MUSIC_PRODUCTION
    },
    {
      type: 'list',
      name: 'status',
      message: 'Project status:',
      choices: Object.values(PROJECT_STATUS),
      default: defaults.status || PROJECT_STATUS.PLANNED
    },
    {
      type: 'input',
      name: 'startDate',
      message: 'Start date (YYYY-MM-DD):',
      default: defaults.startDate || new Date().toISOString().split('T')[0],
      validate: input => {
        const date = new Date(input);
        return !isNaN(date.getTime()) ? true : 'Invalid date format';
      }
    },
    {
      type: 'input',
      name: 'endDate',
      message: 'End date (YYYY-MM-DD):',
      default: defaults.endDate || '',
      validate: input => {
        if (!input) return true;
        const date = new Date(input);
        return !isNaN(date.getTime()) ? true : 'Invalid date format';
      }
    },
    {
      type: 'input',
      name: 'revenue.target',
      message: 'Revenue target ($):',
      default: defaults.revenue?.target || 0,
      validate: input => {
        const num = parseFloat(input);
        return !isNaN(num) && num >= 0 ? true : 'Invalid number';
      },
      filter: input => parseFloat(input)
    },
    {
      type: 'input',
      name: 'revenue.actual',
      message: 'Revenue actual ($):',
      default: defaults.revenue?.actual || 0,
      validate: input => {
        const num = parseFloat(input);
        return !isNaN(num) && num >= 0 ? true : 'Invalid number';
      },
      filter: input => parseFloat(input)
    },
    {
      type: 'input',
      name: 'tags',
      message: 'Tags (comma-separated):',
      default: defaults.tags?.join(', ') || '',
      filter: input => input.split(',').map(tag => tag.trim()).filter(Boolean)
    }
  ];
  
  const answers = await inquirer.prompt(questions);
  
  // Format revenue object
  answers.revenue = {
    target: answers.revenue.target,
    actual: answers.revenue.actual,
    currency: 'USD'
  };
  
  return answers;
}

async function promptForTasks() {
  const tasks = [];
  let addMore = true;
  
  while (addMore) {
    const task = await promptForTask();
    tasks.push(task);
    
    const answer = await inquirer.prompt([
      {
        type: 'confirm',
        name: 'addMore',
        message: 'Add another task?',
        default: false
      }
    ]);
    
    addMore = answer.addMore;
  }
  
  return tasks;
}

async function promptForTask(defaults = {}) {
  const questions = [
    {
      type: 'input',
      name: 'name',
      message: 'Task name:',
      default: defaults.name || '',
      validate: input => input ? true : 'Task name is required'
    },
    {
      type: 'input',
      name: 'description',
      message: 'Task description:',
      default: defaults.description || ''
    },
    {
      type: 'list',
      name: 'priority',
      message: 'Task priority:',
      choices: Object.values(TASK_PRIORITY),
      default: defaults.priority || TASK_PRIORITY.MEDIUM
    },
    {
      type: 'list',
      name: 'status',
      message: 'Task status:',
      choices: Object.values(TASK_STATUS),
      default: defaults.status || TASK_STATUS.TODO
    },
    {
      type: 'input',
      name: 'dueDate',
      message: 'Due date (YYYY-MM-DD):',
      default: defaults.dueDate || '',
      validate: input => {
        if (!input) return true;
        const date = new Date(input);
        return !isNaN(date.getTime()) ? true : 'Invalid date format';
      }
    },
    {
      type: 'input',
      name: 'assignee',
      message: 'Assignee:',
      default: defaults.assignee || ''
    },
    {
      type: 'input',
      name: 'dependencies',
      message: 'Dependencies (comma-separated task IDs):',
      default: defaults.dependencies?.join(', ') || '',
      filter: input => input.split(',').map(id => id.trim()).filter(Boolean)
    }
  ];
  
  // If projectId not provided, prompt for it
  if (!defaults.projectId) {
    const projectId = await promptForProjectId();
    defaults.projectId = projectId;
  }
  
  const answers = await inquirer.prompt(questions);
  
  // Add projectId
  answers.projectId = defaults.projectId;
  
  return answers;
}

async function promptForProjectId() {
  try {
    const projectRepository = app.projectRepository;
    await app.init();
    
    const projects = await projectRepository.getAll();
    
    if (projects.length === 0) {
      console.log(chalk.yellow('No projects found. Please create a project first.'));
      process.exit(1);
    }
    
    const choices = projects.map(project => ({
      name: `${project.name} (${project.id})`,
      value: project.id
    }));
    
    const answer = await inquirer.prompt([
      {
        type: 'list',
        name: 'projectId',
        message: 'Select a project:',
        choices
      }
    ]);
    
    return answer.projectId;
  } catch (error) {
    console.error(chalk.red('Error:'), error);
    process.exit(1);
  }
}

// Parse command line arguments
program.parse(process.argv);

// Show help if no command specified
if (!process.argv.slice(2).length) {
  program.help();
}
