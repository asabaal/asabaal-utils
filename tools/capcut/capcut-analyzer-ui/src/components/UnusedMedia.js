import React, { useState, useEffect } from 'react';
import { Card, Form, Button, Row, Col } from 'react-bootstrap';
import { formatDuration, formatFileSize } from '../utils/formatters';

function UnusedMedia({ data }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredMedia, setFilteredMedia] = useState([]);
  const [activeType, setActiveType] = useState('all');
  const [sortBy, setSortBy] = useState('name');
  const [sortDirection, setSortDirection] = useState('asc');
  
  if (!data || !data.unusedMedia) return <div>No unused media data available</div>;
  
  const { unusedMedia } = data;
  
  // Apply filters and sorting
  useEffect(() => {
    let filtered = [...unusedMedia];
    
    // Filter by type
    if (activeType !== 'all') {
      filtered = filtered.filter(item => item.type === activeType);
    }
    
    // Apply search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(item => 
        (item.name && item.name.toLowerCase().includes(term)) ||
        (item.path && item.path.toLowerCase().includes(term)) ||
        (item.id && item.id.toLowerCase().includes(term))
      );
    }
    
    // Apply sorting
    filtered.sort((a, b) => {
      let valueA, valueB;
      
      // Get values to compare based on sort field
      switch (sortBy) {
        case 'name':
          valueA = a.name || '';
          valueB = b.name || '';
          break;
        case 'type':
          valueA = a.type || '';
          valueB = b.type || '';
          break;
        case 'duration':
          valueA = a.duration || 0;
          valueB = b.duration || 0;
          break;
        case 'size':
          valueA = a.size || 0;
          valueB = b.size || 0;
          break;
        default:
          valueA = a.name || '';
          valueB = b.name || '';
      }
      
      // Compare values
      if (typeof valueA === 'string') {
        const result = valueA.localeCompare(valueB);
        return sortDirection === 'asc' ? result : -result;
      } else {
        const result = valueA - valueB;
        return sortDirection === 'asc' ? result : -result;
      }
    });
    
    setFilteredMedia(filtered);
  }, [unusedMedia, searchTerm, activeType, sortBy, sortDirection]);
  
  // Count unused media by type
  const unusedCounts = unusedMedia.reduce((counts, item) => {
    const type = item.type || 'unknown';
    counts[type] = (counts[type] || 0) + 1;
    return counts;
  }, {});
  
  // Total count of unused media
  const totalUnused = unusedMedia.length;
  
  // Handle search input
  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
  };
  
  // Handle type filter change
  const handleTypeChange = (type) => {
    setActiveType(type);
  };
  
  // Handle sort change
  const handleSortChange = (field) => {
    if (sortBy === field) {
      // Toggle direction if same field
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      // New field, reset to ascending
      setSortBy(field);
      setSortDirection('asc');
    }
  };
  
  // Download unused media list as CSV
  const downloadCSV = () => {
    // Build CSV content
    const headers = ['Name', 'Type', 'Path', 'ID', 'Duration', 'Size'];
    
    const rows = unusedMedia.map(item => [
      item.name || 'Unnamed',
      item.type || 'Unknown',
      item.path || 'N/A',
      item.id || 'N/A',
      item.duration ? formatDuration(item.duration) : 'N/A',
      item.size ? formatFileSize(item.size) : 'N/A'
    ]);
    
    // Combine headers and rows
    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell.replace(/"/g, '""')}"`).join(','))
    ].join('\n');
    
    // Create and trigger download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'unused_media.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };
  
  return (
    <div>
      <Card className="mb-4">
        <Card.Header>
          <div className="d-flex justify-content-between align-items-center">
            <h5 className="mb-0">Unused Media Analysis</h5>
            <div className="d-flex">
              <Form.Control
                type="text"
                placeholder="Search unused media..."
                value={searchTerm}
                onChange={handleSearchChange}
                style={{ width: '250px', marginRight: '10px' }}
              />
              <Button variant="outline-secondary" onClick={downloadCSV}>
                <i className="fas fa-download me-2"></i>
                Export CSV
              </Button>
            </div>
          </div>
        </Card.Header>
        <Card.Body>
          <div className="mb-4">
            <div className="d-flex flex-wrap gap-2">
              <Button 
                variant={activeType === 'all' ? 'primary' : 'outline-primary'}
                onClick={() => handleTypeChange('all')}
              >
                All ({totalUnused})
              </Button>
              
              {Object.entries(unusedCounts).map(([type, count]) => (
                <Button 
                  key={type}
                  variant={activeType === type ? 'primary' : 'outline-primary'}
                  onClick={() => handleTypeChange(type)}
                >
                  {type} ({count})
                </Button>
              ))}
            </div>
          </div>
          
          <div className="mb-3">
            <div className="d-flex justify-content-between align-items-center">
              <div>
                <strong>Found {filteredMedia.length} unused media files</strong>
                {activeType !== 'all' && ` of type ${activeType}`}
                {searchTerm && ` matching "${searchTerm}"`}
              </div>
              
              <div>
                Sort by: 
                <Button 
                  variant="link" 
                  className="p-0 mx-2"
                  onClick={() => handleSortChange('name')}
                >
                  Name
                  {sortBy === 'name' && (
                    <i className={`fas fa-sort-${sortDirection === 'asc' ? 'up' : 'down'} ms-1`}></i>
                  )}
                </Button>
                |
                <Button 
                  variant="link" 
                  className="p-0 mx-2"
                  onClick={() => handleSortChange('type')}
                >
                  Type
                  {sortBy === 'type' && (
                    <i className={`fas fa-sort-${sortDirection === 'asc' ? 'up' : 'down'} ms-1`}></i>
                  )}
                </Button>
                |
                <Button 
                  variant="link" 
                  className="p-0 mx-2"
                  onClick={() => handleSortChange('duration')}
                >
                  Duration
                  {sortBy === 'duration' && (
                    <i className={`fas fa-sort-${sortDirection === 'asc' ? 'up' : 'down'} ms-1`}></i>
                  )}
                </Button>
              </div>
            </div>
          </div>
          
          {filteredMedia.length === 0 ? (
            <div className="text-center p-4">
              <p className="text-muted">No unused media found matching the current filters.</p>
            </div>
          ) : (
            <Row className="media-grid">
              {filteredMedia.map((item, index) => (
                <Col key={`${item.id || item.path || index}`} lg={3} md={4} sm={6} xs={12}>
                  <div className="media-item unused">
                    <div className="d-flex align-items-center mb-2">
                      <i className={`fas fa-${item.type === 'video' ? 'video' : item.type === 'audio' ? 'music' : 'image'} me-2`}></i>
                      <h6 className="mb-0 text-truncate">{item.name || 'Unnamed'}</h6>
                    </div>
                    
                    <div className="media-details">
                      <p className="mb-1 text-muted">Type: {item.type || 'Unknown'}</p>
                      {item.duration && (
                        <p className="mb-1 text-muted">Duration: {formatDuration(item.duration)}</p>
                      )}
                      {(item.width && item.height) && (
                        <p className="mb-1 text-muted">Dimensions: {item.width}×{item.height}</p>
                      )}
                      {item.path && (
                        <p className="mb-0 text-muted text-truncate" title={item.path}>
                          Path: {item.path.split('/').pop()}
                        </p>
                      )}
                    </div>
                  </div>
                </Col>
              ))}
            </Row>
          )}
        </Card.Body>
      </Card>
      
      <Card>
        <Card.Header>
          <h5 className="mb-0">Cleanup Recommendations</h5>
        </Card.Header>
        <Card.Body>
          <div className="row">
            <div className="col-md-6">
              <h6>Why Remove Unused Media?</h6>
              <ul>
                <li>Reduce project file size</li>
                <li>Improve project loading times</li>
                <li>Declutter your media panel</li>
                <li>Simplify project management</li>
                <li>Prevent accidental use of wrong assets</li>
              </ul>
            </div>
            
            <div className="col-md-6">
              <h6>How to Clean Up</h6>
              <ol>
                <li>In CapCut, go to the Media panel</li>
                <li>Right-click on each unused media file</li>
                <li>Select "Remove" from the context menu</li>
                <li>Save your project</li>
              </ol>
              <p>Note: Use the Export CSV feature to create a reference list for cleanup.</p>
            </div>
          </div>
        </Card.Body>
      </Card>
    </div>
  );
}

export default UnusedMedia;