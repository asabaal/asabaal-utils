/**
 * Main Application Script
 * Handles navigation, events, and app logic
 */

// Global state object
const state = {
  currentPage: 'dashboard',
  projects: [],
  tasks: [],
  selectedProject: null,
  selectedTask: null,
  deleteCallback: null,
  filters: {
    projects: {
      category: '',
      status: '',
      search: ''
    },
    tasks: {
      project: '',
      status: '',
      priority: '',
      search: ''
    }
  }
};

// Document ready function
document.addEventListener('DOMContentLoaded', () => {
  // Initialize app
  initApp();
});

/**
 * Initialize the application
 */
async function initApp() {
  // Set up event listeners
  setupEventListeners();
  
  // Load initial data
  try {
    // Show loading indicator
    UI.showLoading();
    
    // Load dashboard page by default
    await loadDashboard();
    
    // Hide loading indicator
    UI.hideLoading();
  } catch (error) {
    console.error('Failed to initialize app:', error);
    UI.hideLoading();
    UI.showAlert(`Failed to initialize app: ${error.message}`, 'danger');
  }
}

/**
 * Set up event listeners
 */
function setupEventListeners() {
  // Navigation links
  document.querySelectorAll('[data-page]').forEach(link => {
    link.addEventListener('click', handleNavigation);
  });
  
  // Add button
  elements.addButton.addEventListener('click', handleAddButton);
  
  // Project form
  elements.saveProject.addEventListener('click', handleSaveProject);
  
  // Task form
  elements.saveTask.addEventListener('click', handleSaveTask);
  
  // Delete confirmation
  elements.confirmDeleteButton.addEventListener('click', handleConfirmDelete);
  
  // Project filters
  elements.projectFilter.addEventListener('change', handleProjectFilter);
  elements.statusFilter.addEventListener('change', handleProjectFilter);
  elements.projectSearch.addEventListener('input', handleProjectFilter);
  elements.clearSearch.addEventListener('click', clearProjectFilters);
  
  // Task filters
  elements.taskProjectFilter.addEventListener('change', handleTaskFilter);
  elements.taskStatusFilter.addEventListener('change', handleTaskFilter);
  elements.taskPriorityFilter.addEventListener('change', handleTaskFilter);
  elements.taskSearch.addEventListener('input', handleTaskFilter);
  elements.clearTaskSearch.addEventListener('click', clearTaskFilters);
  
  // Timeline update
  elements.updateTimeline.addEventListener('click', handleUpdateTimeline);
  
  // Set initial timeline dates
  const today = new Date();
  const startDate = new Date(today);
  startDate.setDate(startDate.getDate() - 30); // 30 days ago
  
  const endDate = new Date(today);
  endDate.setDate(endDate.getDate() + 90); // 90 days ahead
  
  elements.timelineStart.value = startDate.toISOString().split('T')[0];
  elements.timelineEnd.value = endDate.toISOString().split('T')[0];
  
  // Window popstate event for browser history
  window.addEventListener('popstate', handlePopState);
}

/**
 * Handle navigation click
 * @param {Event} event - Click event
 */
async function handleNavigation(event) {
  event.preventDefault();
  
  const page = event.target.dataset.page;
  
  if (page && page !== state.currentPage) {
    // Update history state
    history.pushState({ page }, '', `#${page}`);
    
    // Navigate to page
    await navigateToPage(page);
  }
}

/**
 * Handle popstate event (browser back/forward buttons)
 * @param {Event} event - Popstate event
 */
async function handlePopState(event) {
  const page = event.state?.page || 'dashboard';
  await navigateToPage(page);
}

/**
 * Navigate to a specific page
 * @param {string} page - Page identifier
 */
async function navigateToPage(page) {
  try {
    // Show loading indicator
    UI.showLoading();
    
    // Update active navigation link
    document.querySelectorAll('[data-page]').forEach(link => {
      link.parentElement.classList.remove('active');
      if (link.dataset.page === page) {
        link.parentElement.classList.add('active');
      }
    });
    
    // Handle page navigation
    switch (page) {
      case 'dashboard':
        await loadDashboard();
        break;
      case 'projects':
        await loadProjects();
        break;
      case 'tasks':
        await loadTasks();
        break;
      case 'timeline':
        await loadTimeline();
        break;
      default:
        // Default to dashboard
        await loadDashboard();
        page = 'dashboard';
    }
    
    // Update current page
    state.currentPage = page;
    
    // Hide loading indicator
    UI.hideLoading();
  } catch (error) {
    console.error(`Failed to navigate to ${page}:`, error);
    UI.hideLoading();
    UI.showAlert(`Failed to load ${page}: ${error.message}`, 'danger');
  }
}

