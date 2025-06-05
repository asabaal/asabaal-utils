import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import './MediaExplorer.css';

const MediaExplorer = ({ mediaInfo, relationshipInfo }) => {
  const [mediaTypeFilter, setMediaTypeFilter] = useState('all');
  const [usageFilter, setUsageFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedMedia, setSelectedMedia] = useState(null);
  const location = useLocation();

  // Get filters from URL if present
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const filterParam = params.get('filter');
    const typeParam = params.get('type');
    
    if (filterParam === 'used' || filterParam === 'unused') {
      setUsageFilter(filterParam);
    }
    
    if (typeParam === 'video' || typeParam === 'audio' || typeParam === 'image') {
      setMediaTypeFilter(typeParam);
    }
  }, [location]);

  // Get the list of used media IDs and paths
  const usedMediaIds = new Set(relationshipInfo.relationships?.map(rel => 
    rel.source_type === 'id' ? rel.source : '') || []);
  
  const usedMediaPaths = new Set(relationshipInfo.relationships?.map(rel => 
    rel.source_type === 'path' ? rel.source : '') || []);

  // Filter media items based on selected filters and search term
  const filteredMedia = (mediaInfo.all_items || []).filter(media => {
    // Check media type filter
    const matchesType = mediaTypeFilter === 'all' || media.type === mediaTypeFilter;
    
    // Check usage filter
    const isUsed = usedMediaIds.has(media.id) || usedMediaPaths.has(media.path);
    const matchesUsage = usageFilter === 'all' || 
                         (usageFilter === 'used' && isUsed) || 
                         (usageFilter === 'unused' && !isUsed);
    
    // Check search term
    const matchesSearch = searchTerm === '' || 
                         media.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         media.path.toLowerCase().includes(searchTerm.toLowerCase());
    
    return matchesType && matchesUsage && matchesSearch;
  });

  // Handle media item selection
  const handleMediaSelect = (media) => {
    setSelectedMedia(media);
  };

  // Handle filter changes
  const handleMediaTypeFilter = (type) => {
    setMediaTypeFilter(type);
  };

  const handleUsageFilter = (usage) => {
    setUsageFilter(usage);
  };

  // Handle search
  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
  };

  return (
    <div className="media-explorer">
      <h2 className="page-title mb-4">Media Explorer</h2>
      
      <div className="row">
        <div className="col-md-8">
          <div className="card">
            <div className="card-body">
              <h5 className="card-title">Media Files</h5>
              
              {/* Search and filters */}
              <div className="media-filters mb-4">
                <div className="row g-3 align-items-center">
                  <div className="col-md-6">
                    <div className="input-group">
                      <span className="input-group-text">
                        <i className="fas fa-search"></i>
                      </span>
                      <input 
                        type="text" 
                        className="form-control" 
                        placeholder="Search media files..." 
                        value={searchTerm}
                        onChange={handleSearchChange}
                      />
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="d-flex justify-content-end">
                      <div className="btn-group me-2" role="group">
                        <button 
                          type="button" 
                          className={`btn btn-sm ${mediaTypeFilter === 'all' ? 'btn-primary' : 'btn-outline-primary'}`}
                          onClick={() => handleMediaTypeFilter('all')}
                        >
                          All
                        </button>
                        <button 
                          type="button" 
                          className={`btn btn-sm ${mediaTypeFilter === 'video' ? 'btn-primary' : 'btn-outline-primary'}`}
                          onClick={() => handleMediaTypeFilter('video')}
                        >
                          Video
                        </button>
                        <button 
                          type="button" 
                          className={`btn btn-sm ${mediaTypeFilter === 'audio' ? 'btn-primary' : 'btn-outline-primary'}`}
                          onClick={() => handleMediaTypeFilter('audio')}
                        >
                          Audio
                        </button>
                        <button 
                          type="button" 
                          className={`btn btn-sm ${mediaTypeFilter === 'image' ? 'btn-primary' : 'btn-outline-primary'}`}
                          onClick={() => handleMediaTypeFilter('image')}
                        >
                          Image
                        </button>
                      </div>
                      
                      <div className="btn-group" role="group">
                        <button 
                          type="button" 
                          className={`btn btn-sm ${usageFilter === 'all' ? 'btn-secondary' : 'btn-outline-secondary'}`}
                          onClick={() => handleUsageFilter('all')}
                        >
                          All
                        </button>
                        <button 
                          type="button" 
                          className={`btn btn-sm ${usageFilter === 'used' ? 'btn-success' : 'btn-outline-success'}`}
                          onClick={() => handleUsageFilter('used')}
                        >
                          Used
                        </button>
                        <button 
                          type="button" 
                          className={`btn btn-sm ${usageFilter === 'unused' ? 'btn-danger' : 'btn-outline-danger'}`}
                          onClick={() => handleUsageFilter('unused')}
                        >
                          Unused
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Media list */}
              <div className="media-list">
                {filteredMedia.length === 0 ? (
                  <div className="text-center text-muted py-5">
                    <i className="fas fa-search fa-3x mb-3"></i>
                    <p>No media files match your filters</p>
                  </div>
                ) : (
                  filteredMedia.map((media, index) => {
                    const isUsed = usedMediaIds.has(media.id) || usedMediaPaths.has(media.path);
                    return (
                      <div 
                        key={index} 
                        className={`media-item ${isUsed ? 'used' : 'unused'} ${selectedMedia === media ? 'selected' : ''}`}
                        onClick={() => handleMediaSelect(media)}
                      >
                        <div className="row">
                          <div className="col-md-1">
                            <i className={`fas fa-${media.type === 'video' ? 'video' : media.type === 'audio' ? 'music' : 'image'} fa-2x media-type-${media.type}`}></i>
                          </div>
                          <div className="col-md-9">
                            <h6>{media.name}</h6>
                            <p className="text-muted mb-0">{media.path}</p>
                            {media.duration && (
                              <p className="mb-0"><small>Duration: {formatDuration(media.duration)}</small></p>
                            )}
                          </div>
                          <div className="col-md-2 text-end">
                            <span className={`badge ${isUsed ? 'bg-success' : 'bg-danger'}`}>
                              {isUsed ? 'Used' : 'Unused'}
                            </span>
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </div>
        </div>
        
        <div className="col-md-4">
          {/* Media details panel */}
          <div className="card">
            <div className="card-body">
              <h5 className="card-title">Media Details</h5>
              
              {selectedMedia ? (
                <div className="media-details">
                  <div className="text-center mb-4">
                    <i className={`fas fa-${selectedMedia.type === 'video' ? 'video' : selectedMedia.type === 'audio' ? 'music' : 'image'} fa-4x media-type-${selectedMedia.type}`}></i>
                  </div>
                  
                  <h4>{selectedMedia.name}</h4>
                  <hr />
                  
                  <div className="details-row">
                    <div className="details-label">Type:</div>
                    <div className="details-value text-capitalize">{selectedMedia.type}</div>
                  </div>
                  
                  <div className="details-row">
                    <div className="details-label">Path:</div>
                    <div className="details-value">
                      <code>{selectedMedia.path}</code>
                    </div>
                  </div>
                  
                  {selectedMedia.duration && (
                    <div className="details-row">
                      <div className="details-label">Duration:</div>
                      <div className="details-value">{formatDuration(selectedMedia.duration)}</div>
                    </div>
                  )}
                  
                  {selectedMedia.width && selectedMedia.height && (
                    <div className="details-row">
                      <div className="details-label">Dimensions:</div>
                      <div className="details-value">{selectedMedia.width} × {selectedMedia.height}</div>
                    </div>
                  )}
                  
                  {selectedMedia.id && (
                    <div className="details-row">
                      <div className="details-label">ID:</div>
                      <div className="details-value">
                        <code>{selectedMedia.id}</code>
                      </div>
                    </div>
                  )}
                  
                  <div className="details-row">
                    <div className="details-label">Status:</div>
                    <div className="details-value">
                      {usedMediaIds.has(selectedMedia.id) || usedMediaPaths.has(selectedMedia.path) ? (
                        <span className="badge bg-success">Used in Timeline</span>
                      ) : (
                        <span className="badge bg-danger">Unused</span>
                      )}
                    </div>
                  </div>
                  
                  {/* Usage information */}
                  {(usedMediaIds.has(selectedMedia.id) || usedMediaPaths.has(selectedMedia.path)) && (
                    <div className="usage-info mt-4">
                      <h6>Used in Clips:</h6>
                      <ul className="list-group">
                        {relationshipInfo.relationships
                          .filter(rel => 
                            (rel.source_type === 'id' && rel.source === selectedMedia.id) || 
                            (rel.source_type === 'path' && rel.source === selectedMedia.path)
                          )
                          .map((rel, idx) => (
                            <li key={idx} className="list-group-item bg-dark text-light border-secondary">
                              <i className="fas fa-film me-2"></i>
                              Clip ID: {rel.target}
                            </li>
                          ))}
                      </ul>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center text-muted py-5">
                  <i className="fas fa-photo-video fa-3x mb-3"></i>
                  <p>Select a media file to view details</p>
                </div>
              )}
            </div>
          </div>
          
          {/* Stats card */}
          <div className="card mt-3">
            <div className="card-body">
              <h5 className="card-title">Media Stats</h5>
              
              <div className="stats-row">
                <div className="stats-label">Total Media:</div>
                <div className="stats-value">{mediaInfo.total_count || 0}</div>
              </div>
              
              <div className="stats-row">
                <div className="stats-label">Videos:</div>
                <div className="stats-value">{mediaInfo.type_counts?.video || 0}</div>
              </div>
              
              <div className="stats-row">
                <div className="stats-label">Audio:</div>
                <div className="stats-value">{mediaInfo.type_counts?.audio || 0}</div>
              </div>
              
              <div className="stats-row">
                <div className="stats-label">Images:</div>
                <div className="stats-value">{mediaInfo.type_counts?.image || 0}</div>
              </div>
              
              <div className="stats-row">
                <div className="stats-label">Used Media:</div>
                <div className="stats-value">{mediaInfo.total_count - (relationshipInfo.unused_media?.length || 0)}</div>
              </div>
              
              <div className="stats-row">
                <div className="stats-label">Unused Media:</div>
                <div className="stats-value">{relationshipInfo.unused_media?.length || 0}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Format duration in seconds to MM:SS or HH:MM:SS
const formatDuration = (seconds) => {
  if (isNaN(seconds)) return 'N/A';
  
  // Convert from microseconds if needed
  if (seconds > 1000000) {
    seconds = seconds / 1000000;
  }
  
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  
  if (hours > 0) {
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  } else {
    return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
};

export default MediaExplorer;