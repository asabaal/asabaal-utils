/**
 * UI Helper Functions
 * Contains helper functions for UI manipulations and rendering
 */

// UI Element References
const elements = {
  // Pages
  dashboardPage: document.getElementById('dashboard-page'),
  projectsPage: document.getElementById('projects-page'),
  tasksPage: document.getElementById('tasks-page'),
  timelinePage: document.getElementById('timeline-page'),
  projectDetailPage: document.getElementById('project-detail-page'),
  taskDetailPage: document.getElementById('task-detail-page'),
  
  // Common elements
  pageTitle: document.getElementById('page-title'),
  addButton: document.getElementById('add-button'),
  alertContainer: document.getElementById('alert-container'),
  loadingSpinner: document.getElementById('loading-spinner'),
  
  // Dashboard elements
  totalProjects: document.getElementById('total-projects'),
  activeProjects: document.getElementById('active-projects'),
  upcomingTasks: document.getElementById('upcoming-tasks'),
  overdueTasks: document.getElementById('overdue-tasks'),
  categoriesChart: document.getElementById('categories-chart'),
  prioritiesChart: document.getElementById('priorities-chart'),
  recentActivity: document.getElementById('recent-activity'),
  
  // Projects elements
  projectFilter: document.getElementById('project-filter'),
  statusFilter: document.getElementById('status-filter'),
  projectSearch: document.getElementById('project-search'),
  clearSearch: document.getElementById('clear-search'),
  projectsTableBody: document.getElementById('projects-table-body'),
  projectsPagination: document.getElementById('projects-pagination'),
  
  // Tasks elements
  taskProjectFilter: document.getElementById('task-project-filter'),
  taskStatusFilter: document.getElementById('task-status-filter'),
  taskPriorityFilter: document.getElementById('task-priority-filter'),
  taskSearch: document.getElementById('task-search'),
  clearTaskSearch: document.getElementById('clear-task-search'),
  tasksTableBody: document.getElementById('tasks-table-body'),
  tasksPagination: document.getElementById('tasks-pagination'),
  
  // Timeline elements
  timelineStart: document.getElementById('timeline-start'),
  timelineEnd: document.getElementById('timeline-end'),
  updateTimeline: document.getElementById('update-timeline'),
  timelineContainer: document.getElementById('timeline-container'),
  
  // Modals
  projectModal: new bootstrap.Modal(document.getElementById('project-modal')),
  projectModalLabel: document.getElementById('project-modal-label'),
  projectForm: document.getElementById('project-form'),
  projectId: document.getElementById('project-id'),
  projectName: document.getElementById('project-name'),
  projectDescription: document.getElementById('project-description'),
  projectCategory: document.getElementById('project-category'),
  projectStatus: document.getElementById('project-status'),
  projectStartDate: document.getElementById('project-start-date'),
  projectEndDate: document.getElementById('project-end-date'),
  projectRevenueTarget: document.getElementById('project-revenue-target'),
  projectRevenueActual: document.getElementById('project-revenue-actual'),
  projectTags: document.getElementById('project-tags'),
  saveProject: document.getElementById('save-project'),
  
  taskModal: new bootstrap.Modal(document.getElementById('task-modal')),
  taskModalLabel: document.getElementById('task-modal-label'),
  taskForm: document.getElementById('task-form'),
  taskId: document.getElementById('task-id'),
  taskName: document.getElementById('task-name'),
  taskDescription: document.getElementById('task-description'),
  taskProject: document.getElementById('task-project'),
  taskStatus: document.getElementById('task-status'),
  taskPriority: document.getElementById('task-priority'),
  taskDueDate: document.getElementById('task-due-date'),
  taskAssignee: document.getElementById('task-assignee'),
  saveTask: document.getElementById('save-task'),
  
  confirmDeleteModal: new bootstrap.Modal(document.getElementById('confirm-delete-modal')),
  deleteMessage: document.getElementById('delete-message'),
  confirmDeleteButton: document.getElementById('confirm-delete-button')
};