/**
 * Load dashboard page
 */
async function loadDashboard() {
  try {
    // Show dashboard page
    UI.showPage('dashboard-page', 'Dashboard');
    
    // Fetch dashboard data
    const data = await api.getDashboard();
    
    // Update dashboard UI
    UI.updateDashboardStats(data);
    
    // Load recent activity (using overdue and upcoming tasks as activity)
    const overdueTasks = await api.getOverdueTasks();
    const upcomingTasks = await api.getUpcomingTasks(7);
    
    // Sort tasks by due date
    const recentActivity = [...overdueTasks, ...upcomingTasks].sort((a, b) => {
      if (!a.dueDate) return 1;
      if (!b.dueDate) return -1;
      return new Date(a.dueDate) - new Date(b.dueDate);
    });
    
    // Render recent activity
    elements.recentActivity.innerHTML = '';
    
    if (recentActivity.length === 0) {
      elements.recentActivity.innerHTML = `
        <div class="list-group-item">
          <p class="mb-0">No recent activity found.</p>
        </div>
      `;
    } else {
      // Show up to 10 items
      const items = recentActivity.slice(0, 10);
      
      for (const task of items) {
        const isOverdue = UI.isTaskOverdue(task);
        const itemClass = isOverdue ? 'list-group-item-danger' : 'list-group-item-warning';
        const statusText = isOverdue ? 'Overdue' : 'Due soon';
        
        const item = `
          <div class="list-group-item ${itemClass}">
            <div class="d-flex w-100 justify-content-between">
              <h5 class="mb-1">${task.name}</h5>
              <small>${task.dueDate ? UI.formatDate(task.dueDate) : 'No due date'}</small>
            </div>
            <p class="mb-1">${task.description ? task.description.substring(0, 100) + (task.description.length > 100 ? '...' : '') : 'No description'}</p>
            <div class="d-flex justify-content-between align-items-center">
              <small>${statusText} - ${UI.getTaskPriorityBadge(task.priority)}</small>
              <button class="btn btn-sm btn-outline-primary view-task" data-id="${task.id}">View</button>
            </div>
          </div>
        `;
        
        elements.recentActivity.insertAdjacentHTML('beforeend', item);
      }
    }
    
    // Add event listeners for task view buttons
    document.querySelectorAll('.view-task').forEach(button => {
      button.addEventListener('click', async () => {
        const taskId = button.dataset.id;
        await loadTaskDetail(taskId);
      });
    });
  } catch (error) {
    console.error('Failed to load dashboard:', error);
    throw error;
  }
}

/**
 * Load projects page
 */
async function loadProjects() {
  try {
    // Show projects page
    UI.showPage('projects-page', 'Projects', true);
    
    // Fetch projects
    state.projects = await api.getProjects();
    
    // Filter projects based on current filters
    const filteredProjects = filterProjects(state.projects);
    
    // Render projects table
    UI.renderProjectsTable(filteredProjects);
    
    // Add event listeners for project actions
    setupProjectEventListeners();
  } catch (error) {
    console.error('Failed to load projects:', error);
    throw error;
  }
}

/**
 * Load tasks page
 */
async function loadTasks() {
  try {
    // Show tasks page
    UI.showPage('tasks-page', 'Tasks', true);
    
    // Fetch tasks and projects
    [state.tasks, state.projects] = await Promise.all([
      api.getTasks(),
      api.getProjects()
    ]);
    
    // Update project filter select
    populateTaskProjectFilter();
    
    // Filter tasks based on current filters
    const filteredTasks = filterTasks(state.tasks);
    
    // Render tasks table
    UI.renderTasksTable(filteredTasks, state.projects);
    
    // Add event listeners for task actions
    setupTaskEventListeners();
  } catch (error) {
    console.error('Failed to load tasks:', error);
    throw error;
  }
}

/**
 * Load timeline page
 */
async function loadTimeline() {
  try {
    // Show timeline page
    UI.showPage('timeline-page', 'Timeline');
    
    // Get timeline data
    const startDate = elements.timelineStart.value;
    const endDate = elements.timelineEnd.value;
    
    const data = await api.getTimelineData(startDate, endDate);
    
    // Render timeline
    UI.renderTimeline(data);
    
    // Add event listeners for timeline items
    setupTimelineEventListeners();
  } catch (error) {
    console.error('Failed to load timeline:', error);
    throw error;
  }
}

