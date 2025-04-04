#!/usr/bin/env node

/**
 * Seed script to populate the project management system with initial data
 * based on Asabaal's 2025 business timeline
 */

const path = require('path');
const { ProjectManagementApp, PROJECT_CATEGORIES } = require('../src/index');

// Initialize the app
const app = new ProjectManagementApp({
  dataDir: path.join(process.cwd(), 'data')
});

// Define the timeline data
const seedData = {
  projects: [
    // APRIL/MAY Projects
    {
      name: 'Trading Program Evaluation',
      description: 'Evaluate trading programs and select the best option',
      category: PROJECT_CATEGORIES.TRADING,
      status: 'in_progress',
      startDate: '2025-04-01',
      endDate: '2025-05-15',
      revenue: {
        target: 0,
        actual: 0,
        currency: 'USD'
      },
      tags: ['trading', 'evaluation', 'immediate', 'priority']
    },
    {
      name: 'Trading Strategy Implementation',
      description: 'Implement trading strategies to achieve profitability',
      category: PROJECT_CATEGORIES.TRADING,
      status: 'planned',
      startDate: '2025-04-15',
      endDate: '2025-05-31',
      revenue: {
        target: 2000,
        actual: 0,
        currency: 'USD'
      },
      tags: ['trading', 'strategy', 'implementation']
    },
    {
      name: 'Business Registration',
      description: 'Register business formally and set up necessary infrastructure',
      category: PROJECT_CATEGORIES.BUSINESS,
      status: 'planned',
      startDate: '2025-04-10',
      endDate: '2025-05-31',
      revenue: {
        target: 0,
        actual: 0,
        currency: 'USD'
      },
      tags: ['business', 'legal', 'registration']
    },
    
    // MAY Projects
    {
      name: 'Business Infrastructure Setup',
      description: 'Set up business email, banking, and accounting',
      category: PROJECT_CATEGORIES.BUSINESS,
      status: 'planned',
      startDate: '2025-05-01',
      endDate: '2025-05-31',
      revenue: {
        target: 0,
        actual: 0,
        currency: 'USD'
      },
      tags: ['business', 'infrastructure', 'setup']
    },
    {
      name: 'InvestFest Messaging Development',
      description: 'Develop business messaging for InvestFest (August)',
      category: PROJECT_CATEGORIES.BUSINESS,
      status: 'planned',
      startDate: '2025-05-15',
      endDate: '2025-06-30',
      revenue: {
        target: 0,
        actual: 0,
        currency: 'USD'
      },
      tags: ['business', 'marketing', 'investfest']
    },
    
    // JUNE/JULY Projects
    {
      name: 'Dapper Demos Vol. 3 Content Cycle',
      description: 'Execute content cycle for the "Dapper Demos Vol. 3" EP (released February)',
      category: PROJECT_CATEGORIES.CONTENT_CREATION,
      status: 'planned',
      startDate: '2025-06-01',
      endDate: '2025-07-31',
      revenue: {
        target: 1000,
        actual: 0,
        currency: 'USD'
      },
      tags: ['music', 'content', 'promotion', 'dapper-demos']
    },
    {
      name: 'Trading Strategy Refinement',
      description: 'Refine trading strategies based on initial implementation',
      category: PROJECT_CATEGORIES.TRADING,
      status: 'planned',
      startDate: '2025-06-01',
      endDate: '2025-07-31',
      revenue: {
        target: 3000,
        actual: 0,
        currency: 'USD'
      },
      tags: ['trading', 'strategy', 'refinement']
    },
    {
      name: 'Music Analysis Pipeline',
      description: 'Develop data collection pipeline for music analysis',
      category: PROJECT_CATEGORIES.TECHNOLOGY,
      status: 'planned',
      startDate: '2025-06-15',
      endDate: '2025-07-31',
      revenue: {
        target: 0,
        actual: 0,
        currency: 'USD'
      },
      tags: ['technology', 'data', 'music-analysis']
    },
    {
      name: 'Business Partnership Development',
      description: 'Strengthen existing business partnerships and explore new ones',
      category: PROJECT_CATEGORIES.BUSINESS,
      status: 'planned',
      startDate: '2025-06-01',
      endDate: '2025-07-31',
      revenue: {
        target: 500,
        actual: 0,
        currency: 'USD'
      },
      tags: ['business', 'partnerships', 'networking']
    },
    
    // AUGUST/SEPTEMBER Projects
    {
      name: 'InvestFest Attendance',
      description: 'Attend InvestFest with clear business messaging',
      category: PROJECT_CATEGORIES.BUSINESS,
      status: 'planned',
      startDate: '2025-08-01',
      endDate: '2025-08-15',
      revenue: {
        target: 0,
        actual: 0,
        currency: 'USD'
      },
      tags: ['business', 'conference', 'investfest', 'networking']
    },
    {
      name: '4-D(emos) EP Preparation',
      description: 'Prepare "4-D(emos)" EP for release',
      category: PROJECT_CATEGORIES.MUSIC_PRODUCTION,
      status: 'planned',
      startDate: '2025-08-01',
      endDate: '2025-09-30',
      revenue: {
        target: 0,
        actual: 0,
        currency: 'USD'
      },
      tags: ['music', 'production', '4-demos']
    },
    {
      name: 'Website Transition',
      description: 'Finalize website transition to new platform',
      category: PROJECT_CATEGORIES.TECHNOLOGY,
      status: 'planned',
      startDate: '2025-08-15',
      endDate: '2025-09-30',
      revenue: {
        target: 0,
        actual: 0,
        currency: 'USD'
      },
      tags: ['technology', 'website', 'transition']
    },
    {
      name: 'Weekly Content Production',
      description: 'Establish consistent weekly content production',
      category: PROJECT_CATEGORIES.CONTENT_CREATION,
      status: 'planned',
      startDate: '2025-08-01',
      endDate: '2025-09-30',
      revenue: {
        target: 1000,
        actual: 0,
        currency: 'USD'
      },
      tags: ['content', 'production', 'consistency']
    },
    
    // OCTOBER Projects
    {
      name: '4-D(emos) EP Release',
      description: 'Release "4-D(emos)" EP (end of month)',
      category: PROJECT_CATEGORIES.MUSIC_PRODUCTION,
      status: 'planned',
      startDate: '2025-10-01',
      endDate: '2025-10-31',
      revenue: {
        target: 2000,
        actual: 0,
        currency: 'USD'
      },
      tags: ['music', 'release', '4-demos']
    },
    {
      name: 'Advanced Trading Strategies',
      description: 'Implement advanced trading strategies',
      category: PROJECT_CATEGORIES.TRADING,
      status: 'planned',
      startDate: '2025-10-01',
      endDate: '2025-10-31',
      revenue: {
        target: 4000,
        actual: 0,
        currency: 'USD'
      },
      tags: ['trading', 'advanced', 'strategies']
    },
    {
      name: 'Media Platform Expansion',
      description: 'Expand media platform submissions',
      category: PROJECT_CATEGORIES.CONTENT_CREATION,
      status: 'planned',
      startDate: '2025-10-01',
      endDate: '2025-10-31',
      revenue: {
        target: 500,
        actual: 0,
        currency: 'USD'
      },
      tags: ['content', 'platforms', 'expansion']
    },
    {
      name: 'Professional Debut Planning',
      description: 'Begin planning for professional debut project',
      category: PROJECT_CATEGORIES.MUSIC_PRODUCTION,
      status: 'planned',
      startDate: '2025-10-15',
      endDate: '2025-11-30',
      revenue: {
        target: 0,
        actual: 0,
        currency: 'USD'
      },
      tags: ['music', 'planning', 'professional-debut']
    },
    
    // NOVEMBER/DECEMBER Projects
    {
      name: '4-D(emos) Post-Release Cycle',
      description: 'Execute post-release content cycle for "4-D(emos)"',
      category: PROJECT_CATEGORIES.CONTENT_CREATION,
      status: 'planned',
      startDate: '2025-11-01',
      endDate: '2025-12-15',
      revenue: {
        target: 1500,
        actual: 0,
        currency: 'USD'
      },
      tags: ['music', 'content', 'post-release', '4-demos']
    },
    {
      name: '"I Never Asked To Be Queer" Project Roadmap',
      description: 'Prepare "I Never Asked To Be Queer" project roadmap',
      category: PROJECT_CATEGORIES.MUSIC_PRODUCTION,
      status: 'planned',
      startDate: '2025-11-01',
      endDate: '2025-12-31',
      revenue: {
        target: 0,
        actual: 0,
        currency: 'USD'
      },
      tags: ['music', 'planning', 'roadmap', 'inever']
    },
    {
      name: 'January 2026 Single Preparation',
      description: 'Finalize at least one single for January 2026 release',
      category: PROJECT_CATEGORIES.MUSIC_PRODUCTION,
      status: 'planned',
      startDate: '2025-11-15',
      endDate: '2025-12-31',
      revenue: {
        target: 0,
        actual: 0,
        currency: 'USD'
      },
      tags: ['music', 'production', 'single', '2026']
    },
    {
      name: '2025 Review & 2026 Planning',
      description: 'Review annual performance and set 2026 targets',
      category: PROJECT_CATEGORIES.BUSINESS,
      status: 'planned',
      startDate: '2025-12-01',
      endDate: '2025-12-31',
      revenue: {
        target: 0,
        actual: 0,
        currency: 'USD'
      },
      tags: ['business', 'review', 'planning', '2026']
    }
  ],
  tasks: [
    // Trading Program Evaluation Tasks
    {
      name: 'Research available trading programs',
      description: 'Identify and list all potential trading programs to evaluate',
      projectId: null, // Will be populated after project creation
      priority: 'high',
      status: 'in_progress',
      dueDate: '2025-04-10'
    },
    {
      name: 'Develop evaluation criteria',
      description: 'Create a framework for comparing trading programs',
      projectId: null, // Will be populated after project creation
      priority: 'high',
      status: 'todo',
      dueDate: '2025-04-12'
    },
    {
      name: 'Test top 3 trading programs',
      description: 'Run simulations on the top candidates',
      projectId: null, // Will be populated after project creation
      priority: 'high',
      status: 'todo',
      dueDate: '2025-04-30'
    },
    {
      name: 'Make final selection',
      description: 'Choose the best trading program based on evaluation',
      projectId: null, // Will be populated after project creation
      priority: 'high',
      status: 'todo',
      dueDate: '2025-05-15'
    },
    
    // Business Registration Tasks
    {
      name: 'Research business entity types',
      description: 'Determine the best business structure (LLC, S-Corp, etc.)',
      projectId: null, // Will be populated after project creation
      priority: 'medium',
      status: 'todo',
      dueDate: '2025-04-20'
    },
    {
      name: 'File registration paperwork',
      description: 'Submit all necessary forms for business registration',
      projectId: null, // Will be populated after project creation
      priority: 'medium',
      status: 'todo',
      dueDate: '2025-05-10'
    },
    {
      name: 'Apply for EIN',
      description: 'Obtain Employer Identification Number from IRS',
      projectId: null, // Will be populated after project creation
      priority: 'medium',
      status: 'todo',
      dueDate: '2025-05-15'
    },
    {
      name: 'Register business name',
      description: 'File for DBA (Doing Business As) if necessary',
      projectId: null, // Will be populated after project creation
      priority: 'medium',
      status: 'todo',
      dueDate: '2025-05-20'
    },
    
    // Business Infrastructure Setup Tasks
    {
      name: 'Set up business email',
      description: 'Create professional email accounts for the business',
      projectId: null, // Will be populated after project creation
      priority: 'medium',
      status: 'todo',
      dueDate: '2025-05-05'
    },
    {
      name: 'Open business bank account',
      description: 'Research and open account with appropriate bank',
      projectId: null, // Will be populated after project creation
      priority: 'high',
      status: 'todo',
      dueDate: '2025-05-10'
    },
    {
      name: 'Set up accounting software',
      description: 'Choose and configure accounting system',
      projectId: null, // Will be populated after project creation
      priority: 'medium',
      status: 'todo',
      dueDate: '2025-05-15'
    },
    {
      name: 'Establish bookkeeping procedures',
      description: 'Create system for tracking income and expenses',
      projectId: null, // Will be populated after project creation
      priority: 'medium',
      status: 'todo',
      dueDate: '2025-05-25'
    },
    
    // Dapper Demos Vol. 3 Content Cycle Tasks
    {
      name: 'Develop content strategy',
      description: 'Plan content types and schedule for promotion',
      projectId: null, // Will be populated after project creation
      priority: 'high',
      status: 'todo',
      dueDate: '2025-06-10'
    },
    {
      name: 'Create promotional materials',
      description: 'Design graphics, videos, and other assets',
      projectId: null, // Will be populated after project creation
      priority: 'high',
      status: 'todo',
      dueDate: '2025-06-20'
    },
    {
      name: 'Schedule social media posts',
      description: 'Prepare and schedule content across platforms',
      projectId: null, // Will be populated after project creation
      priority: 'medium',
      status: 'todo',
      dueDate: '2025-06-25'
    },
    {
      name: 'Reach out to playlist curators',
      description: 'Contact playlist curators for potential inclusion',
      projectId: null, // Will be populated after project creation
      priority: 'medium',
      status: 'todo',
      dueDate: '2025-07-10'
    },
    {
      name: 'Analyze campaign performance',
      description: 'Review metrics and assess effectiveness',
      projectId: null, // Will be populated after project creation
      priority: 'medium',
      status: 'todo',
      dueDate: '2025-07-31'
    },
    
    // InvestFest Attendance Tasks
    {
      name: 'Register for InvestFest',
      description: 'Secure tickets and accommodations',
      projectId: null, // Will be populated after project creation
      priority: 'high',
      status: 'todo',
      dueDate: '2025-06-15'
    },
    {
      name: 'Prepare business pitch deck',
      description: 'Create presentation materials for networking',
      projectId: null, // Will be populated after project creation
      priority: 'high',
      status: 'todo',
      dueDate: '2025-07-15'
    },
    {
      name: 'Develop revenue pipeline documentation',
      description: 'Create clear visual representation of revenue streams',
      projectId: null, // Will be populated after project creation
      priority: 'high',
      status: 'todo',
      dueDate: '2025-07-31'
    },
    {
      name: 'Schedule networking meetings',
      description: 'Arrange meetings with potential partners/investors',
      projectId: null, // Will be populated after project creation
      priority: 'medium',
      status: 'todo',
      dueDate: '2025-07-25'
    },
    
    // 4-D(emos) EP Preparation Tasks
    {
      name: 'Finalize track selection',
      description: 'Choose final tracks for inclusion on EP',
      projectId: null, // Will be populated after project creation
      priority: 'high',
      status: 'todo',
      dueDate: '2025-08-15'
    },
    {
      name: 'Complete mixing and mastering',
      description: 'Finalize audio production for all tracks',
      projectId: null, // Will be populated after project creation
      priority: 'high',
      status: 'todo',
      dueDate: '2025-09-15'
    },
    {
      name: 'Design EP artwork',
      description: 'Create cover art and other visual assets',
      projectId: null, // Will be populated after project creation
      priority: 'medium',
      status: 'todo',
      dueDate: '2025-09-01'
    },
    {
      name: 'Prepare distribution package',
      description: 'Organize all assets for distributor submission',
      projectId: null, // Will be populated after project creation
      priority: 'high',
      status: 'todo',
      dueDate: '2025-09-20'
    },
    {
      name: 'Submit to distribution service',
      description: 'Upload EP to distribution platform',
      projectId: null, // Will be populated after project creation
      priority: 'high',
      status: 'todo',
      dueDate: '2025-09-30'
    },
    
    // 4-D(emos) EP Release Tasks
    {
      name: 'Confirm release details',
      description: 'Verify all platforms show correct information',
      projectId: null, // Will be populated after project creation
      priority: 'high',
      status: 'todo',
      dueDate: '2025-10-10'
    },
    {
      name: 'Launch social media campaign',
      description: 'Begin executing promotional strategy',
      projectId: null, // Will be populated after project creation
      priority: 'high',
      status: 'todo',
      dueDate: '2025-10-15'
    },
    {
      name: 'Send press releases',
      description: 'Distribute press materials to media contacts',
      projectId: null, // Will be populated after project creation
      priority: 'medium',
      status: 'todo',
      dueDate: '2025-10-20'
    },
    {
      name: 'Release day activities',
      description: 'Coordinate all release day promotion',
      projectId: null, // Will be populated after project creation
      priority: 'high',
      status: 'todo',
      dueDate: '2025-10-31'
    },
    
    // 2025 Review & 2026 Planning Tasks
    {
      name: 'Gather annual performance data',
      description: 'Compile metrics from all business areas',
      projectId: null, // Will be populated after project creation
      priority: 'medium',
      status: 'todo',
      dueDate: '2025-12-10'
    },
    {
      name: 'Analyze revenue streams',
      description: 'Evaluate performance of each revenue source',
      projectId: null, // Will be populated after project creation
      priority: 'high',
      status: 'todo',
      dueDate: '2025-12-15'
    },
    {
      name: 'Set 2026 goals',
      description: 'Establish specific, measurable targets for next year',
      projectId: null, // Will be populated after project creation
      priority: 'high',
      status: 'todo',
      dueDate: '2025-12-20'
    },
    {
      name: 'Create Q1 2026 roadmap',
      description: 'Develop detailed plan for first quarter',
      projectId: null, // Will be populated after project creation
      priority: 'high',
      status: 'todo',
      dueDate: '2025-12-31'
    }
  ]
};

