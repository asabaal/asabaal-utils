/**
 * Storage utility for persisting data
 * Uses file-based storage by default but can be extended to use other backends
 */

const fs = require('fs').promises;
const path = require('path');

class Storage {
  constructor(options = {}) {
    this.dataDir = options.dataDir || path.join(process.cwd(), 'data');
    this.prettyPrint = options.prettyPrint || true;
  }

  /**
   * Initialize storage - create data directory if it doesn't exist
   */
  async init() {
    try {
      await fs.mkdir(this.dataDir, { recursive: true });
      console.log(`Storage initialized at ${this.dataDir}`);
      return true;
    } catch (error) {
      console.error('Failed to initialize storage:', error);
      throw error;
    }
  }

  /**
   * Save collection data to file
   * @param {string} collection - Collection name (e.g., 'projects', 'tasks')
   * @param {Array|Object} data - Data to save
   */
  async save(collection, data) {
    try {
      const filePath = path.join(this.dataDir, `${collection}.json`);
      const jsonData = this.prettyPrint 
        ? JSON.stringify(data, null, 2) 
        : JSON.stringify(data);
      
      await fs.writeFile(filePath, jsonData, 'utf8');
      return true;
    } catch (error) {
      console.error(`Failed to save ${collection}:`, error);
      throw error;
    }
  }

  /**
   * Load collection data from file
   * @param {string} collection - Collection name
   * @returns {Array|Object} Loaded data
   */
  async load(collection) {
    try {
      const filePath = path.join(this.dataDir, `${collection}.json`);
      
      try {
        const data = await fs.readFile(filePath, 'utf8');
        return JSON.parse(data);
      } catch (readError) {
        // If file doesn't exist, return empty array/object
        if (readError.code === 'ENOENT') {
          return Array.isArray(collection) ? [] : {};
        }
        throw readError;
      }
    } catch (error) {
      console.error(`Failed to load ${collection}:`, error);
      throw error;
    }
  }

  /**
   * Check if a collection exists
   * @param {string} collection - Collection name
   * @returns {Promise<boolean>} True if exists
   */
  async exists(collection) {
    try {
      const filePath = path.join(this.dataDir, `${collection}.json`);
      await fs.access(filePath);
      return true;
    } catch (error) {
      return false;
    }
  }

  /**
   * Delete a collection
   * @param {string} collection - Collection name
   */
  async delete(collection) {
    try {
      const filePath = path.join(this.dataDir, `${collection}.json`);
      await fs.unlink(filePath);
      return true;
    } catch (error) {
      console.error(`Failed to delete ${collection}:`, error);
      throw error;
    }
  }

  /**
   * List all available collections
   * @returns {Promise<string[]>} Collection names
   */
  async listCollections() {
    try {
      const files = await fs.readdir(this.dataDir);
      return files
        .filter(file => file.endsWith('.json'))
        .map(file => file.replace('.json', ''));
    } catch (error) {
      console.error('Failed to list collections:', error);
      throw error;
    }
  }
}

module.exports = Storage;