/**
 * Load project detail
 * @param {string} projectId - Project ID
 */
async function loadProjectDetail(projectId) {
  try {
    // Show loading indicator
    UI.showLoading();
    
    // Fetch project data
    const data = await api.getProject(projectId);
    
    if (!data) {
      UI.hideLoading();
      UI.showAlert('Project not found', 'danger');
      return;
    }
    
    // Store selected project
    state.selectedProject = data.project;
    
    // Update history state
    history.pushState({ page: 'project-detail', id: projectId }, '', `#project/${projectId}`);
    
    // Show project detail page
    UI.showPage('project-detail-page', data.project.name);
    
    // Render project detail
    UI.renderProjectDetail(data);
    
    // Add event listeners for project detail actions
    setupProjectDetailEventListeners();
    
    // Hide loading indicator
    UI.hideLoading();
  } catch (error) {
    console.error(`Failed to load project ${projectId}:`, error);
    UI.hideLoading();
    UI.showAlert(`Failed to load project: ${error.message}`, 'danger');
  }
}

/**
 * Load task detail
 * @param {string} taskId - Task ID
 */
async function loadTaskDetail(taskId) {
  try {
    // Show loading indicator
    UI.showLoading();
    
    // Find task in state
    const task = state.tasks.find(t => t.id === taskId);
    
    if (!task) {
      UI.hideLoading();
      UI.showAlert('Task not found', 'danger');
      return;
    }
    
    // Store selected task
    state.selectedTask = task;
    
    // Update history state
    history.pushState({ page: 'task-detail', id: taskId }, '', `#task/${taskId}`);
    
    // Show edit task modal
    UI.populateTaskForm(task);
    elements.taskModalLabel.textContent = 'Edit Task';
    elements.taskModal.show();
    
    // Hide loading indicator
    UI.hideLoading();
  } catch (error) {
    console.error(`Failed to load task ${taskId}:`, error);
    UI.hideLoading();
    UI.showAlert(`Failed to load task: ${error.message}`, 'danger');
  }
}

/**
 * Handle add button click
 */
function handleAddButton() {
  if (state.currentPage === 'projects') {
    // Show add project modal
    UI.resetProjectForm();
    elements.projectModalLabel.textContent = 'Add New Project';
    elements.projectModal.show();
  } else if (state.currentPage === 'tasks') {
    // Show add task modal
    UI.resetTaskForm();
    UI.populateProjectSelect(state.projects);
    elements.taskModalLabel.textContent = 'Add New Task';
    elements.taskModal.show();
  }
}

/**
 * Handle save project
 */
async function handleSaveProject() {
  try {
    // Get project data from form
    const projectData = UI.getProjectFormData();
    
    // Validate form
    if (!projectData.name) {
      UI.showAlert('Project name is required', 'danger');
      return;
    }
    
    if (!projectData.startDate || !projectData.endDate) {
      UI.showAlert('Start and end dates are required', 'danger');
      return;
    }
    
    // Show loading indicator
    UI.showLoading();
    
    // Check if editing or creating
    if (projectData.id) {
      // Update project
      await api.updateProject(projectData.id, projectData);
      UI.showAlert('Project updated successfully', 'success');
    } else {
      // Create project
      await api.createProject(projectData);
      UI.showAlert('Project created successfully', 'success');
    }
    
    // Hide modal
    elements.projectModal.hide();
    
    // Reload current page
    if (state.currentPage === 'projects') {
      await loadProjects();
    } else if (state.currentPage === 'dashboard') {
      await loadDashboard();
    } else if (state.currentPage === 'timeline') {
      await loadTimeline();
    }
    
    // Hide loading indicator
    UI.hideLoading();
  } catch (error) {
    console.error('Failed to save project:', error);
    UI.hideLoading();
    UI.showAlert(`Failed to save project: ${error.message}`, 'danger');
  }
}

/**
 * Handle save task
 */
