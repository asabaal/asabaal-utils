/**
 * API client for interacting with the project analysis backend
 */

/**
 * Analyzes a CapCut project file
 * @param {File} file - The project file to analyze
 * @returns {Promise<Object>} The analysis results
 */
export const analyzeProject = async (file) => {
  try {
    const formData = new FormData();
    formData.append('project_file', file);
    
    const response = await fetch('/api/analyze-project', {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to analyze project');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error analyzing project:', error);
    throw error;
  }
};

/**
 * Mock function to get sample project data for development
 * @returns {Promise<Object>} Sample project data
 */
export const getSampleProjectData = async () => {
  return {
    media_info: {
      all_items: [
        { id: 'video1', name: 'interview.mp4', path: '/videos/interview.mp4', type: 'video', duration: 120 },
        { id: 'video2', name: 'b-roll.mp4', path: '/videos/b-roll.mp4', type: 'video', duration: 45 },
        { id: 'audio1', name: 'background.mp3', path: '/audio/background.mp3', type: 'audio', duration: 180 },
        { id: 'image1', name: 'logo.png', path: '/images/logo.png', type: 'image' }
      ],
      total_count: 4,
      type_counts: { video: 2, audio: 1, image: 1 }
    },
    timeline_info: {
      tracks: [
        { id: 'track1', index: 0, type: 'video' },
        { id: 'track2', index: 1, type: 'audio' }
      ],
      clips: [
        { 
          id: 'clip1', 
          track_id: 'track1', 
          track_index: 0, 
          clip_index: 0, 
          material_id: 'video1',
          timeline_start: 0,
          timeline_duration: 15000000 // in microseconds
        },
        { 
          id: 'clip2', 
          track_id: 'track1', 
          track_index: 0, 
          clip_index: 1, 
          material_id: 'video2',
          timeline_start: 15000000,
          timeline_duration: 10000000 
        },
        { 
          id: 'clip3', 
          track_id: 'track2', 
          track_index: 1, 
          clip_index: 0, 
          material_id: 'audio1',
          timeline_start: 0,
          timeline_duration: 25000000 
        }
      ],
      total_tracks: 2,
      total_clips: 3
    },
    relationships: {
      relationships: [
        { source: 'video1', target: 'clip1', type: 'media_to_clip', source_type: 'id' },
        { source: 'video2', target: 'clip2', type: 'media_to_clip', source_type: 'id' },
        { source: 'audio1', target: 'clip3', type: 'media_to_clip', source_type: 'id' }
      ],
      unused_media: [
        { id: 'image1', name: 'logo.png', path: '/images/logo.png', type: 'image' }
      ]
    }
  };
};