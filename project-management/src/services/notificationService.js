/**
 * Notification Service
 * Handles sending notifications through different channels
 */

class NotificationService {
  constructor(options = {}) {
    this.channels = options.channels || ['console'];
    this.config = options.config || {};
    this.history = [];
    this.historyLimit = options.historyLimit || 100;
  }

  /**
   * Send a notification through all configured channels
   * @param {Object} notification - Notification data
   * @returns {Promise<boolean>} Success status
   */
  async send(notification) {
    const results = [];
    const timestamp = new Date().toISOString();
    
    const notificationWithTimestamp = {
      ...notification,
      timestamp: notification.timestamp || timestamp
    };
    
    try {
      // Send through each configured channel
      for (const channel of this.channels) {
        try {
          switch (channel) {
            case 'console':
              results.push(await this._sendConsole(notificationWithTimestamp));
              break;
            case 'email':
              results.push(await this._sendEmail(notificationWithTimestamp));
              break;
            case 'desktop':
              results.push(await this._sendDesktop(notificationWithTimestamp));
              break;
            default:
              console.warn(`Unknown notification channel: ${channel}`);
              results.push(false);
          }
        } catch (channelError) {
          console.error(`Error sending ${channel} notification:`, channelError);
          results.push(false);
        }
      }
      
      // Add to history
      this._addToHistory(notificationWithTimestamp, results);
      
      // Return true if at least one channel succeeded
      return results.some(result => result === true);
    } catch (error) {
      console.error('Error sending notification:', error);
      return false;
    }
  }

  /**
   * Send a console notification
   * @private
   * @param {Object} notification - Notification data
   * @returns {Promise<boolean>} Success status
   */
  async _sendConsole(notification) {
    try {
      const { title, message, timestamp } = notification;
      
      console.log('\n=== NOTIFICATION ===');
      console.log(`TIME: ${timestamp}`);
      console.log(`TITLE: ${title}`);
      console.log(`MESSAGE: ${message}`);
      console.log('====================\n');
      
      return true;
    } catch (error) {
      console.error('Error sending console notification:', error);
      return false;
    }
  }

  /**
   * Send an email notification
   * @private
   * @param {Object} notification - Notification data
   * @returns {Promise<boolean>} Success status
   */
  async _sendEmail(notification) {
    try {
      const { title, message } = notification;
      
      if (!this.config.email) {
        throw new Error('Email configuration missing');
      }
      
      const { transporter, from, to } = this.config.email;
      
      if (!transporter || !from || !to) {
        throw new Error('Email configuration incomplete');
      }
      
      // This is a placeholder for email sending logic
      // In a real implementation, you would use a library like nodemailer
      console.log(`Would send email from ${from} to ${to}:`, { title, message });
      
      return true;
    } catch (error) {
      console.error('Error sending email notification:', error);
      return false;
    }
  }

  /**
   * Send a desktop notification
   * @private
   * @param {Object} notification - Notification data
   * @returns {Promise<boolean>} Success status
   */
  async _sendDesktop(notification) {
    try {
      const { title, message } = notification;
      
      // This is a placeholder for desktop notification logic
      // In a real implementation, you would use a library like node-notifier
      console.log('Would send desktop notification:', { title, message });
      
      return true;
    } catch (error) {
      console.error('Error sending desktop notification:', error);
      return false;
    }
  }

  /**
   * Add a notification to history
   * @private
   * @param {Object} notification - Notification data
   * @param {Array<boolean>} results - Channel success results
   */
  _addToHistory(notification, results) {
    this.history.unshift({
      ...notification,
      results,
      success: results.some(result => result === true)
    });
    
    // Trim history to limit
    if (this.history.length > this.historyLimit) {
      this.history = this.history.slice(0, this.historyLimit);
    }
  }

  /**
   * Get notification history
   * @param {number} limit - Maximum number of items to return
   * @returns {Array} Notification history
   */
  getHistory(limit = 10) {
    return this.history.slice(0, limit);
  }

  /**
   * Clear notification history
   */
  clearHistory() {
    this.history = [];
  }

  /**
   * Configure notification channels
   * @param {Object} config - Channel configuration
   */
  configure(config) {
    this.config = {
      ...this.config,
      ...config
    };
  }

  /**
   * Add a notification channel
   * @param {string} channel - Channel name
   */
  addChannel(channel) {
    if (!this.channels.includes(channel)) {
      this.channels.push(channel);
    }
  }

  /**
   * Remove a notification channel
   * @param {string} channel - Channel name
   */
  removeChannel(channel) {
    this.channels = this.channels.filter(c => c !== channel);
  }
}

module.exports = NotificationService;