async function handleSaveTask() {
  try {
    // Get task data from form
    const taskData = UI.getTaskFormData();
    
    // Validate form
    if (!taskData.name) {
      UI.showAlert('Task name is required', 'danger');
      return;
    }
    
    if (!taskData.projectId) {
      UI.showAlert('Project is required', 'danger');
      return;
    }
    
    // Show loading indicator
    UI.showLoading();
    
    // Check if editing or creating
    if (taskData.id) {
      // Update task
      await api.updateTask(taskData.id, taskData);
      UI.showAlert('Task updated successfully', 'success');
    } else {
      // Create task
      await api.createTask(taskData);
      UI.showAlert('Task created successfully', 'success');
    }
    
    // Hide modal
    elements.taskModal.hide();
    
    // Reload current page
    if (state.currentPage === 'tasks') {
      await loadTasks();
    } else if (state.currentPage === 'dashboard') {
      await loadDashboard();
    } else if (state.currentPage === 'project-detail') {
      await loadProjectDetail(state.selectedProject.id);
    }
    
    // Hide loading indicator
    UI.hideLoading();
  } catch (error) {
    console.error('Failed to save task:', error);
    UI.hideLoading();
    UI.showAlert(`Failed to save task: ${error.message}`, 'danger');
  }
}

/**
 * Set up project event listeners
 */
function setupProjectEventListeners() {
  // Project links
  document.querySelectorAll('.project-link').forEach(link => {
    link.addEventListener('click', async (event) => {
      event.preventDefault();
      const projectId = link.dataset.id;
      await loadProjectDetail(projectId);
    });
  });
  
  // Edit project buttons
  document.querySelectorAll('.edit-project').forEach(button => {
    button.addEventListener('click', async () => {
      const projectId = button.dataset.id;
      const project = state.projects.find(p => p.id === projectId);
      
      if (project) {
        UI.populateProjectForm(project);
        elements.projectModalLabel.textContent = 'Edit Project';
        elements.projectModal.show();
      }
    });
  });
  
  // Delete project buttons
  document.querySelectorAll('.delete-project').forEach(button => {
    button.addEventListener('click', () => {
      const projectId = button.dataset.id;
      const project = state.projects.find(p => p.id === projectId);
      
      if (project) {
        elements.deleteMessage.textContent = `Are you sure you want to delete project "${project.name}"? This will also delete all tasks associated with this project.`;
        
        state.deleteCallback = async () => {
          try {
            UI.showLoading();
            await api.deleteProject(projectId);
            UI.showAlert('Project deleted successfully', 'success');
            await loadProjects();
            UI.hideLoading();
          } catch (error) {
            console.error('Failed to delete project:', error);
            UI.hideLoading();
            UI.showAlert(`Failed to delete project: ${error.message}`, 'danger');
          }
        };
        
        elements.confirmDeleteModal.show();
      }
    });
  });
}

/**
 * Set up task event listeners
 */
function setupTaskEventListeners() {
  // Task links
  document.querySelectorAll('.task-link').forEach(link => {
    link.addEventListener('click', async (event) => {
      event.preventDefault();
      const taskId = link.dataset.id;
      await loadTaskDetail(taskId);
    });
  });
  
  // Edit task buttons
  document.querySelectorAll('.edit-task').forEach(button => {
    button.addEventListener('click', async () => {
      const taskId = button.dataset.id;
      const task = state.tasks.find(t => t.id === taskId);
      
      if (task) {
        UI.populateTaskForm(task);
        UI.populateProjectSelect(state.projects, task.projectId);
        elements.taskModalLabel.textContent = 'Edit Task';
        elements.taskModal.show();
      }
    });
  });
  
  // Complete task buttons
  document.querySelectorAll('.complete-task').forEach(button => {
    button.addEventListener('click', async () => {
      const taskId = button.dataset.id;
      
      try {
        UI.showLoading();
        await api.completeTask(taskId);
        UI.showAlert('Task marked as complete', 'success');
        
        // Reload current page
        if (state.currentPage === 'tasks') {
          await loadTasks();
        } else if (state.currentPage === 'dashboard') {
          await loadDashboard();
        }
        
        UI.hideLoading();
      } catch (error) {
        console.error('Failed to complete task:', error);
        UI.hideLoading();
        UI.showAlert(`Failed to complete task: ${error.message}`, 'danger');
      }
    });
  });
  
  // Delete task buttons
  document.querySelectorAll('.delete-task').forEach(button => {
    button.addEventListener('click', () => {
      const taskId = button.dataset.id;
      const task = state.tasks.find(t => t.id === taskId);
      
      if (task) {
        elements.deleteMessage.textContent = `Are you sure you want to delete task "${task.name}"?`;
        
        state.deleteCallback = async () => {
          try {
            UI.showLoading();
            await api.deleteTask(taskId);
            UI.showAlert('Task deleted successfully', 'success');
            
            // Reload current page
            if (state.currentPage === 'tasks') {
              await loadTasks();
            } else if (state.currentPage === 'dashboard') {
              await loadDashboard();
            } else if (state.currentPage === 'project-detail') {
              await loadProjectDetail(state.selectedProject.id);
            }
            
            UI.hideLoading();
          } catch (error) {
            console.error('Failed to delete task:', error);
            UI.hideLoading();
            UI.showAlert(`Failed to delete task: ${error.message}`, 'danger');
          }
        };
        
        elements.confirmDeleteModal.show();
      }
    });
  });
}

