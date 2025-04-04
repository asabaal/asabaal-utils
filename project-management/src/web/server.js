/**
 * Web server for the project management system
 * Provides a REST API and serves the frontend
 */

const express = require('express');
const path = require('path');
const { ProjectManagementApp } = require('../index');

// Initialize the app
const app = new ProjectManagementApp({
  dataDir: path.join(process.cwd(), 'data')
});

// Create Express app
const server = express();
const PORT = process.env.PORT || 3000;

// Middleware
server.use(express.json());
server.use(express.urlencoded({ extended: true }));
server.use(express.static(path.join(__dirname, 'public')));

// Initialize data services
let projectService;
let initialized = false;

// Initialization middleware
server.use(async (req, res, next) => {
  if (!initialized) {
    try {
      await app.init();
      projectService = app.getProjectService();
      initialized = true;
      console.log('Project management system initialized');
    } catch (error) {
      console.error('Failed to initialize project management system:', error);
      return res.status(500).json({ error: 'Failed to initialize system' });
    }
  }
  next();
});

// API Routes

// Get dashboard data
server.get('/api/dashboard', async (req, res) => {
  try {
    const dashboard = await app.getDashboardSummary();
    res.json(dashboard);
  } catch (error) {
    console.error('Error getting dashboard:', error);
    res.status(500).json({ error: 'Failed to fetch dashboard data' });
  }
});

// Get all projects
server.get('/api/projects', async (req, res) => {
  try {
    const projects = await projectService.projectRepository.getAll();
    res.json(projects);
  } catch (error) {
    console.error('Error getting projects:', error);
    res.status(500).json({ error: 'Failed to fetch projects' });
  }
});

// Get project by ID
server.get('/api/projects/:id', async (req, res) => {
  try {
    const project = await projectService.getProjectWithTasks(req.params.id);
    
    if (!project) {
      return res.status(404).json({ error: 'Project not found' });
    }
    
    res.json(project);
  } catch (error) {
    console.error(`Error getting project ${req.params.id}:`, error);
    res.status(500).json({ error: 'Failed to fetch project' });
  }
});

// Create project
server.post('/api/projects', async (req, res) => {
  try {
    const { project, tasks } = req.body;
    
    if (!project || !project.name) {
      return res.status(400).json({ error: 'Project name is required' });
    }
    
    const result = await projectService.createProject(project, tasks || []);
    res.status(201).json(result);
  } catch (error) {
    console.error('Error creating project:', error);
    res.status(500).json({ error: 'Failed to create project' });
  }
});

// Update project
server.put('/api/projects/:id', async (req, res) => {
  try {
    const { project, tasksToUpdate, tasksToAdd, taskIdsToRemove } = req.body;
    
    if (!project) {
      return res.status(400).json({ error: 'Project data is required' });
    }
    
    const result = await projectService.updateProject(
      req.params.id,
      project,
      tasksToUpdate || [],
      tasksToAdd || [],
      taskIdsToRemove || []
    );
    
    if (!result) {
      return res.status(404).json({ error: 'Project not found' });
    }
    
    res.json(result);
  } catch (error) {
    console.error(`Error updating project ${req.params.id}:`, error);
    res.status(500).json({ error: 'Failed to update project' });
  }
});

// Delete project
server.delete('/api/projects/:id', async (req, res) => {
  try {
    const deleted = await projectService.deleteProject(req.params.id);
    
    if (!deleted) {
      return res.status(404).json({ error: 'Project not found' });
    }
    
    res.json({ success: true });
  } catch (error) {
    console.error(`Error deleting project ${req.params.id}:`, error);
    res.status(500).json({ error: 'Failed to delete project' });
  }
});

// Get project status
server.get('/api/projects/:id/status', async (req, res) => {
  try {
    const status = await projectService.getProjectStatus(req.params.id);
    
    if (!status) {
      return res.status(404).json({ error: 'Project not found' });
    }
    
    res.json(status);
  } catch (error) {
    console.error(`Error getting project status ${req.params.id}:`, error);
    res.status(500).json({ error: 'Failed to fetch project status' });
  }
});