// Chart instances
let categoriesChart = null;
let prioritiesChart = null;

/**
 * UI Helper Class
 * Contains methods for UI manipulations
 */
class UI {
  /**
   * Show a page and hide others
   * @param {string} pageId - ID of the page to show
   * @param {string} title - Page title
   * @param {boolean} showAddButton - Whether to show the add button
   */
  static showPage(pageId, title, showAddButton = false) {
    // Hide all pages
    document.querySelectorAll('.page-section').forEach(page => {
      page.style.display = 'none';
    });
    
    // Show selected page
    const page = document.getElementById(pageId);
    if (page) {
      page.style.display = 'block';
    }
    
    // Update page title
    elements.pageTitle.textContent = title;
    
    // Show/hide add button
    elements.addButton.style.display = showAddButton ? 'block' : 'none';
  }
  
  /**
   * Show loading spinner
   */
  static showLoading() {
    elements.loadingSpinner.style.display = 'block';
  }
  
  /**
   * Hide loading spinner
   */
  static hideLoading() {
    elements.loadingSpinner.style.display = 'none';
  }
  
  /**
   * Show an alert message
   * @param {string} message - Alert message
   * @param {string} type - Alert type (success, danger, warning, info)
   * @param {number} duration - Duration in milliseconds (0 for persistent)
   */
  static showAlert(message, type = 'info', duration = 5000) {
    const alertId = `alert-${Date.now()}`;
    const alertHtml = `
      <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert">
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
      </div>
    `;
    
    elements.alertContainer.insertAdjacentHTML('beforeend', alertHtml);
    
    if (duration > 0) {
      setTimeout(() => {
        const alert = document.getElementById(alertId);
        if (alert) {
          alert.remove();
        }
      }, duration);
    }
  }
  
  /**
   * Clear all alerts
   */
  static clearAlerts() {
    elements.alertContainer.innerHTML = '';
  }
  
  /**
   * Update dashboard stats
   * @param {Object} data - Dashboard data
   */
  static updateDashboardStats(data) {
    elements.totalProjects.textContent = data.projects.total;
    elements.activeProjects.textContent = data.projects.active;
    elements.upcomingTasks.textContent = data.tasks.upcoming;
    elements.overdueTasks.textContent = data.tasks.overdue;
    
    // Create charts
    UI.createCategoriesChart(data.projects.byCategory);
    UI.createPrioritiesChart(data.tasks.byPriority);
  }
  
  /**
   * Create categories chart
   * @param {Object} categoriesData - Categories data
   */
  static createCategoriesChart(categoriesData) {
    const ctx = elements.categoriesChart.getContext('2d');
    
    // Destroy existing chart if it exists
    if (categoriesChart) {
      categoriesChart.destroy();
    }
    
    // Prepare data
    const labels = Object.keys(categoriesData).map(key => {
      // Format category names
      const words = key.split('_');
      return words.map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
    });
    
    const data = Object.values(categoriesData);
    
    // Create new chart
    categoriesChart = new Chart(ctx, {
      type: 'pie',
      data: {
        labels: labels,
        datasets: [{
          data: data,
          backgroundColor: [
            '#9c27b0', // Music Production
            '#28a745', // Trading
            '#fd7e14', // Content Creation
            '#17a2b8', // Technology
            '#007bff'  // Business
          ],
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            position: 'right'
          }
        }
      }
    });
  }
  
