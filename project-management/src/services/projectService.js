/**
 * Project Service
 * Coordinates operations between projects and tasks
 */

class ProjectService {
  constructor(projectRepository, taskRepository) {
    this.projectRepository = projectRepository;
    this.taskRepository = taskRepository;
  }

  /**
   * Initialize the service
   */
  async init() {
    await this.projectRepository.init();
    await this.taskRepository.init();
    return true;
  }

  /**
   * Create a new project with tasks
   * @param {Object} projectData - Project data
   * @param {Array} tasks - Optional tasks to create
   * @returns {Promise<Object>} Created project with tasks
   */
  async createProject(projectData, tasks = []) {
    // Create the project first
    const project = await this.projectRepository.create(projectData);
    
    // Add tasks if provided
    const createdTasks = [];
    for (const taskData of tasks) {
      const task = await this.taskRepository.create({
        ...taskData,
        projectId: project.id
      });
      createdTasks.push(task);
    }
    
    return {
      project,
      tasks: createdTasks
    };
  }

  /**
   * Get a project with all its tasks
   * @param {string} projectId - Project ID
   * @returns {Promise<Object>} Project with tasks
   */
  async getProjectWithTasks(projectId) {
    const project = await this.projectRepository.getById(projectId);
    
    if (!project) {
      return null;
    }
    
    const tasks = await this.taskRepository.getTasksByProject(projectId);
    
    return {
      project,
      tasks
    };
  }

  /**
   * Update a project and optionally its tasks
   * @param {string} projectId - Project ID
   * @param {Object} projectData - Updated project data
   * @param {Array} tasksToUpdate - Optional tasks to update
   * @param {Array} tasksToAdd - Optional new tasks to add
   * @param {Array} taskIdsToRemove - Optional task IDs to remove
   * @returns {Promise<Object>} Updated project with tasks
   */
  async updateProject(
    projectId,
    projectData,
    tasksToUpdate = [],
    tasksToAdd = [],
    taskIdsToRemove = []
  ) {
    // Update the project
    const project = await this.projectRepository.update(projectId, projectData);
    
    if (!project) {
      return null;
    }
    
    // Update existing tasks
    for (const taskData of tasksToUpdate) {
      await this.taskRepository.update(taskData.id, taskData);
    }
    
    // Add new tasks
    for (const taskData of tasksToAdd) {
      await this.taskRepository.create({
        ...taskData,
        projectId
      });
    }
    
    // Remove tasks
    for (const taskId of taskIdsToRemove) {
      await this.taskRepository.delete(taskId);
    }
    
    // Get all tasks for the project
    const tasks = await this.taskRepository.getTasksByProject(projectId);
    
    return {
      project,
      tasks
    };
  }

  /**
   * Delete a project and all its tasks
   * @param {string} projectId - Project ID
   * @returns {Promise<boolean>} True if deleted
   */
  async deleteProject(projectId) {
    // Get all tasks for the project
    const tasks = await this.taskRepository.getTasksByProject(projectId);
    
    // Delete all tasks
    for (const task of tasks) {
      await this.taskRepository.delete(task.id);
    }
    
    // Delete the project
    return await this.projectRepository.delete(projectId);
  }

  /**
   * Get project status summary
   * @param {string} projectId - Project ID
   * @returns {Promise<Object>} Status summary
   */
  async getProjectStatus(projectId) {
    const { project, tasks } = await this.getProjectWithTasks(projectId);
    
    if (!project) {
      return null;
    }
    
    // Count tasks by status
    const taskCounts = {
      total: tasks.length,
      todo: 0,
      inProgress: 0,
      review: 0,
      done: 0
    };
    
    for (const task of tasks) {
      switch (task.status) {
        case 'todo':
          taskCounts.todo++;
          break;
        case 'in_progress':
          taskCounts.inProgress++;
          break;
        case 'review':
          taskCounts.review++;
          break;
        case 'done':
          taskCounts.done++;
          break;
      }
    }
    
    // Calculate progress percentage
    const progress = taskCounts.total > 0
      ? Math.round((taskCounts.done / taskCounts.total) * 100)
      : 0;
    
    // Calculate if project is on schedule
    const isOnSchedule = project.isOnSchedule ? project.isOnSchedule() : null;
    
    // Count overdue tasks
    const overdueTasks = tasks.filter(task => {
      if (!task.dueDate || task.status === 'done') return false;
      return new Date(task.dueDate) < new Date();
    });
    
    return {
      project: {
        id: project.id,
        name: project.name,
        status: project.status,
        startDate: project.startDate,
        endDate: project.endDate
      },
      progress,
      isOnSchedule,
      taskCounts,
      overdueTasks: overdueTasks.length,
      updated: project.updatedAt
    };
  }

  /**
   * Get dashboard summary of all projects
   * @returns {Promise<Object>} Dashboard data
   */
  async getDashboardSummary() {
    // Get all projects
    const projects = await this.projectRepository.getAll();
    
    // Get active projects
    const activeProjects = projects.filter(
      project => project.status === 'in_progress'
    );
    
    // Get all tasks
    const tasks = await this.taskRepository.getAll();
    
    // Get overdue tasks
    const overdueTasks = await this.taskRepository.getOverdueTasks();
    
    // Get tasks due in the next 7 days
    const upcomingTasks = await this.taskRepository.getTasksDueInDays(7);
    
    // Count tasks by priority
    const tasksByPriority = {
      low: tasks.filter(task => task.priority === 'low').length,
      medium: tasks.filter(task => task.priority === 'medium').length,
      high: tasks.filter(task => task.priority === 'high').length,
      urgent: tasks.filter(task => task.priority === 'urgent').length
    };
    
    // Count projects by category
    const projectsByCategory = {};
    for (const project of projects) {
      if (!projectsByCategory[project.category]) {
        projectsByCategory[project.category] = 0;
      }
      projectsByCategory[project.category]++;
    }
    
    return {
      projects: {
        total: projects.length,
        active: activeProjects.length,
        completed: projects.filter(p => p.status === 'completed').length,
        byCategory: projectsByCategory
      },
      tasks: {
        total: tasks.length,
        overdue: overdueTasks.length,
        upcoming: upcomingTasks.length,
        byPriority: tasksByPriority,
        completed: tasks.filter(t => t.status === 'done').length
      },
      updated: new Date().toISOString()
    };
  }

  /**
   * Get projects and tasks for a specific date range
   * @param {Date} startDate - Range start
   * @param {Date} endDate - Range end
   * @returns {Promise<Object>} Projects and tasks in the range
   */
  async getTimelineData(startDate, endDate) {
    // Get projects in the date range
    const projects = await this.projectRepository.getProjectsForPeriod(
      startDate,
      endDate
    );
    
    // Get all tasks for these projects
    const projectIds = projects.map(project => project.id);
    const allTasks = await this.taskRepository.getAll();
    const tasks = allTasks.filter(task => projectIds.includes(task.projectId));
    
    // Filter tasks to only include those in the date range
    const tasksInRange = tasks.filter(task => {
      if (!task.dueDate) return false;
      
      const dueDate = new Date(task.dueDate);
      return dueDate >= new Date(startDate) && dueDate <= new Date(endDate);
    });
    
    return {
      projects,
      tasks: tasksInRange
    };
  }
}

module.exports = ProjectService;
