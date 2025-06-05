/**
 * Analyzes a CapCut project structure analysis JSON file
 * and extracts relevant data for visualization
 */

// Analyze project data and extract key information
export function analyzeProjectData(data) {
  // Initialize result structure
  const result = {
    projectName: getProjectName(data),
    materials: extractMaterials(data),
    timeline: extractTimeline(data),
    statistics: calculateStatistics(data),
    mediaReferences: Array.isArray(data.media_references) 
      ? data.media_references 
      : []
  };
  
  return result;
}

// Extract the project name from the data
function getProjectName(data) {
  // Try to find project name from file paths or other metadata
  if (data.media_references && data.media_references.length > 0) {
    // Extract directory name from first media reference
    const path = data.media_references[0];
    const parts = path.split('/');
    return parts[parts.length - 2] || 'CapCut Project';
  }
  
  return 'CapCut Project';
}

// Extract all materials from the project
function extractMaterials(data) {
  const result = {
    videos: [],
    audios: [],
    images: [],
    texts: [],
    effects: [],
    stickers: [],
    transitions: []
  };
  
  // Process media pools
  if (data.media_pools) {
    for (const poolKey in data.media_pools) {
      const pool = data.media_pools[poolKey];
      
      if (pool.items && Array.isArray(pool.items)) {
        // Group by type
        for (const item of pool.items) {
          const type = item.type?.toLowerCase() || 'unknown';
          
          // Map type to a category
          const category = getCategory(type);
          
          if (result[category]) {
            result[category].push({
              ...item,
              category,
              isUsed: false // Will be updated later
            });
          }
        }
      }
    }
  }
  
  return result;
}

// Map media type to a category
function getCategory(type) {
  const typeMap = {
    'video': 'videos',
    'audio': 'audios',
    'image': 'images',
    'text': 'texts',
    'effect': 'effects',
    'sticker': 'stickers',
    'transition': 'transitions'
  };
  
  return typeMap[type] || 'videos';
}

// Extract timeline information
function extractTimeline(data) {
  const result = {
    tracks: [],
    segments: [],
    duration: 0
  };
  
  // Process timeline data
  if (data.timeline_data) {
    for (const timelineKey in data.timeline_data) {
      const timeline = data.timeline_data[timelineKey];
      
      // Extract tracks
      if (timeline.tracks && Array.isArray(timeline.tracks)) {
        for (const track of timeline.tracks) {
          result.tracks.push({
            id: track.id || `track_${track.index}`,
            index: track.index || 0,
            type: track.type || 'unknown',
            name: getTrackName(track)
          });
          
          // Extract segments
          if (track.segments && Array.isArray(track.segments)) {
            for (const segment of track.segments) {
              const segmentObj = {
                id: segment.id || `segment_${track.index}_${segment.index}`,
                trackId: track.id || `track_${track.index}`,
                trackIndex: track.index || 0,
                materialId: segment.material_id,
                startTime: segment.timeline_start || 0,
                endTime: segment.timeline_end || 0,
                duration: segment.timeline_duration || 0
              };
              
              result.segments.push(segmentObj);
              
              // Update timeline duration
              if (segmentObj.endTime > result.duration) {
                result.duration = segmentObj.endTime;
              }
            }
          }
        }
      }
    }
  }
  
  return result;
}

// Get a descriptive name for a track based on its type and index
function getTrackName(track) {
  const typeMap = {
    'video': 'Main Video',
    'audio': 'Audio',
    'text': 'Text Overlay',
    'broll': 'B-Roll',
    'unknown': 'Track'
  };
  
  const type = track.type?.toLowerCase() || 'unknown';
  const baseName = typeMap[type] || typeMap.unknown;
  
  return `${baseName} ${track.index + 1}`;
}

