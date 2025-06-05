import React, { useState, useEffect, useRef } from 'react';
import './TimelineVisualizer.css';

const TimelineVisualizer = ({ timelineInfo, mediaInfo }) => {
  const [selectedClip, setSelectedClip] = useState(null);
  const [scale, setScale] = useState(1);
  const [zoomLevel, setZoomLevel] = useState(5);
  const timelineContainerRef = useRef(null);
  const tracksContainerRef = useRef(null);

  // Prepare media lookup tables
  const mediaById = {};
  const mediaByPath = {};
  
  (mediaInfo.all_items || []).forEach(media => {
    if (media.id) mediaById[media.id] = media;
    if (media.path) mediaByPath[media.path] = media;
  });

  // Find the maximum timeline position for scaling
  const findMaxTimelineEnd = () => {
    if (!timelineInfo.clips || timelineInfo.clips.length === 0) return 60000000; // Default 1 minute in μs
    
    return Math.max(
      ...timelineInfo.clips.map(clip => {
        const start = clip.timeline_start || 0;
        const duration = clip.timeline_duration || 0;
        return start + duration;
      })
    );
  };

  const maxTimelineEnd = findMaxTimelineEnd();
  
  // Update scale when zoom level changes
  useEffect(() => {
    // Exponential scale: 2^(zoomLevel-5) to make level 5 = 100%
    const newScale = Math.pow(2, zoomLevel - 5);
    setScale(newScale);
  }, [zoomLevel]);

  // Handle clip selection
  const handleClipClick = (clip) => {
    setSelectedClip(clip);
  };

  // Handle zoom controls
  const handleZoomIn = () => {
    if (zoomLevel < 10) setZoomLevel(zoomLevel + 1);
  };

  const handleZoomOut = () => {
    if (zoomLevel > 1) setZoomLevel(zoomLevel - 1);
  };

  const handleZoomReset = () => {
    setZoomLevel(5); // Reset to 100%
  };

  // Generate ruler marks
  const generateRulerMarks = () => {
    const marks = [];
    // Base interval in microseconds
    const baseInterval = 5000000; // 5 seconds
    
    // Adjust interval based on zoom level
    const interval = baseInterval / Math.pow(2, zoomLevel - 5);
    
    // Calculate how many marks to create
    const totalWidth = maxTimelineEnd * scale;
    const numMarks = Math.ceil(totalWidth / interval);
    
    for (let i = 0; i <= numMarks; i++) {
      const position = i * interval;
      const positionPercent = (position / maxTimelineEnd) * 100;
      
      marks.push(
        <div 
          key={i} 
          className="timeline-ruler-mark" 
          style={{ left: `${positionPercent}%` }}
        >
          {i % 2 === 0 && (
            <div className="timeline-ruler-text">
              {formatDuration(position)}
            </div>
          )}
        </div>
      );
    }
    
    return marks;
  };
  
  // Find the media for a clip
  const getMediaForClip = (clip) => {
    if (clip.material_id && mediaById[clip.material_id]) {
      return mediaById[clip.material_id];
    }
    
    if (clip.media_path && mediaByPath[clip.media_path]) {
      return mediaByPath[clip.media_path];
    }
    
    return null;
  };

  // Determine clip type based on media
  const getClipTypeClass = (clip) => {
    const media = getMediaForClip(clip);
    if (!media) return '';
    
    return `${media.type}-clip`;
  };

  // Get clip display name
  const getClipDisplayName = (clip) => {
    const media = getMediaForClip(clip);
    if (media) return media.name;
    
    return `Clip ${clip.clip_index}`;
  };

  return (
    <div className="timeline-visualizer">
      <h2 className="page-title mb-4">Timeline Visualizer</h2>
      
      <div className="row">
        <div className="col-md-12">
          <div className="card">
            <div className="card-body">
              <div className="d-flex justify-content-between align-items-center mb-3">
                <h5 className="card-title mb-0">Timeline</h5>
                
                {/* Zoom controls */}
                <div className="timeline-zoom-controls">
                  <button 
                    className="btn btn-sm btn-outline-secondary me-2" 
                    onClick={handleZoomOut}
                    disabled={zoomLevel <= 1}
                  >
                    <i className="fas fa-search-minus"></i>
                  </button>
                  
                  <span className="zoom-level me-2">
                    {Math.round(scale * 100)}%
                  </span>
                  
                  <button 
                    className="btn btn-sm btn-outline-secondary me-2" 
                    onClick={handleZoomIn}
                    disabled={zoomLevel >= 10}
                  >
                    <i className="fas fa-search-plus"></i>
                  </button>
                  
                  <button 
                    className="btn btn-sm btn-outline-secondary" 
                    onClick={handleZoomReset}
                  >
                    <i className="fas fa-sync-alt"></i>
                  </button>
                </div>
              </div>
              
              {/* Timeline container */}
              <div 
                className="timeline-container" 
                ref={timelineContainerRef}
                style={{ overflowX: 'auto' }}
              >
                <div 
                  className="timeline-content" 
                  style={{ width: `${scale * 100}%`, minWidth: '100%' }}
                >
                  {/* Ruler */}
                  <div className="timeline-ruler">
                    {generateRulerMarks()}
                  </div>
                  
                  {/* Tracks and clips */}
                  <div className="timeline-tracks" ref={tracksContainerRef}>
                    {timelineInfo.tracks && timelineInfo.tracks.length > 0 ? (
                      timelineInfo.tracks.map((track, trackIndex) => (
                        <div 
                          key={track.id || trackIndex} 
                          className="timeline-track"
                          data-track-id={track.id}
                        >
                          <div className="timeline-track-label">
                            Track {track.index} ({track.type})
                          </div>
                          
                          {/* Clips in this track */}
                          {timelineInfo.clips && timelineInfo.clips
                            .filter(clip => clip.track_id === track.id)
                            .map((clip, clipIndex) => {
                              // Skip clips without position info
                              if (clip.timeline_start === undefined || clip.timeline_duration === undefined) {
                                return null;
                              }
                              
                              // Calculate position and width
                              const start = (clip.timeline_start / maxTimelineEnd) * 100;
                              const width = (clip.timeline_duration / maxTimelineEnd) * 100;
                              
                              return (
                                <div
                                  key={clip.id || clipIndex}
                                  className={`timeline-clip ${getClipTypeClass(clip)} ${selectedClip === clip ? 'selected' : ''}`}
                                  style={{ left: `${start}%`, width: `${width}%` }}
                                  onClick={() => handleClipClick(clip)}
                                  title={getClipDisplayName(clip)}
                                  data-clip-id={clip.id}
                                >
                                  {getClipDisplayName(clip)}
                                </div>
                              );
                            })}
                        </div>
                      ))
                    ) : (
                      <div className="text-center text-muted py-5">
                        <i className="fas fa-film fa-3x mb-3"></i>
                        <p>No timeline data available</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Clip details panel */}
      <div className="row mt-4">
        <div className="col-md-12">
          <div className="card">
            <div className="card-body">
              <h5 className="card-title">Clip Details</h5>
              
              {selectedClip ? (
                <div className="clip-details">
                  <div className="row">
                    <div className="col-md-6">
                      <div className="details-section">
                        <h6>Clip Information</h6>
                        
                        <div className="details-row">
                          <div className="details-label">Clip ID:</div>
                          <div className="details-value">
                            <code>{selectedClip.id || 'N/A'}</code>
                          </div>
                        </div>
                        
                        <div className="details-row">
                          <div className="details-label">Track:</div>
                          <div className="details-value">
                            Track {selectedClip.track_index} ({timelineInfo.tracks.find(t => t.id === selectedClip.track_id)?.type || 'unknown'})
                          </div>
                        </div>
                        
                        <div className="details-row">
                          <div className="details-label">Position:</div>
                          <div className="details-value">
                            {formatDuration(selectedClip.timeline_start)} - {formatDuration(selectedClip.timeline_start + selectedClip.timeline_duration)}
                          </div>
                        </div>
                        
                        <div className="details-row">
                          <div className="details-label">Duration:</div>
                          <div className="details-value">
                            {formatDuration(selectedClip.timeline_duration)}
                          </div>
                        </div>
                        
                        {selectedClip.source_start !== undefined && selectedClip.source_duration !== undefined && (
                          <div className="details-row">
                            <div className="details-label">Source Range:</div>
                            <div className="details-value">
                              {formatDuration(selectedClip.source_start)} - {formatDuration(selectedClip.source_start + selectedClip.source_duration)}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                    
                    <div className="col-md-6">
                      <div className="details-section">
                        <h6>Media Reference</h6>
                        
                        {selectedClip.material_id && (
                          <div className="details-row">
                            <div className="details-label">Material ID:</div>
                            <div className="details-value">
                              <code>{selectedClip.material_id}</code>
                            </div>
                          </div>
                        )}
                        
                        {selectedClip.media_path && (
                          <div className="details-row">
                            <div className="details-label">Media Path:</div>
                            <div className="details-value">
                              <code>{selectedClip.media_path}</code>
                            </div>
                          </div>
                        )}
                        
                        {/* Media details if available */}
                        {(() => {
                          const media = getMediaForClip(selectedClip);
                          if (!media) return (
                            <div className="text-muted">
                              No media information available for this clip
                            </div>
                          );
                          
                          return (
                            <>
                              <div className="details-row">
                                <div className="details-label">Media Name:</div>
                                <div className="details-value">
                                  <i className={`fas fa-${media.type === 'video' ? 'video' : media.type === 'audio' ? 'music' : 'image'} me-2 media-type-${media.type}`}></i>
                                  {media.name}
                                </div>
                              </div>
                              
                              <div className="details-row">
                                <div className="details-label">Media Type:</div>
                                <div className="details-value text-capitalize">
                                  {media.type}
                                </div>
                              </div>
                              
                              {media.duration && (
                                <div className="details-row">
                                  <div className="details-label">Media Duration:</div>
                                  <div className="details-value">
                                    {formatDuration(media.duration)}
                                  </div>
                                </div>
                              )}
                            </>
                          );
                        })()}
                      </div>
                    </div>
                  </div>
                  
                  {/* Location in project */}
                  {selectedClip.location && (
                    <div className="details-section mt-3">
                      <h6>Project Location</h6>
                      <code className="location-path">{selectedClip.location}</code>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center text-muted py-5">
                  <i className="fas fa-hand-pointer fa-3x mb-3"></i>
                  <p>Select a clip in the timeline to view details</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Format duration in microseconds to MM:SS or HH:MM:SS
const formatDuration = (microseconds) => {
  if (microseconds === undefined || microseconds === null) return 'N/A';
  
  // Convert microseconds to seconds
  const seconds = microseconds / 1000000;
  
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  
  if (hours > 0) {
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  } else {
    return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
};

export default TimelineVisualizer;