/**
 * Main function to seed the database
 */
async function seedDatabase() {
  try {
    // Initialize the app
    await app.init();
    
    console.log('Initializing project management system...');
    
    // We'll use the project service for creating projects with tasks
    const projectService = app.getProjectService();
    
    // Create the projects first
    console.log('Creating projects...');
    const projectMap = {};
    
    for (const projectData of seedData.projects) {
      const result = await projectService.projectRepository.create(projectData);
      console.log(`Created project: ${result.name}`);
      
      // Store the project ID for later use
      projectMap[result.name] = result.id;
    }
    
    // Now assign tasks to their projects and create them
    console.log('Creating tasks...');
    for (const taskData of seedData.tasks) {
      // Try to find the appropriate project for this task based on keywords
      let assignedProject = null;
      
      // This is a simple heuristic; you might want to improve this
      for (const [projectName, projectId] of Object.entries(projectMap)) {
        if (taskData.name.includes(projectName) || 
            taskData.description.includes(projectName) ||
            projectName.includes(taskData.name.split(' ')[0])) {
          assignedProject = projectId;
          break;
        }
      }
      
      // If no matching project was found, assign to a default project
      if (!assignedProject) {
        // Find a project with a similar category
        const projectNames = Object.keys(projectMap);
        for (const name of projectNames) {
          if (name.toLowerCase().includes(taskData.name.split(' ')[0].toLowerCase())) {
            assignedProject = projectMap[name];
            break;
          }
        }
        
        // If still no match, use the first project as default
        if (!assignedProject) {
          assignedProject = projectMap[Object.keys(projectMap)[0]];
        }
      }
      
      // Assign project ID and create the task
      const taskWithProject = {
        ...taskData,
        projectId: assignedProject
      };
      
      const result = await projectService.taskRepository.create(taskWithProject);
      console.log(`Created task: ${result.name}`);
    }
    
    console.log('Seed completed successfully!');
    console.log(`Created ${Object.keys(projectMap).length} projects and ${seedData.tasks.length} tasks.`);
    
    // Return to show the data was seeded
    return true;
  } catch (error) {
    console.error('Error seeding database:', error);
    throw error;
  }
}

// Run the seed function if executed directly
if (require.main === module) {
  seedDatabase()
    .then(() => {
      console.log('Database seeded successfully');
      process.exit(0);
    })
    .catch(error => {
      console.error('Seed failed:', error);
      process.exit(1);
    });
}

module.exports = seedDatabase;
