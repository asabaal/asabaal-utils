/**
 * Project Repository
 * Handles CRUD operations for projects
 */

const { Project } = require('../models');

class ProjectRepository {
  constructor(storage) {
    this.storage = storage;
    this.collectionName = 'projects';
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
      console.error('Failed to initialize project repository:', error);
      throw error;
    }
  }

  /**
   * Get all projects
   * @param {Object} filters - Optional filters
   * @returns {Promise<Project[]>} List of projects
   */
  async getAll(filters = {}) {
    try {
      const projects = await this.storage.load(this.collectionName);
      
      // Apply filters if provided
      if (Object.keys(filters).length === 0) {
        return projects;
      }
      
      return projects.filter(project => {
        return Object.entries(filters).every(([key, value]) => {
          // Handle date range filters
          if (key === 'startDateFrom' && value) {
            return new Date(project.startDate) >= new Date(value);
          }
          if (key === 'startDateTo' && value) {
            return new Date(project.startDate) <= new Date(value);
          }
          if (key === 'endDateFrom' && value) {
            return new Date(project.endDate) >= new Date(value);
          }
          if (key === 'endDateTo' && value) {
            return new Date(project.endDate) <= new Date(value);
          }
          
          // Handle array contains filter
          if (key === 'tags' && Array.isArray(value)) {
            return value.every(tag => project.tags.includes(tag));
          }
          
          // Default equality check
          return project[key] === value;
        });
      });
    } catch (error) {
      console.error('Failed to get projects:', error);
      throw error;
    }
  }

  /**
   * Get a project by ID
   * @param {string} id - Project ID
   * @returns {Promise<Project|null>} Found project or null
   */
  async getById(id) {
    try {
      const projects = await this.storage.load(this.collectionName);
      return projects.find(project => project.id === id) || null;
    } catch (error) {
      console.error(`Failed to get project ${id}:`, error);
      throw error;
    }
  }

  /**
   * Create a new project
   * @param {Object} projectData - Project data
   * @returns {Promise<Project>} Created project
   */
  async create(projectData) {
    try {
      const projects = await this.storage.load(this.collectionName);
      
      // Create new project instance
      const project = new Project(projectData);
      
      // Save to storage
      projects.push(project);
      await this.storage.save(this.collectionName, projects);
      
      return project;
    } catch (error) {
      console.error('Failed to create project:', error);
      throw error;
    }
  }

  /**
   * Update an existing project
   * @param {string} id - Project ID
   * @param {Object} projectData - Updated project data
   * @returns {Promise<Project|null>} Updated project or null
   */
  async update(id, projectData) {
    try {
      const projects = await this.storage.load(this.collectionName);
      const index = projects.findIndex(project => project.id === id);
      
      if (index === -1) {
        return null;
      }
      
      // Update project
      const updatedProject = {
        ...projects[index],
        ...projectData,
        updatedAt: new Date().toISOString()
      };
      
      projects[index] = updatedProject;
      await this.storage.save(this.collectionName, projects);
      
      return updatedProject;
    } catch (error) {
      console.error(`Failed to update project ${id}:`, error);
      throw error;
    }
  }

  /**
   * Delete a project
   * @param {string} id - Project ID
   * @returns {Promise<boolean>} True if deleted
   */
  async delete(id) {
    try {
      const projects = await this.storage.load(this.collectionName);
      const filteredProjects = projects.filter(project => project.id !== id);
      
      if (filteredProjects.length === projects.length) {
        return false; // Project not found
      }
      
      await this.storage.save(this.collectionName, filteredProjects);
      return true;
    } catch (error) {
      console.error(`Failed to delete project ${id}:`, error);
      throw error;
    }
  }

  /**
   * Get projects due for a specific period
   * @param {Date} startDate - Period start
   * @param {Date} endDate - Period end
   * @returns {Promise<Project[]>} Projects due in the period
   */
  async getProjectsForPeriod(startDate, endDate) {
    try {
      const projects = await this.storage.load(this.collectionName);
      const start = new Date(startDate);
      const end = new Date(endDate);
      
      return projects.filter(project => {
        const projectStart = new Date(project.startDate);
        const projectEnd = new Date(project.endDate);
        
        // Project starts or ends within the period
        // Or project spans the entire period
        return (
          (projectStart >= start && projectStart <= end) ||
          (projectEnd >= start && projectEnd <= end) ||
          (projectStart <= start && projectEnd >= end)
        );
      });
    } catch (error) {
      console.error('Failed to get projects for period:', error);
      throw error;
    }
  }

  /**
   * Get active projects (in progress)
   * @returns {Promise<Project[]>} Active projects
   */
  async getActiveProjects() {
    try {
      const projects = await this.storage.load(this.collectionName);
      return projects.filter(
        project => project.status === 'in_progress'
      );
    } catch (error) {
      console.error('Failed to get active projects:', error);
      throw error;
    }
  }

  /**
   * Get overdue projects
   * @returns {Promise<Project[]>} Overdue projects
   */
  async getOverdueProjects() {
    try {
      const projects = await this.storage.load(this.collectionName);
      const today = new Date();
      
      return projects.filter(project => {
        return (
          project.status !== 'completed' &&
          project.status !== 'cancelled' &&
          new Date(project.endDate) < today
        );
      });
    } catch (error) {
      console.error('Failed to get overdue projects:', error);
      throw error;
    }
  }
}

module.exports = ProjectRepository;
