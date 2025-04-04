/**
 * API Client for Project Management System
 * Handles all interactions with the backend REST API
 */

class ApiClient {
  /**
   * Initialize the API client
   * @param {string} baseUrl - API base URL (default: current host)
   */
  constructor(baseUrl = '') {
    this.baseUrl = baseUrl || `${window.location.protocol}//${window.location.host}`;
    this.apiPath = '/api';
  }

  /**
   * Build the full URL for an API endpoint
   * @param {string} endpoint - API endpoint
   * @returns {string} Full URL
   */
  buildUrl(endpoint) {
    return `${this.baseUrl}${this.apiPath}${endpoint}`;
  }

  /**
   * Make an API request
   * @param {string} endpoint - API endpoint
   * @param {string} method - HTTP method
   * @param {Object} data - Request data (for POST/PUT)
   * @returns {Promise<Object>} Response data
   */
  async request(endpoint, method = 'GET', data = null) {
    const url = this.buildUrl(endpoint);
    
    const options = {
      method,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    };
    
    if (data && (method === 'POST' || method === 'PUT')) {
      options.body = JSON.stringify(data);
    }
    
    try {
      const response = await fetch(url, options);
      
      // Check if the response is JSON
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        const jsonData = await response.json();
        
        // Check for error response
        if (!response.ok) {
          throw new Error(jsonData.error || `API error: ${response.status}`);
        }
        
        return jsonData;
      } else {
        // Handle non-JSON response
        if (!response.ok) {
          const text = await response.text();
          throw new Error(text || `API error: ${response.status}`);
        }
        
        return await response.text();
      }
    } catch (error) {
      console.error(`API request failed: ${url}`, error);
      throw error;
    }
  }

  // Dashboard methods
  
  /**
   * Get dashboard summary data
   * @returns {Promise<Object>} Dashboard data
   */
  async getDashboard() {
    return this.request('/dashboard');
  }
  
  // Project methods
  
  /**
   * Get all projects
   * @returns {Promise<Array>} List of projects
   */
  async getProjects() {
    return this.request('/projects');
  }
  
  /**
   * Get a project by ID
   * @param {string} id - Project ID
   * @returns {Promise<Object>} Project with tasks
   */
  async getProject(id) {
    return this.request(`/projects/${id}`);
  }
  
  /**
   * Create a new project
   * @param {Object} project - Project data
   * @param {Array} tasks - Optional tasks to create
   * @returns {Promise<Object>} Created project with tasks
   */
  async createProject(project, tasks = []) {
    return this.request('/projects', 'POST', { project, tasks });
  }
  
  /**
   * Update a project
   * @param {string} id - Project ID
   * @param {Object} project - Updated project data
   * @param {Array} tasksToUpdate - Optional tasks to update
   * @param {Array} tasksToAdd - Optional new tasks to add
   * @param {Array} taskIdsToRemove - Optional task IDs to remove
   * @returns {Promise<Object>} Updated project with tasks
   */
  async updateProject(id, project, tasksToUpdate = [], tasksToAdd = [], taskIdsToRemove = []) {
    return this.request(`/projects/${id}`, 'PUT', {
      project,
      tasksToUpdate,
      tasksToAdd,
      taskIdsToRemove
    });
  }
  
  /**
   * Delete a project
   * @param {string} id - Project ID
   * @returns {Promise<Object>} Success status
   */
  async deleteProject(id) {
    return this.request(`/projects/${id}`, 'DELETE');
  }
  
  /**
   * Get project status
   * @param {string} id - Project ID
   * @returns {Promise<Object>} Project status
   */
  async getProjectStatus(id) {
    return this.request(`/projects/${id}/status`);
  }
  
  // Task methods
  
  /**
   * Get all tasks
   * @returns {Promise<Array>} List of tasks
   */
  async getTasks() {
    return this.request('/tasks');
  }
  
  /**
   * Get tasks for a project
   * @param {string} projectId - Project ID
   * @returns {Promise<Array>} List of tasks
   */
  async getProjectTasks(projectId) {
    return this.request(`/projects/${projectId}/tasks`);
  }
  
  /**
   * Create a new task
   * @param {Object} task - Task data
   * @returns {Promise<Object>} Created task
   */
  async createTask(task) {
    return this.request('/tasks', 'POST', task);
  }
  
  /**
   * Update a task
   * @param {string} id - Task ID
   * @param {Object} task - Updated task data
   * @returns {Promise<Object>} Updated task
   */
  async updateTask(id, task) {
    return this.request(`/tasks/${id}`, 'PUT', task);
  }
  
  /**
   * Delete a task
   * @param {string} id - Task ID
   * @returns {Promise<Object>} Success status
   */
  async deleteTask(id) {
    return this.request(`/tasks/${id}`, 'DELETE');
  }
  
  /**
   * Mark a task as complete
   * @param {string} id - Task ID
   * @returns {Promise<Object>} Updated task
   */
  async completeTask(id) {
    return this.request(`/tasks/${id}/complete`, 'PUT');
  }
  
  /**
   * Get overdue tasks
   * @returns {Promise<Array>} List of overdue tasks
   */
  async getOverdueTasks() {
    return this.request('/tasks/overdue');
  }
  
  /**
   * Get upcoming tasks
   * @param {number} days - Number of days to look ahead
   * @returns {Promise<Array>} List of upcoming tasks
   */
  async getUpcomingTasks(days = 7) {
    return this.request(`/tasks/upcoming?days=${days}`);
  }
  
  // Timeline methods
  
  /**
   * Get timeline data
   * @param {string} startDate - Start date (YYYY-MM-DD)
   * @param {string} endDate - End date (YYYY-MM-DD)
   * @returns {Promise<Object>} Timeline data
   */
  async getTimelineData(startDate, endDate) {
    return this.request(`/timeline?start=${startDate}&end=${endDate}`);
  }
}

// Create a global API client instance
const api = new ApiClient();