/**
 * Set up timeline event listeners
 */
function setupTimelineEventListeners() {
  // Project links
  document.querySelectorAll('.project-link').forEach(link => {
    link.addEventListener('click', async (event) => {
      event.preventDefault();
      const projectId = link.dataset.id;
      await loadProjectDetail(projectId);
    });
  });
}

/**
 * Set up project detail event listeners
 */
function setupProjectDetailEventListeners() {
  // Edit project button
  document.querySelector('.edit-project-detail').addEventListener('click', () => {
    UI.populateProjectForm(state.selectedProject);
    elements.projectModalLabel.textContent = 'Edit Project';
    elements.projectModal.show();
  });
  
  // Add task button
  document.querySelector('.add-task-detail').addEventListener('click', () => {
    UI.resetTaskForm();
    elements.taskProject.value = state.selectedProject.id;
    elements.taskModalLabel.textContent = 'Add New Task';
    elements.taskModal.show();
  });
  
  // Complete task checkboxes
  document.querySelectorAll('.complete-task-checkbox').forEach(checkbox => {
    checkbox.addEventListener('change', async () => {
      if (checkbox.checked) {
        const taskId = checkbox.dataset.id;
        
        try {
          UI.showLoading();
          await api.completeTask(taskId);
          UI.showAlert('Task marked as complete', 'success');
          await loadProjectDetail(state.selectedProject.id);
          UI.hideLoading();
        } catch (error) {
          console.error('Failed to complete task:', error);
          UI.hideLoading();
          UI.showAlert(`Failed to complete task: ${error.message}`, 'danger');
          checkbox.checked = false;
        }
      }
    });
  });
  
  // Edit task buttons
  document.querySelectorAll('.edit-task').forEach(button => {
    button.addEventListener('click', async () => {
      const taskId = button.dataset.id;
      const task = state.tasks.find(t => t.id === taskId);
      
      if (!task) {
        // Fetch all tasks if not found in state
        state.tasks = await api.getTasks();
      }
      
      const updatedTask = state.tasks.find(t => t.id === taskId);
      
      if (updatedTask) {
        UI.populateTaskForm(updatedTask);
        UI.populateProjectSelect([state.selectedProject], state.selectedProject.id);
        elements.taskModalLabel.textContent = 'Edit Task';
        elements.taskModal.show();
      }
    });
  });
  
  // Delete task buttons
  document.querySelectorAll('.delete-task').forEach(button => {
    button.addEventListener('click', () => {
      const taskId = button.dataset.id;
      
      // Find task in project tasks
      const task = state.selectedProject.tasks?.find(t => t.id === taskId);
      
      if (task) {
        elements.deleteMessage.textContent = `Are you sure you want to delete task "${task.name}"?`;
        
        state.deleteCallback = async () => {
          try {
            UI.showLoading();
            await api.deleteTask(taskId);
            UI.showAlert('Task deleted successfully', 'success');
            await loadProjectDetail(state.selectedProject.id);
            UI.hideLoading();
          } catch (error) {
            console.error('Failed to delete task:', error);
            UI.hideLoading();
            UI.showAlert(`Failed to delete task: ${error.message}`, 'danger');
          }
        };
        
        elements.confirmDeleteModal.show();
      }
    });
  });
}

/**
 * Handle confirm delete
 */
function handleConfirmDelete() {
  elements.confirmDeleteModal.hide();
  
  if (state.deleteCallback) {
    state.deleteCallback();
    state.deleteCallback = null;
  }
}

/**
 * Handle project filter change
 */
function handleProjectFilter() {
  state.filters.projects.category = elements.projectFilter.value;
  state.filters.projects.status = elements.statusFilter.value;
  state.filters.projects.search = elements.projectSearch.value.toLowerCase();
  
  const filteredProjects = filterProjects(state.projects);
  UI.renderProjectsTable(filteredProjects);
  setupProjectEventListeners();
}

/**
 * Clear project filters
 */