// Get all tasks
server.get('/api/tasks', async (req, res) => {
  try {
    const tasks = await projectService.taskRepository.getAll();
    res.json(tasks);
  } catch (error) {
    console.error('Error getting tasks:', error);
    res.status(500).json({ error: 'Failed to fetch tasks' });
  }
});

// Get tasks for a project
server.get('/api/projects/:id/tasks', async (req, res) => {
  try {
    const tasks = await projectService.taskRepository.getTasksByProject(req.params.id);
    res.json(tasks);
  } catch (error) {
    console.error(`Error getting tasks for project ${req.params.id}:`, error);
    res.status(500).json({ error: 'Failed to fetch tasks' });
  }
});

// Create task
server.post('/api/tasks', async (req, res) => {
  try {
    const task = req.body;
    
    if (!task || !task.name || !task.projectId) {
      return res.status(400).json({ error: 'Task name and project ID are required' });
    }
    
    const result = await projectService.taskRepository.create(task);
    res.status(201).json(result);
  } catch (error) {
    console.error('Error creating task:', error);
    res.status(500).json({ error: 'Failed to create task' });
  }
});

// Update task
server.put('/api/tasks/:id', async (req, res) => {
  try {
    const task = req.body;
    
    if (!task) {
      return res.status(400).json({ error: 'Task data is required' });
    }
    
    const result = await projectService.taskRepository.update(req.params.id, task);
    
    if (!result) {
      return res.status(404).json({ error: 'Task not found' });
    }
    
    res.json(result);
  } catch (error) {
    console.error(`Error updating task ${req.params.id}:`, error);
    res.status(500).json({ error: 'Failed to update task' });
  }
});

// Delete task
server.delete('/api/tasks/:id', async (req, res) => {
  try {
    const deleted = await projectService.taskRepository.delete(req.params.id);
    
    if (!deleted) {
      return res.status(404).json({ error: 'Task not found' });
    }
    
    res.json({ success: true });
  } catch (error) {
    console.error(`Error deleting task ${req.params.id}:`, error);
    res.status(500).json({ error: 'Failed to delete task' });
  }
});

// Mark task as complete
server.put('/api/tasks/:id/complete', async (req, res) => {
  try {
    const result = await projectService.taskRepository.markAsComplete(req.params.id);
    
    if (!result) {
      return res.status(404).json({ error: 'Task not found' });
    }
    
    res.json(result);
  } catch (error) {
    console.error(`Error marking task ${req.params.id} as complete:`, error);
    res.status(500).json({ error: 'Failed to complete task' });
  }
});

// Get overdue tasks
server.get('/api/tasks/overdue', async (req, res) => {
  try {
    const tasks = await projectService.taskRepository.getOverdueTasks();
    res.json(tasks);
  } catch (error) {
    console.error('Error getting overdue tasks:', error);
    res.status(500).json({ error: 'Failed to fetch overdue tasks' });
  }
});

// Get upcoming tasks
server.get('/api/tasks/upcoming', async (req, res) => {
  try {
    const days = req.query.days ? parseInt(req.query.days) : 7;
    const tasks = await projectService.taskRepository.getTasksDueInDays(days);
    res.json(tasks);
  } catch (error) {
    console.error('Error getting upcoming tasks:', error);
    res.status(500).json({ error: 'Failed to fetch upcoming tasks' });
  }
});

// Get timeline data
server.get('/api/timeline', async (req, res) => {
  try {
    const startDate = req.query.start || new Date().toISOString().split('T')[0];
    const endDate = req.query.end || new Date(new Date().getTime() + 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
    
    const data = await projectService.getTimelineData(startDate, endDate);
    res.json(data);
  } catch (error) {
    console.error('Error getting timeline data:', error);
    res.status(500).json({ error: 'Failed to fetch timeline data' });
  }
});

// Serve the main app for all other routes (SPA support)
server.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Start the server
function startServer() {
  return new Promise((resolve, reject) => {
    const httpServer = server.listen(PORT, () => {
      console.log(`Server running on http://localhost:${PORT}`);
      resolve(httpServer);
    });
    
    httpServer.on('error', error => {
      console.error('Server error:', error);
      reject(error);
    });
  });
}

// Export for use in other modules
module.exports = {
  startServer,
  app,
  server
};

// Start the server if this file is run directly
if (require.main === module) {
  startServer().catch(console.error);
}
