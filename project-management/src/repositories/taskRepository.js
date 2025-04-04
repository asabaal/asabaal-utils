/**
 * Task Repository
 * Handles CRUD operations for tasks
 */

const { Task } = require('../models');

class TaskRepository {
  constructor(storage) {
    this.storage = storage;
    this.collectionName = 'tasks';
  }

  /**
   * Initialize the repository
   */
  async init() {
    try {
      const exists = await this.storage.exists(this.collectionName);
      if (!exists) {
        await this.storage.save(this.collectionName, []);
      }
      return true;
    } catch (error) {
      console.error('Failed to initialize task repository:', error);
      throw error;
    }
  }

  /**
   * Get all tasks
   * @param {Object} filters - Optional filters
   * @returns {Promise<Task[]>} List of tasks
   */
  async getAll(filters = {}) {
    try {
      const tasks = await this.storage.load(this.collectionName);
      
      // Apply filters if provided
      if (Object.keys(filters).length === 0) {
        return tasks;
      }
      
      return tasks.filter(task => {
        return Object.entries(filters).every(([key, value]) => {
          // Handle date filters
          if (key === 'dueDateBefore' && value) {
            return !task.dueDate || new Date(task.dueDate) <= new Date(value);
          }
          if (key === 'dueDateAfter' && value) {
            return !task.dueDate || new Date(task.dueDate) >= new Date(value);
          }
          
          // Default equality check
          return task[key] === value;
        });
      });
    } catch (error) {
      console.error('Failed to get tasks:', error);
      throw error;
    }
  }

  /**
   * Get a task by ID
   * @param {string} id - Task ID
   * @returns {Promise<Task|null>} Found task or null
   */
  async getById(id) {
    try {
      const tasks = await this.storage.load(this.collectionName);
      return tasks.find(task => task.id === id) || null;
    } catch (error) {
      console.error(`Failed to get task ${id}:`, error);
      throw error;
    }
  }

  /**
   * Create a new task
   * @param {Object} taskData - Task data
   * @returns {Promise<Task>} Created task
   */
  async create(taskData) {
    try {
      const tasks = await this.storage.load(this.collectionName);
      
      // Create new task instance
      const task = new Task(taskData);
      
      // Save to storage
      tasks.push(task);
      await this.storage.save(this.collectionName, tasks);
      
      return task;
    } catch (error) {
      console.error('Failed to create task:', error);
      throw error;
    }
  }

  /**
   * Update an existing task
   * @param {string} id - Task ID
   * @param {Object} taskData - Updated task data
   * @returns {Promise<Task|null>} Updated task or null
   */
  async update(id, taskData) {
    try {
      const tasks = await this.storage.load(this.collectionName);
      const index = tasks.findIndex(task => task.id === id);
      
      if (index === -1) {
        return null;
      }
      
      // Update task
      const updatedTask = {
        ...tasks[index],
        ...taskData,
        updatedAt: new Date().toISOString()
      };
      
      tasks[index] = updatedTask;
      await this.storage.save(this.collectionName, tasks);
      
      return updatedTask;
    } catch (error) {
      console.error(`Failed to update task ${id}:`, error);
      throw error;
    }
  }

  /**
   * Delete a task
   * @param {string} id - Task ID
   * @returns {Promise<boolean>} True if deleted
   */
  async delete(id) {
    try {
      const tasks = await this.storage.load(this.collectionName);
      const filteredTasks = tasks.filter(task => task.id !== id);
      
      if (filteredTasks.length === tasks.length) {
        return false; // Task not found
      }
      
      await this.storage.save(this.collectionName, filteredTasks);
      return true;
    } catch (error) {
      console.error(`Failed to delete task ${id}:`, error);
      throw error;
    }
  }

  /**
   * Get tasks for a specific project
   * @param {string} projectId - Project ID
   * @returns {Promise<Task[]>} Tasks for the project
   */
  async getTasksByProject(projectId) {
    try {
      const tasks = await this.storage.load(this.collectionName);
      return tasks.filter(task => task.projectId === projectId);
    } catch (error) {
      console.error(`Failed to get tasks for project ${projectId}:`, error);
      throw error;
    }
  }

  /**
   * Get tasks due in the next X days
   * @param {number} days - Number of days
   * @returns {Promise<Task[]>} Tasks due in the period
   */
  async getTasksDueInDays(days = 7) {
    try {
      const tasks = await this.storage.load(this.collectionName);
      const today = new Date();
      const futureDate = new Date();
      futureDate.setDate(today.getDate() + days);
      
      return tasks.filter(task => {
        if (!task.dueDate || task.status === 'done') return false;
        
        const dueDate = new Date(task.dueDate);
        return dueDate >= today && dueDate <= futureDate;
      });
    } catch (error) {
      console.error(`Failed to get tasks due in ${days} days:`, error);
      throw error;
    }
  }

  /**
   * Get overdue tasks
   * @returns {Promise<Task[]>} Overdue tasks
   */
  async getOverdueTasks() {
    try {
      const tasks = await this.storage.load(this.collectionName);
      const today = new Date();
      
      return tasks.filter(task => {
        if (!task.dueDate || task.status === 'done') return false;
        
        return new Date(task.dueDate) < today;
      });
    } catch (error) {
      console.error('Failed to get overdue tasks:', error);
      throw error;
    }
  }

  /**
   * Get tasks by priority
   * @param {string} priority - Task priority
   * @returns {Promise<Task[]>} Tasks with the specified priority
   */
  async getTasksByPriority(priority) {
    try {
      const tasks = await this.storage.load(this.collectionName);
      return tasks.filter(task => task.priority === priority);
    } catch (error) {
      console.error(`Failed to get ${priority} priority tasks:`, error);
      throw error;
    }
  }

  /**
   * Mark a task as complete
   * @param {string} id - Task ID
   * @returns {Promise<Task|null>} Updated task or null
   */
  async markAsComplete(id) {
    try {
      const tasks = await this.storage.load(this.collectionName);
      const index = tasks.findIndex(task => task.id === id);
      
      if (index === -1) {
        return null;
      }
      
      // Update task status
      tasks[index] = {
        ...tasks[index],
        status: 'done',
        updatedAt: new Date().toISOString()
      };
      
      await this.storage.save(this.collectionName, tasks);
      return tasks[index];
    } catch (error) {
      console.error(`Failed to mark task ${id} as complete:`, error);
      throw error;
    }
  }
}

module.exports = TaskRepository;