function clearProjectFilters() {
  elements.projectFilter.value = '';
  elements.statusFilter.value = '';
  elements.projectSearch.value = '';
  
  state.filters.projects.category = '';
  state.filters.projects.status = '';
  state.filters.projects.search = '';
  
  const filteredProjects = filterProjects(state.projects);
  UI.renderProjectsTable(filteredProjects);
  setupProjectEventListeners();
}

/**
 * Handle task filter change
 */
function handleTaskFilter() {
  state.filters.tasks.project = elements.taskProjectFilter.value;
  state.filters.tasks.status = elements.taskStatusFilter.value;
  state.filters.tasks.priority = elements.taskPriorityFilter.value;
  state.filters.tasks.search = elements.taskSearch.value.toLowerCase();
  
  const filteredTasks = filterTasks(state.tasks);
  UI.renderTasksTable(filteredTasks, state.projects);
  setupTaskEventListeners();
}

/**
 * Clear task filters
 */
function clearTaskFilters() {
  elements.taskProjectFilter.value = '';
  elements.taskStatusFilter.value = '';
  elements.taskPriorityFilter.value = '';
  elements.taskSearch.value = '';
  
  state.filters.tasks.project = '';
  state.filters.tasks.status = '';
  state.filters.tasks.priority = '';
  state.filters.tasks.search = '';
  
  const filteredTasks = filterTasks(state.tasks);
  UI.renderTasksTable(filteredTasks, state.projects);
  setupTaskEventListeners();
}

/**
 * Handle update timeline
 */
async function handleUpdateTimeline() {
  try {
    UI.showLoading();
    await loadTimeline();
    UI.hideLoading();
  } catch (error) {
    console.error('Failed to update timeline:', error);
    UI.hideLoading();
    UI.showAlert(`Failed to update timeline: ${error.message}`, 'danger');
  }
}

/**
 * Filter projects based on current filters
 * @param {Array} projects - List of projects to filter
 * @returns {Array} Filtered projects
 */
function filterProjects(projects) {
  return projects.filter(project => {
    // Filter by category
    if (state.filters.projects.category && project.category !== state.filters.projects.category) {
      return false;
    }
    
    // Filter by status
    if (state.filters.projects.status && project.status !== state.filters.projects.status) {
      return false;
    }
    
    // Filter by search
    if (state.filters.projects.search) {
      const searchStr = state.filters.projects.search.toLowerCase();
      return (
        project.name.toLowerCase().includes(searchStr) ||
        project.description.toLowerCase().includes(searchStr) ||
        project.tags.some(tag => tag.toLowerCase().includes(searchStr))
      );
    }
    
    return true;
  });
}

/**
 * Filter tasks based on current filters
 * @param {Array} tasks - List of tasks to filter
 * @returns {Array} Filtered tasks
 */
function filterTasks(tasks) {
  return tasks.filter(task => {
    // Filter by project
    if (state.filters.tasks.project && task.projectId !== state.filters.tasks.project) {
      return false;
    }
    
    // Filter by status
    if (state.filters.tasks.status && task.status !== state.filters.tasks.status) {
      return false;
    }
    
    // Filter by priority
    if (state.filters.tasks.priority && task.priority !== state.filters.tasks.priority) {
      return false;
    }
    
    // Filter by search
    if (state.filters.tasks.search) {
      const searchStr = state.filters.tasks.search.toLowerCase();
      return (
        task.name.toLowerCase().includes(searchStr) ||
        task.description.toLowerCase().includes(searchStr) ||
        (task.assignee && task.assignee.toLowerCase().includes(searchStr))
      );
    }
    
    return true;
  });
}

/**
 * Populate task project filter select
 */
function populateTaskProjectFilter() {
  elements.taskProjectFilter.innerHTML = '<option value="">All Projects</option>';
  
  for (const project of state.projects) {
    const option = document.createElement('option');
    option.value = project.id;
    option.textContent = project.name;
    elements.taskProjectFilter.appendChild(option);
  }
}

// Check for URL hash on load and navigate to the appropriate page
if (window.location.hash) {
  const hash = window.location.hash.substring(1);
  
  if (hash.startsWith('project/')) {
    const projectId = hash.split('/')[1];
    loadProjectDetail(projectId);
  } else if (hash.startsWith('task/')) {
    const taskId = hash.split('/')[1];
    loadTaskDetail(taskId);
  } else if (['dashboard', 'projects', 'tasks', 'timeline'].includes(hash)) {
    history.replaceState({ page: hash }, '', `#${hash}`);
    navigateToPage(hash);
  }
}
