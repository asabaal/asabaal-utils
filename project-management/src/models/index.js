/**
 * Core data models for the project management system
 */

// Project Categories
const PROJECT_CATEGORIES = {
  MUSIC_PRODUCTION: 'music_production',
  TRADING: 'trading',
  CONTENT_CREATION: 'content_creation',
  TECHNOLOGY: 'technology',
  BUSINESS: 'business'
};

// Project Status
const PROJECT_STATUS = {
  PLANNED: 'planned',
  IN_PROGRESS: 'in_progress',
  ON_HOLD: 'on_hold',
  COMPLETED: 'completed',
  CANCELLED: 'cancelled'
};

// Task Priority
const TASK_PRIORITY = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
  URGENT: 'urgent'
};

// Task Status
const TASK_STATUS = {
  TODO: 'todo',
  IN_PROGRESS: 'in_progress',
  REVIEW: 'review',
  DONE: 'done'
};

/**
 * Project Model
 * Represents a major business initiative
 */
class Project {
  constructor({
    id = null,
    name,
    description = '',
    category,
    status = PROJECT_STATUS.PLANNED,
    startDate,
    endDate,
    revenue = {
      target: 0,
      actual: 0,
      currency: 'USD'
    },
    tasks = [],
    notes = [],
    tags = []
  }) {
    this.id = id || Date.now().toString();
    this.name = name;
    this.description = description;
    this.category = category;
    this.status = status;
    this.startDate = startDate;
    this.endDate = endDate;
    this.revenue = revenue;
    this.tasks = tasks;
    this.notes = notes;
    this.tags = tags;
    this.createdAt = new Date().toISOString();
    this.updatedAt = new Date().toISOString();
  }

  // Calculate project progress based on completed tasks
  calculateProgress() {
    if (this.tasks.length === 0) return 0;
    
    const completedTasks = this.tasks.filter(
      task => task.status === TASK_STATUS.DONE
    ).length;
    
    return (completedTasks / this.tasks.length) * 100;
  }

  // Check if project is on schedule
  isOnSchedule() {
    const today = new Date();
    const end = new Date(this.endDate);
    
    if (today > end && this.status !== PROJECT_STATUS.COMPLETED) {
      return false;
    }
    
    // Calculate expected progress based on timeline
    const start = new Date(this.startDate);
    const totalDuration = end - start;
    const elapsed = today - start;
    
    if (elapsed <= 0) return true; // Not started yet
    
    const expectedProgress = Math.min(100, (elapsed / totalDuration) * 100);
    const actualProgress = this.calculateProgress();
    
    // Allow 10% buffer
    return actualProgress >= (expectedProgress - 10);
  }
}

/**
 * Task Model
 * Represents a specific action item within a project
 */
class Task {
  constructor({
    id = null,
    projectId,
    name,
    description = '',
    status = TASK_STATUS.TODO,
    priority = TASK_PRIORITY.MEDIUM,
    dueDate = null,
    assignee = null,
    dependencies = [],
    subtasks = [],
    notes = []
  }) {
    this.id = id || Date.now().toString();
    this.projectId = projectId;
    this.name = name;
    this.description = description;
    this.status = status;
    this.priority = priority;
    this.dueDate = dueDate;
    this.assignee = assignee;
    this.dependencies = dependencies;
    this.subtasks = subtasks;
    this.notes = notes;
    this.createdAt = new Date().toISOString();
    this.updatedAt = new Date().toISOString();
  }

  // Check if task is blocked by dependencies
  isBlocked() {
    return this.dependencies.length > 0;
  }

  // Check if task is overdue
  isOverdue() {
    if (!this.dueDate) return false;
    
    const today = new Date();
    const due = new Date(this.dueDate);
    
    return today > due && this.status !== TASK_STATUS.DONE;
  }
}

/**
 * Timeline Model
 * Represents a specific period with associated goals and projects
 */
class Timeline {
  constructor({
    id = null,
    name,
    startDate,
    endDate,
    projects = [],
    goals = [],
    milestones = []
  }) {
    this.id = id || Date.now().toString();
    this.name = name;
    this.startDate = startDate;
    this.endDate = endDate;
    this.projects = projects;
    this.goals = goals;
    this.milestones = milestones;
    this.createdAt = new Date().toISOString();
    this.updatedAt = new Date().toISOString();
  }

  // Calculate overall timeline progress
  calculateProgress() {
    if (this.projects.length === 0) return 0;
    
    const totalProgress = this.projects.reduce(
      (sum, project) => sum + project.calculateProgress(),
      0
    );
    
    return totalProgress / this.projects.length;
  }
}

module.exports = {
  PROJECT_CATEGORIES,
  PROJECT_STATUS,
  TASK_PRIORITY,
  TASK_STATUS,
  Project,
  Task,
  Timeline
};