  /**
   * Create priorities chart
   * @param {Object} prioritiesData - Priorities data
   */
  static createPrioritiesChart(prioritiesData) {
    const ctx = elements.prioritiesChart.getContext('2d');
    
    // Destroy existing chart if it exists
    if (prioritiesChart) {
      prioritiesChart.destroy();
    }
    
    // Prepare data
    const labels = Object.keys(prioritiesData).map(key => {
      return key.charAt(0).toUpperCase() + key.slice(1);
    });
    
    const data = Object.values(prioritiesData);
    
    // Create new chart
    prioritiesChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Tasks by Priority',
          data: data,
          backgroundColor: [
            '#007bff', // Low
            '#6c757d', // Medium
            '#fd7e14', // High
            '#dc3545'  // Urgent
          ],
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              precision: 0
            }
          }
        },
        plugins: {
          legend: {
            display: false
          }
        }
      }
    });
  }
  
  /**
   * Render projects table
   * @param {Array} projects - List of projects
   */
  static renderProjectsTable(projects) {
    elements.projectsTableBody.innerHTML = '';
    
    if (projects.length === 0) {
      const emptyRow = `
        <tr>
          <td colspan="6" class="text-center">No projects found</td>
        </tr>
      `;
      elements.projectsTableBody.innerHTML = emptyRow;
      return;
    }
    
    for (const project of projects) {
      const statusBadge = UI.getStatusBadge(project.status);
      const progressBar = UI.getProgressBar(project.calculateProgress ? project.calculateProgress() : 0);
      
      const row = `
        <tr data-id="${project.id}">
          <td>
            <a href="#" class="project-link" data-id="${project.id}">${project.name}</a>
            <div class="small text-muted">${project.description.substring(0, 50)}${project.description.length > 50 ? '...' : ''}</div>
          </td>
          <td>${UI.formatCategory(project.category)}</td>
          <td>${statusBadge}</td>
          <td>${UI.formatDate(project.startDate)} - ${UI.formatDate(project.endDate)}</td>
          <td>${progressBar}</td>
          <td>
            <div class="btn-group btn-group-sm">
              <button type="button" class="btn btn-outline-primary edit-project" data-id="${project.id}">
                <i class="bi bi-pencil"></i>
              </button>
              <button type="button" class="btn btn-outline-danger delete-project" data-id="${project.id}">
                <i class="bi bi-trash"></i>
              </button>
            </div>
          </td>
        </tr>
      `;
      
      elements.projectsTableBody.insertAdjacentHTML('beforeend', row);
    }
  }
  
  /**
   * Render tasks table
   * @param {Array} tasks - List of tasks
   * @param {Array} projects - List of projects (for project names)
   */
  static renderTasksTable(tasks, projects) {
    elements.tasksTableBody.innerHTML = '';
    
    if (tasks.length === 0) {
      const emptyRow = `
        <tr>
          <td colspan="6" class="text-center">No tasks found</td>
        </tr>
      `;
      elements.tasksTableBody.innerHTML = emptyRow;
      return;
    }
    
    // Create a map of project IDs to names
    const projectMap = {};
    for (const project of projects) {
      projectMap[project.id] = project.name;
    }
    
    for (const task of tasks) {
      const statusBadge = UI.getTaskStatusBadge(task.status);
      const priorityBadge = UI.getTaskPriorityBadge(task.priority);
      const projectName = projectMap[task.projectId] || 'Unknown Project';
      
      const row = `
        <tr data-id="${task.id}">
          <td>
            <a href="#" class="task-link" data-id="${task.id}">${task.name}</a>
            <div class="small text-muted">${task.description.substring(0, 50)}${task.description.length > 50 ? '...' : ''}</div>
          </td>
          <td>${projectName}</td>
          <td>${statusBadge}</td>
          <td>${priorityBadge}</td>
          <td>${task.dueDate ? UI.formatDate(task.dueDate) : 'No due date'}</td>
          <td>
            <div class="btn-group btn-group-sm">
              <button type="button" class="btn btn-outline-success complete-task ${task.status === 'done' ? 'disabled' : ''}" data-id="${task.id}" ${task.status === 'done' ? 'disabled' : ''}>
                <i class="bi bi-check-lg"></i>
              </button>
              <button type="button" class="btn btn-outline-primary edit-task" data-id="${task.id}">
                <i class="bi bi-pencil"></i>
              </button>
              <button type="button" class="btn btn-outline-danger delete-task" data-id="${task.id}">
                <i class="bi bi-trash"></i>
              </button>
            </div>
          </td>
        </tr>
      `;
      
      elements.tasksTableBody.insertAdjacentHTML('beforeend', row);
    }
  }
  
  /**
   * Render timeline
   * @param {Object} data - Timeline data (projects and tasks)
   */
  static renderTimeline(data) {
    const { projects, tasks } = data;
    elements.timelineContainer.innerHTML = '';
    
    if (projects.length === 0) {
      elements.timelineContainer.innerHTML = `
        <div class="alert alert-info">No projects found in the selected date range</div>
      `;
      return;
    }
    
    // Group projects by month
    const projectsByMonth = {};
    for (const project of projects) {
      const startDate = new Date(project.startDate);
      const month = startDate.toLocaleString('default', { month: 'long', year: 'numeric' });
      
      if (!projectsByMonth[month]) {
        projectsByMonth[month] = [];
      }
      
      projectsByMonth[month].push(project);
    }
    
    // Create project tasks map
    const projectTasks = {};
    for (const task of tasks) {
      if (!projectTasks[task.projectId]) {
        projectTasks[task.projectId] = [];
      }
      
      projectTasks[task.projectId].push(task);
    }
    
    // Sort months chronologically
    const sortedMonths = Object.keys(projectsByMonth).sort((a, b) => {
      const dateA = new Date(a);
      const dateB = new Date(b);
      return dateA - dateB;
    });
    
    // Create timeline
    for (const month of sortedMonths) {
      const monthProjects = projectsByMonth[month];
      
      // Create month header
      const monthHeader = `
        <div class="timeline-month">
          <h5>${month}</h5>
        </div>
      `;
      elements.timelineContainer.insertAdjacentHTML('beforeend', monthHeader);
      
      // Create month projects
      for (const project of monthProjects) {
        const projectClass = `timeline-project-${project.category.split('_')[0]}`;
        
        // Format project dates
        const startDate = new Date(project.startDate);
        const endDate = new Date(project.endDate);
        const dateRange = `${startDate.toLocaleDateString()} - ${endDate.toLocaleDateString()}`;
        
        // Get project tasks
        const tasks = projectTasks[project.id] || [];
        let tasksHtml = '';
        
        if (tasks.length > 0) {
          tasksHtml = '<div class="timeline-tasks">';
          
          for (const task of tasks) {
            const isDone = task.status === 'done';
            const isOverdue = UI.isTaskOverdue(task);
            const taskClasses = [
              'timeline-task',
              `task-${task.status}`,
              isOverdue ? 'task-overdue' : ''
            ].filter(Boolean).join(' ');
            
            tasksHtml += `
              <div class="${taskClasses}">
                ${isDone ? '<i class="bi bi-check-circle-fill text-success me-1"></i>' : ''}
                ${isOverdue ? '<i class="bi bi-exclamation-triangle-fill text-danger me-1"></i>' : ''}
                ${task.name}
                ${task.dueDate ? `<span class="float-end">${UI.formatDate(task.dueDate)}</span>` : ''}
              </div>
            `;
          }
          
          tasksHtml += '</div>';
        }
        
        // Create project card
        const projectCard = `
          <div class="timeline-project ${projectClass}">
            <h5>
              <a href="#" class="project-link" data-id="${project.id}">${project.name}</a>
              <span class="badge ${UI.getStatusClass(project.status)} float-end">${UI.formatStatus(project.status)}</span>
            </h5>
            <div class="timeline-date">${dateRange}</div>
            <div class="progress mt-2 mb-2">
              <div class="progress-bar" role="progressbar" style="width: ${project.calculateProgress ? project.calculateProgress() : 0}%"></div>
            </div>
            ${tasksHtml}
          </div>
        `;
        
        elements.timelineContainer.insertAdjacentHTML('beforeend', projectCard);
      }
    }
  }
  
  /**
   * Render project detail
   * @param {Object} data - Project data with tasks
   */
  static renderProjectDetail(data) {
    const { project, tasks } = data;
    elements.projectDetailPage.innerHTML = '';
    
    // Calculate project progress
    const progress = project.calculateProgress ? project.calculateProgress() : 0;
    
    // Count tasks by status
    const taskCounts = {
      total: tasks.length,
      todo: tasks.filter(t => t.status === 'todo').length,
      inProgress: tasks.filter(t => t.status === 'in_progress').length,
      review: tasks.filter(t => t.status === 'review').length,
      done: tasks.filter(t => t.status === 'done').length,
      overdue: tasks.filter(t => UI.isTaskOverdue(t)).length
    };
    
    // Create project header
    const header = `
      <div class="project-header">
        <h2>${project.name}</h2>
        <div>
          <button class="btn btn-primary edit-project-detail" data-id="${project.id}">
            <i class="bi bi-pencil"></i> Edit Project
          </button>
          <button class="btn btn-success add-task-detail" data-project="${project.id}">
            <i class="bi bi-plus-circle"></i> Add Task
          </button>
        </div>
      </div>
      <div class="mb-2">
        <span class="badge ${UI.getStatusClass(project.status)}">${UI.formatStatus(project.status)}</span>
        <span class="badge bg-secondary">${UI.formatCategory(project.category)}</span>
        ${project.tags.map(tag => `<span class="badge bg-info">${tag}</span>`).join(' ')}
      </div>
    `;
    
    // Create project stats
    const stats = `
      <div class="project-stats">
        <div class="project-stat-item">
          <h3>${progress.toFixed(0)}%</h3>
          <p>Progress</p>
          <div class="progress mt-2">
            <div class="progress-bar" role="progressbar" style="width: ${progress}%"></div>
          </div>
        </div>
        <div class="project-stat-item">
          <h3>${taskCounts.total}</h3>
          <p>Total Tasks</p>
        </div>
        <div class="project-stat-item">
          <h3>${taskCounts.done}</h3>
          <p>Completed</p>
        </div>
        <div class="project-stat-item">
          <h3>${taskCounts.overdue}</h3>
          <p>Overdue</p>
        </div>
      </div>
    `;
    
    // Create project details
    const details = `
      <div class="row">
        <div class="col-md-6">
          <div class="project-section">
            <h4>Description</h4>
            <p class="project-description">${project.description || 'No description provided.'}</p>
          </div>
        </div>
        <div class="col-md-6">
          <div class="project-section">
            <h4>Details</h4>
            <table class="table">
              <tr>
                <th>Timeline</th>
                <td>${UI.formatDate(project.startDate)} - ${UI.formatDate(project.endDate)}</td>
              </tr>
              <tr>
                <th>Revenue Target</th>
                <td>$${project.revenue.target.toLocaleString()}</td>
              </tr>
              <tr>
                <th>Revenue Actual</th>
                <td>$${project.revenue.actual.toLocaleString()}</td>
              </tr>
              <tr>
                <th>Created</th>
                <td>${UI.formatDateTime(project.createdAt)}</td>
              </tr>
              <tr>
                <th>Last Updated</th>
                <td>${UI.formatDateTime(project.updatedAt)}</td>
              </tr>
            </table>
          </div>
        </div>
      </div>
    `;
    
    // Create tasks section
    let tasksHtml = `
      <div class="project-section">
        <h4>Tasks</h4>
    `;
    
    if (tasks.length === 0) {
      tasksHtml += `
        <div class="alert alert-info">No tasks found for this project. Click the "Add Task" button to create one.</div>
      `;
    } else {
      // Group tasks by status
      const tasksByStatus = {
        todo: tasks.filter(t => t.status === 'todo'),
        inProgress: tasks.filter(t => t.status === 'in_progress'),
        review: tasks.filter(t => t.status === 'review'),
        done: tasks.filter(t => t.status === 'done')
      };
      
      // Create tabs for task statuses
      tasksHtml += `
        <ul class="nav nav-tabs" role="tablist">
          <li class="nav-item" role="presentation">
            <button class="nav-link active" id="todo-tab" data-bs-toggle="tab" data-bs-target="#todo-tasks" type="button" role="tab">
              To Do (${tasksByStatus.todo.length})
            </button>
          </li>
          <li class="nav-item" role="presentation">
            <button class="nav-link" id="inprogress-tab" data-bs-toggle="tab" data-bs-target="#inprogress-tasks" type="button" role="tab">
              In Progress (${tasksByStatus.inProgress.length})
            </button>
          </li>
          <li class="nav-item" role="presentation">
            <button class="nav-link" id="review-tab" data-bs-toggle="tab" data-bs-target="#review-tasks" type="button" role="tab">
              Review (${tasksByStatus.review.length})
            </button>
          </li>
          <li class="nav-item" role="presentation">
            <button class="nav-link" id="done-tab" data-bs-toggle="tab" data-bs-target="#done-tasks" type="button" role="tab">
              Done (${tasksByStatus.done.length})
            </button>
          </li>
        </ul>
        
        <div class="tab-content p-3 border border-top-0 rounded-bottom">
      `;
      
      // Create content for each tab
      for (const [status, statusTasks] of Object.entries(tasksByStatus)) {
        const isActive = status === 'todo';
        
        tasksHtml += `
          <div class="tab-pane fade ${isActive ? 'show active' : ''}" id="${status}-tasks" role="tabpanel">
        `;
        
        if (statusTasks.length === 0) {
          tasksHtml += `<div class="alert alert-info">No ${UI.formatStatus(status)} tasks found.</div>`;
        } else {
          for (const task of statusTasks) {
            const isOverdue = UI.isTaskOverdue(task);
            
            tasksHtml += `
              <div class="task-list-item">
                <div class="task-checkbox">
                  <input type="checkbox" class="form-check-input complete-task-checkbox" data-id="${task.id}" ${task.status === 'done' ? 'checked disabled' : ''}>
                </div>
                <div class="task-name">
                  ${task.name}
                  ${isOverdue ? '<span class="badge bg-danger ms-2">Overdue</span>' : ''}
                </div>
                <div class="task-priority">
                  ${UI.getTaskPriorityBadge(task.priority)}
                </div>
                <div class="task-due-date">
                  ${task.dueDate ? UI.formatDate(task.dueDate) : 'No due date'}
                </div>
                <div class="task-actions">
                  <button type="button" class="btn btn-sm btn-outline-primary edit-task" data-id="${task.id}">
                    <i class="bi bi-pencil"></i>
                  </button>
                  <button type="button" class="btn btn-sm btn-outline-danger delete-task" data-id="${task.id}">
                    <i class="bi bi-trash"></i>
                  </button>
                </div>
              </div>
            `;
          }
        }
        
        tasksHtml += `</div>`;
      }
      
      tasksHtml += `</div>`;
    }
    
    tasksHtml += `</div>`;
    
    // Combine all sections
    elements.projectDetailPage.innerHTML = header + stats + details + tasksHtml;
  }
  
  /**
   * Populate project form for editing
   * @param {Object} project - Project data
   */
  static populateProjectForm(project) {
    elements.projectId.value = project.id;
    elements.projectName.value = project.name;
    elements.projectDescription.value = project.description;
    elements.projectCategory.value = project.category;
    elements.projectStatus.value = project.status;
    elements.projectStartDate.value = project.startDate;
    elements.projectEndDate.value = project.endDate;
    elements.projectRevenueTarget.value = project.revenue.target;
    elements.projectRevenueActual.value = project.revenue.actual;
    elements.projectTags.value = project.tags.join(', ');
  }
  
  /**
   * Reset project form
   */
  static resetProjectForm() {
    elements.projectId.value = '';
    elements.projectForm.reset();
    elements.projectStartDate.value = new Date().toISOString().split('T')[0];
    
    // Set end date to 30 days from now
    const endDate = new Date();
    endDate.setDate(endDate.getDate() + 30);
    elements.projectEndDate.value = endDate.toISOString().split('T')[0];
  }
  
  /**
   * Get project data from form
   * @returns {Object} Project data
   */
  static getProjectFormData() {
    return {
      id: elements.projectId.value || null,
      name: elements.projectName.value,
      description: elements.projectDescription.value,
      category: elements.projectCategory.value,
      status: elements.projectStatus.value,
      startDate: elements.projectStartDate.value,
      endDate: elements.projectEndDate.value,
      revenue: {
        target: parseFloat(elements.projectRevenueTarget.value) || 0,
        actual: parseFloat(elements.projectRevenueActual.value) || 0,
        currency: 'USD'
      },
      tags: elements.projectTags.value
        .split(',')
        .map(tag => tag.trim())
        .filter(Boolean)
    };
  }
  
  /**
   * Populate task form for editing
   * @param {Object} task - Task data
   */
  static populateTaskForm(task) {
    elements.taskId.value = task.id;
    elements.taskName.value = task.name;
    elements.taskDescription.value = task.description;
    elements.taskProject.value = task.projectId;
    elements.taskStatus.value = task.status;
    elements.taskPriority.value = task.priority;
    elements.taskDueDate.value = task.dueDate || '';
    elements.taskAssignee.value = task.assignee || '';
  }
  
  /**
   * Reset task form
   */
  static resetTaskForm() {
    elements.taskId.value = '';
    elements.taskForm.reset();
    
    // Set default due date to 7 days from now
    const dueDate = new Date();
    dueDate.setDate(dueDate.getDate() + 7);
    elements.taskDueDate.value = dueDate.toISOString().split('T')[0];
  }
  
  /**
   * Get task data from form
   * @returns {Object} Task data
   */
  static getTaskFormData() {
    return {
      id: elements.taskId.value || null,
      name: elements.taskName.value,
      description: elements.taskDescription.value,
      projectId: elements.taskProject.value,
      status: elements.taskStatus.value,
      priority: elements.taskPriority.value,
      dueDate: elements.taskDueDate.value || null,
      assignee: elements.taskAssignee.value || null
    };
  }
  
  /**
   * Populate project select element
   * @param {Array} projects - List of projects
   * @param {string} selectedId - Selected project ID
   */
  static populateProjectSelect(projects, selectedId = null) {
    elements.taskProject.innerHTML = '';
    
    for (const project of projects) {
      const option = document.createElement('option');
      option.value = project.id;
      option.textContent = project.name;
      
      if (selectedId && project.id === selectedId) {
        option.selected = true;
      }
      
      elements.taskProject.appendChild(option);
    }
  }
  
  /**
   * Get status badge HTML
   * @param {string} status - Status value
   * @returns {string} Badge HTML
   */
  static getStatusBadge(status) {
    return `<span class="badge ${UI.getStatusClass(status)}">${UI.formatStatus(status)}</span>`;
  }
  
  /**
   * Get status CSS class
   * @param {string} status - Status value
   * @returns {string} CSS class
   */
  static getStatusClass(status) {
    switch (status) {
      case 'planned':
        return 'bg-primary';
      case 'in_progress':
        return 'bg-warning text-dark';
      case 'on_hold':
        return 'bg-secondary';
      case 'completed':
        return 'bg-success';
      case 'cancelled':
        return 'bg-danger';
      default:
        return 'bg-secondary';
    }
  }
  
  /**
   * Get task status badge HTML
   * @param {string} status - Status value
   * @returns {string} Badge HTML
   */
  static getTaskStatusBadge(status) {
    return `<span class="badge ${UI.getTaskStatusClass(status)}">${UI.formatTaskStatus(status)}</span>`;
  }
  
  /**
   * Get task status CSS class
   * @param {string} status - Status value
   * @returns {string} CSS class
   */
  static getTaskStatusClass(status) {
    switch (status) {
      case 'todo':
        return 'bg-primary';
      case 'in_progress':
        return 'bg-warning text-dark';
      case 'review':
        return 'bg-info text-dark';
      case 'done':
        return 'bg-success';
      default:
        return 'bg-secondary';
    }
  }
  
  /**
   * Get task priority badge HTML
   * @param {string} priority - Priority value
   * @returns {string} Badge HTML
   */
  static getTaskPriorityBadge(priority) {
    return `<span class="badge ${UI.getTaskPriorityClass(priority)}">${UI.formatTaskPriority(priority)}</span>`;
  }
  
  /**
   * Get task priority CSS class
   * @param {string} priority - Priority value
   * @returns {string} CSS class
   */
  static getTaskPriorityClass(priority) {
    switch (priority) {
      case 'low':
        return 'bg-primary';
      case 'medium':
        return 'bg-secondary';
      case 'high':
        return 'bg-warning text-dark';
      case 'urgent':
        return 'bg-danger';
      default:
        return 'bg-secondary';
    }
  }
  
  /**
   * Get progress bar HTML
   * @param {number} percentage - Progress percentage
   * @returns {string} Progress bar HTML
   */
  static getProgressBar(percentage) {
    return `
      <div class="progress">
        <div class="progress-bar" role="progressbar" style="width: ${percentage}%" aria-valuenow="${percentage}" aria-valuemin="0" aria-valuemax="100"></div>
      </div>
    `;
  }
  
  /**
   * Format status text
   * @param {string} status - Status value
   * @returns {string} Formatted status
   */
  static formatStatus(status) {
    switch (status) {
      case 'in_progress':
        return 'In Progress';
      case 'on_hold':
        return 'On Hold';
      default:
        return status.charAt(0).toUpperCase() + status.slice(1);
    }
  }
  
  /**
   * Format task status text
   * @param {string} status - Status value
   * @returns {string} Formatted status
   */
  static formatTaskStatus(status) {
    switch (status) {
      case 'todo':
        return 'To Do';
      case 'in_progress':
        return 'In Progress';
      default:
        return status.charAt(0).toUpperCase() + status.slice(1);
    }
  }
  
  /**
   * Format task priority text
   * @param {string} priority - Priority value
   * @returns {string} Formatted priority
   */
  static formatTaskPriority(priority) {
    return priority.charAt(0).toUpperCase() + priority.slice(1);
  }
  
  /**
   * Format category text
   * @param {string} category - Category value
   * @returns {string} Formatted category
   */
  static formatCategory(category) {
    const words = category.split('_');
    return words.map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
  }
  
  /**
   * Format date
   * @param {string} dateString - Date string
   * @returns {string} Formatted date
   */
  static formatDate(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    return date.toLocaleDateString();
  }
  
  /**
   * Format date and time
   * @param {string} dateTimeString - Date and time string
   * @returns {string} Formatted date and time
   */
  static formatDateTime(dateTimeString) {
    if (!dateTimeString) return '';
    
    const date = new Date(dateTimeString);
    return date.toLocaleString();
  }
  
  /**
   * Check if a task is overdue
   * @param {Object} task - Task object
   * @returns {boolean} True if overdue
   */
  static isTaskOverdue(task) {
    if (!task.dueDate || task.status === 'done') return false;
    
    const dueDate = new Date(task.dueDate);
    dueDate.setHours(23, 59, 59, 999); // End of day
    
    return dueDate < new Date();
  }
}
