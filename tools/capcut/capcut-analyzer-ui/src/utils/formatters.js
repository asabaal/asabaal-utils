/**
 * Utility functions for formatting data values
 */

// Format a duration in seconds to a readable string
export function formatDuration(seconds) {
  if (seconds === undefined || seconds === null) return 'N/A';
  
  // Handle floating point precision
  seconds = Math.round(seconds * 100) / 100;
  
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  const ms = Math.round((seconds % 1) * 1000);
  
  let result = '';
  
  if (hours > 0) {
    result += `${hours}:`;
    result += `${minutes.toString().padStart(2, '0')}:`;
  } else {
    result += `${minutes}:`;
  }
  
  result += `${secs.toString().padStart(2, '0')}`;
  
  // Only show milliseconds if less than a second or if we need precision
  if (seconds < 1 || seconds % 1 !== 0) {
    result += `.${ms.toString().padStart(3, '0')}`;
  }
  
  return result;
}

// Format a file size in bytes to a readable string
export function formatFileSize(bytes) {
  if (bytes === undefined || bytes === null) return 'N/A';
  
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let size = bytes;
  let unitIndex = 0;
  
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }
  
  return `${size.toFixed(1)} ${units[unitIndex]}`;
}

// Format a date string or timestamp to a readable string
export function formatDate(date) {
  if (!date) return 'N/A';
  
  try {
    const dateObj = new Date(date);
    return dateObj.toLocaleDateString() + ' ' + dateObj.toLocaleTimeString();
  } catch (error) {
    return 'Invalid Date';
  }
}