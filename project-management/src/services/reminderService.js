/**
 * Reminder Service
 * Manages automated reminders for deadlines
 */

class ReminderService {
  constructor(taskRepository, projectRepository, notifier) {
    this.taskRepository = taskRepository;
    this.projectRepository = projectRepository;
    this.notifier = notifier;
    this.reminderSchedule = {
      tasks: {
        // Days before due date to send reminders
        upcoming: [7, 3, 1],
        // Hours after due date for overdue reminders
        overdue: [1, 24, 72]
      },
      projects: {
        // Days before end date to send reminders
        upcoming: [14, 7, 3, 1],
        // Hours after end date for overdue reminders
        overdue: [1, 24, 72]
      }
    };
  }

  /**
   * Check for and send due reminders
   * @returns {Promise<Object>} Results of the reminder check
   */
  async checkReminders() {
    const results = {
      taskReminders: [],
      projectReminders: []
    };

    try {
      // Check for task reminders
      const taskReminders = await this._checkTaskReminders();
      results.taskReminders = taskReminders;

      // Check for project reminders
      const projectReminders = await this._checkProjectReminders();
      results.projectReminders = projectReminders;

      return results;
    } catch (error) {
      console.error('Error checking reminders:', error);
      throw error;
    }
  }

  /**
   * Check for task reminders
   * @private
   * @returns {Promise<Array>} Sent reminders
   */
  async _checkTaskReminders() {
    const sentReminders = [];
    const now = new Date();
    
    try {
      // Get all incomplete tasks with due dates
      const tasks = await this.taskRepository.getAll();
      const tasksWithDueDates = tasks.filter(
        task => task.dueDate && task.status !== 'done'
      );
      
      for (const task of tasksWithDueDates) {
        const dueDate = new Date(task.dueDate);
        
        // Check for upcoming deadlines
        const daysUntilDue = Math.ceil((dueDate - now) / (1000 * 60 * 60 * 24));
        
        if (daysUntilDue > 0 && this.reminderSchedule.tasks.upcoming.includes(daysUntilDue)) {
          // Send upcoming reminder
          const reminderType = 'upcoming';
          const reminder = {
            type: 'task',
            reminderType,
            taskId: task.id,
            taskName: task.name,
            dueDate: task.dueDate,
            daysUntilDue,
            priority: task.priority
          };
          
          await this._sendReminder(reminder);
          sentReminders.push(reminder);
        } 
        // Check for overdue tasks
        else if (daysUntilDue < 0) {
          const hoursOverdue = Math.abs(Math.ceil((now - dueDate) / (1000 * 60 * 60)));
          
          // Check if any of the overdue reminder thresholds match
          for (const hours of this.reminderSchedule.tasks.overdue) {
            if (hoursOverdue === hours) {
              const reminderType = 'overdue';
              const reminder = {
                type: 'task',
                reminderType,
                taskId: task.id,
                taskName: task.name,
                dueDate: task.dueDate,
                hoursOverdue,
                priority: task.priority
              };
              
              await this._sendReminder(reminder);
              sentReminders.push(reminder);
              break;
            }
          }
        }
      }
      
      return sentReminders;
    } catch (error) {
      console.error('Error checking task reminders:', error);
      throw error;
    }
  }

  /**
   * Check for project reminders
   * @private
   * @returns {Promise<Array>} Sent reminders
   */
  async _checkProjectReminders() {
    const sentReminders = [];
    const now = new Date();
    
    try {
      // Get all active projects with end dates
      const projects = await this.projectRepository.getAll();
      const activeProjects = projects.filter(
        project => (
          project.endDate && 
          project.status !== 'completed' &&
          project.status !== 'cancelled'
        )
      );
      
      for (const project of activeProjects) {
        const endDate = new Date(project.endDate);
        
        // Check for upcoming deadlines
        const daysUntilEnd = Math.ceil((endDate - now) / (1000 * 60 * 60 * 24));
        
        if (daysUntilEnd > 0 && this.reminderSchedule.projects.upcoming.includes(daysUntilEnd)) {
          // Send upcoming reminder
          const reminderType = 'upcoming';
          const reminder = {
            type: 'project',
            reminderType,
            projectId: project.id,
            projectName: project.name,
            endDate: project.endDate,
            daysUntilEnd,
            status: project.status
          };
          
          await this._sendReminder(reminder);
          sentReminders.push(reminder);
        } 
        // Check for overdue projects
        else if (daysUntilEnd < 0) {
          const hoursOverdue = Math.abs(Math.ceil((now - endDate) / (1000 * 60 * 60)));
          
          // Check if any of the overdue reminder thresholds match
          for (const hours of this.reminderSchedule.projects.overdue) {
            if (hoursOverdue === hours) {
              const reminderType = 'overdue';
              const reminder = {
                type: 'project',
                reminderType,
                projectId: project.id,
                projectName: project.name,
                endDate: project.endDate,
                hoursOverdue,
                status: project.status
              };
              
              await this._sendReminder(reminder);
              sentReminders.push(reminder);
              break;
            }
          }
        }
      }
      
      return sentReminders;
    } catch (error) {
      console.error('Error checking project reminders:', error);
      throw error;
    }
  }

  /**
   * Send a reminder notification
   * @private
   * @param {Object} reminder - Reminder data
   */
  async _sendReminder(reminder) {
    try {
      if (!this.notifier) {
        console.log('Notifier not configured, skipping reminder:', reminder);
        return;
      }
      
      let title, message;
      
      // Format the notification based on reminder type
      if (reminder.type === 'task') {
        title = reminder.reminderType === 'upcoming'
          ? `Task Due in ${reminder.daysUntilDue} day(s)`
          : `Task Overdue by ${reminder.hoursOverdue} hour(s)`;
        
        message = reminder.reminderType === 'upcoming'
          ? `The task "${reminder.taskName}" is due in ${reminder.daysUntilDue} day(s)`
          : `The task "${reminder.taskName}" is overdue by ${reminder.hoursOverdue} hour(s)`;
        
        if (reminder.priority === 'high' || reminder.priority === 'urgent') {
          title = `⚠️ ${title} - ${reminder.priority.toUpperCase()}`;
        }
      } 
      else if (reminder.type === 'project') {
        title = reminder.reminderType === 'upcoming'
          ? `Project Deadline in ${reminder.daysUntilEnd} day(s)`
          : `Project Deadline Missed by ${reminder.hoursOverdue} hour(s)`;
        
        message = reminder.reminderType === 'upcoming'
          ? `The project "${reminder.projectName}" is ending in ${reminder.daysUntilEnd} day(s)`
          : `The project "${reminder.projectName}" has missed its deadline by ${reminder.hoursOverdue} hour(s)`;
      }
      
      // Send the notification
      await this.notifier.send({
        title,
        message,
        timestamp: new Date().toISOString(),
        data: reminder
      });
      
      console.log(`Sent reminder: ${title}`);
    } catch (error) {
      console.error('Error sending reminder:', error);
      // Don't throw here to prevent stopping the reminder check process
    }
  }

  /**
   * Set custom reminder schedule
   * @param {Object} schedule - New reminder schedule
   */
  setReminderSchedule(schedule) {
    this.reminderSchedule = {
      ...this.reminderSchedule,
      ...schedule
    };
  }
}

module.exports = ReminderService;