// Calculate statistics for the project
function calculateStatistics(data) {
  // Initialize statistics
  const stats = {
    totalMaterials: 0,
    materialsByType: {},
    totalSegments: 0,
    totalTracks: 0,
    timelineDuration: 0,
    usedMaterials: 0,
    unusedMaterials: 0,
    usagePercentage: 0
  };
  
  // Count materials
  if (data.media_pools) {
    for (const poolKey in data.media_pools) {
      const pool = data.media_pools[poolKey];
      
      if (pool.items && Array.isArray(pool.items)) {
        stats.totalMaterials += pool.items.length;
        
        // Count by type
        for (const item of pool.items) {
          const type = item.type?.toLowerCase() || 'unknown';
          stats.materialsByType[type] = (stats.materialsByType[type] || 0) + 1;
        }
      }
    }
  }
  
  // Count segments and tracks
  if (data.timeline_data) {
    const trackIds = new Set();
    
    for (const timelineKey in data.timeline_data) {
      const timeline = data.timeline_data[timelineKey];
      
      if (timeline.tracks && Array.isArray(timeline.tracks)) {
        for (const track of timeline.tracks) {
          trackIds.add(track.id || `track_${track.index}`);
          
          if (track.segments && Array.isArray(track.segments)) {
            stats.totalSegments += track.segments.length;
          }
        }
      }
    }
    
    stats.totalTracks = trackIds.size;
  }
  
  // Get timeline duration
  if (data.timeline_data) {
    for (const timelineKey in data.timeline_data) {
      const timeline = data.timeline_data[timelineKey];
      stats.timelineDuration = Math.max(stats.timelineDuration, timeline.duration || 0);
    }
  }
  
  return stats;
}

// Find unused media in the project
export function findUnusedMedia(data) {
  // Get all material IDs
  const materialIds = new Set();
  const materialPaths = new Set();
  const usedMaterialIds = new Set();
  const usedMaterialPaths = new Set();
  
  // Collect all material IDs and paths
  if (data.media_pools) {
    for (const poolKey in data.media_pools) {
      const pool = data.media_pools[poolKey];
      
      if (pool.items && Array.isArray(pool.items)) {
        for (const item of pool.items) {
          if (item.id) {
            materialIds.add(item.id);
          }
          if (item.path) {
            materialPaths.add(item.path);
            // Also add just the filename
            const parts = item.path.split('/');
            materialPaths.add(parts[parts.length - 1]);
          }
        }
      }
    }
  }
  
  // Collect used material IDs from timeline
  if (data.timeline_data) {
    for (const timelineKey in data.timeline_data) {
      const timeline = data.timeline_data[timelineKey];
      
      if (timeline.tracks && Array.isArray(timeline.tracks)) {
        for (const track of timeline.tracks) {
          if (track.segments && Array.isArray(track.segments)) {
            for (const segment of track.segments) {
              if (segment.material_id) {
                usedMaterialIds.add(segment.material_id);
              }
              if (segment.media_path) {
                usedMaterialPaths.add(segment.media_path);
                // Also add just the filename
                const parts = segment.media_path.split('/');
                usedMaterialPaths.add(parts[parts.length - 1]);
              }
            }
          }
        }
      }
    }
  }
  
  // Collect used material IDs from clip references
  if (data.clip_references) {
    for (const clipId in data.clip_references) {
      const clipRef = data.clip_references[clipId];
      
      if (clipRef.id) {
        usedMaterialIds.add(clipRef.id);
      }
      if (clipRef.path) {
        usedMaterialPaths.add(clipRef.path);
        // Also add just the filename
        const parts = clipRef.path.split('/');
        usedMaterialPaths.add(parts[parts.length - 1]);
      }
    }
  }
  
  // Find unused materials
  const unusedMedia = [];
  
  if (data.media_pools) {
    for (const poolKey in data.media_pools) {
      const pool = data.media_pools[poolKey];
      
      if (pool.items && Array.isArray(pool.items)) {
        for (const item of pool.items) {
          const isUsed = 
            (item.id && usedMaterialIds.has(item.id)) || 
            (item.path && usedMaterialPaths.has(item.path)) ||
            (item.path && usedMaterialPaths.has(item.path.split('/').pop()));
          
          if (!isUsed) {
            unusedMedia.push({
              ...item,
              poolKey
            });
          }
        }
      }
    }
  }
  
  return unusedMedia;
}