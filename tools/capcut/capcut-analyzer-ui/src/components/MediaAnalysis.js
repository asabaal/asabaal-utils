import React, { useState, useEffect } from 'react';
import { Card, Form, Tabs, Tab, Table } from 'react-bootstrap';
import { formatDuration, formatFileSize } from '../utils/formatters';

function MediaAnalysis({ data }) {
  const [activeTab, setActiveTab] = useState('videos');
  const [searchTerm, setSearchTerm] = useState('');
  const [mediaItems, setMediaItems] = useState([]);
  
  if (!data || !data.materials) return <div>No media data available</div>;
  
  // Determine which media items to show based on active tab
  useEffect(() => {
    let items = [];
    
    if (data.materials[activeTab]) {
      items = data.materials[activeTab];
    }
    
    // Mark used vs unused
    if (data.unusedMedia) {
      const unusedIds = new Set(data.unusedMedia.map(m => m.id));
      
      items = items.map(item => ({
        ...item,
        isUsed: !unusedIds.has(item.id)
      }));
    }
    
    // Apply search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      items = items.filter(item => 
        (item.name && item.name.toLowerCase().includes(term)) ||
        (item.path && item.path.toLowerCase().includes(term)) ||
        (item.id && item.id.toLowerCase().includes(term))
      );
    }
    
    setMediaItems(items);
  }, [activeTab, searchTerm, data]);
  
  // Count items by type
  const counts = {
    videos: data.materials.videos?.length || 0,
    audios: data.materials.audios?.length || 0,
    texts: data.materials.texts?.length || 0,
    images: data.materials.images?.length || 0,
    effects: data.materials.effects?.length || 0,
    stickers: data.materials.stickers?.length || 0,
    transitions: data.materials.transitions?.length || 0
  };
  
  // Handle search input
  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
  };
  
  return (
    <div>
      <Card className="mb-4">
        <Card.Header>
          <div className="d-flex justify-content-between align-items-center">
            <h5 className="mb-0">Media Library Analysis</h5>
            <Form.Control
              type="text"
              placeholder="Search media..."
              value={searchTerm}
              onChange={handleSearchChange}
              style={{ width: '300px' }}
            />
          </div>
        </Card.Header>
        <Card.Body>
          <Tabs
            activeKey={activeTab}
            onSelect={(k) => setActiveTab(k)}
            className="mb-3"
          >
            <Tab eventKey="videos" title={`Videos (${counts.videos})`} />
            <Tab eventKey="audios" title={`Audio (${counts.audios})`} />
            <Tab eventKey="texts" title={`Text (${counts.texts})`} />
            <Tab eventKey="images" title={`Images (${counts.images})`} />
            {counts.effects > 0 && <Tab eventKey="effects" title={`Effects (${counts.effects})`} />}
            {counts.stickers > 0 && <Tab eventKey="stickers" title={`Stickers (${counts.stickers})`} />}
            {counts.transitions > 0 && <Tab eventKey="transitions" title={`Transitions (${counts.transitions})`} />}
          </Tabs>
          
          {mediaItems.length === 0 ? (
            <div className="text-center p-4">
              <p className="text-muted">No {activeTab} found{searchTerm ? ' matching search criteria' : ''}.</p>
            </div>
          ) : (
            <Table responsive variant="dark" className="media-table">
              <thead>
                <tr>
                  <th>Status</th>
                  <th>Name</th>
                  <th>Type</th>
                  {activeTab === 'videos' && <th>Duration</th>}
                  {activeTab === 'audios' && <th>Duration</th>}
                  {(activeTab === 'videos' || activeTab === 'images') && <th>Dimensions</th>}
                  <th>Path</th>
                </tr>
              </thead>
              <tbody>
                {mediaItems.map((item, index) => (
                  <tr key={`${item.id || item.path || index}`}>
                    <td>
                      <span className={`badge ${item.isUsed ? 'bg-success' : 'bg-danger'}`}>
                        {item.isUsed ? 'Used' : 'Unused'}
                      </span>
                    </td>
                    <td>{item.name || 'Unnamed'}</td>
                    <td>{item.type}</td>
                    {activeTab === 'videos' && (
                      <td>{item.duration ? formatDuration(item.duration) : 'N/A'}</td>
                    )}
                    {activeTab === 'audios' && (
                      <td>{item.duration ? formatDuration(item.duration) : 'N/A'}</td>
                    )}
                    {(activeTab === 'videos' || activeTab === 'images') && (
                      <td>
                        {item.width && item.height ? `${item.width}×${item.height}` : 'N/A'}
                      </td>
                    )}
                    <td style={{ maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {item.path || 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </Card.Body>
      </Card>
      
      <Card>
        <Card.Header>
          <h5 className="mb-0">Usage Statistics</h5>
        </Card.Header>
        <Card.Body>
          <div className="row">
            <div className="col-md-6">
              <h6>Media Usage by Type</h6>
              <Table responsive variant="dark">
                <thead>
                  <tr>
                    <th>Type</th>
                    <th>Total</th>
                    <th>Used</th>
                    <th>Unused</th>
                    <th>Usage %</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(counts).filter(([_, count]) => count > 0).map(([type, count]) => {
                    // Calculate used/unused for each type
                    const unusedCount = data.unusedMedia ? 
                      data.unusedMedia.filter(m => m.type?.toLowerCase() === type.slice(0, -1)).length : 0;
                    const usedCount = count - unusedCount;
                    const usagePercent = count > 0 ? Math.round((usedCount / count) * 100) : 0;
                    
                    return (
                      <tr key={type}>
                        <td style={{ textTransform: 'capitalize' }}>{type}</td>
                        <td>{count}</td>
                        <td>{usedCount}</td>
                        <td>{unusedCount}</td>
                        <td>
                          <div className="progress" style={{ height: '5px', width: '100px' }}>
                            <div 
                              className="progress-bar" 
                              role="progressbar" 
                              style={{ 
                                width: `${usagePercent}%`, 
                                backgroundColor: usagePercent > 50 ? 'var(--used-media)' : 'var(--unused-media)' 
                              }}
                              aria-valuenow={usagePercent} 
                              aria-valuemin="0" 
                              aria-valuemax="100"
                            />
                          </div>
                          <span className="ms-2">{usagePercent}%</span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </Table>
            </div>
            
            <div className="col-md-6">
              {/* Add a pie chart or other visualization here */}
              <h6>Media Path Analysis</h6>
              <p>Group media files by directory structure:</p>
              
              <div className="directory-tree">
                {(() => {
                  // Build directory tree
                  const tree = {};
                  
                  // Add all media items to the tree
                  for (const type in data.materials) {
                    for (const item of data.materials[type]) {
                      if (!item.path) continue;
                      
                      const pathParts = item.path.split('/');
                      let currentLevel = tree;
                      
                      // Skip the last part (filename)
                      for (let i = 0; i < pathParts.length - 1; i++) {
                        const part = pathParts[i];
                        if (!part) continue;
                        
                        if (!currentLevel[part]) {
                          currentLevel[part] = { 
                            _count: 0,
                            _used: 0,
                            _unused: 0
                          };
                        }
                        
                        currentLevel[part]._count++;
                        
                        // Update used/unused counts
                        if (data.unusedMedia && data.unusedMedia.some(m => m.id === item.id || m.path === item.path)) {
                          currentLevel[part]._unused++;
                        } else {
                          currentLevel[part]._used++;
                        }
                        
                        currentLevel = currentLevel[part];
                      }
                    }
                  }
                  
                  // Render tree as a list
                  const renderTree = (node, depth = 0, path = '') => {
                    return (
                      <ul style={{ listStyle: 'none', paddingLeft: depth > 0 ? '20px' : '0' }}>
                        {Object.entries(node)
                          .filter(([key]) => !key.startsWith('_'))
                          .sort(([keyA], [keyB]) => keyA.localeCompare(keyB))
                          .map(([key, value]) => {
                            const fullPath = path ? `${path}/${key}` : key;
                            const usedPercent = value._count > 0 ? Math.round((value._used / value._count) * 100) : 0;
                            
                            return (
                              <li key={fullPath}>
                                <div className="d-flex align-items-center">
                                  <span>
                                    <i className="fas fa-folder me-2"></i>
                                    {key} 
                                    <span className="text-muted ms-2">
                                      ({value._count} files, {value._used} used, {value._unused} unused)
                                    </span>
                                  </span>
                                  <div className="progress ms-3" style={{ height: '5px', width: '60px', flex: '0 0 60px' }}>
                                    <div 
                                      className="progress-bar" 
                                      role="progressbar" 
                                      style={{ 
                                        width: `${usedPercent}%`, 
                                        backgroundColor: usedPercent > 50 ? 'var(--used-media)' : 'var(--unused-media)' 
                                      }}
                                    />
                                  </div>
                                </div>
                                {renderTree(value, depth + 1, fullPath)}
                              </li>
                            );
                          })}
                      </ul>
                    );
                  };
                  
                  return renderTree(tree);
                })()}
              </div>
            </div>
          </div>
        </Card.Body>
      </Card>
    </div>
  );
}

export default MediaAnalysis;