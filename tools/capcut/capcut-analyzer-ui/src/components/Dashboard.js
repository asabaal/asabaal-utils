import React from 'react';
import { Card, Row, Col } from 'react-bootstrap';
import { formatDuration } from '../utils/formatters';

function Dashboard({ data }) {
  if (!data) return <div>No data available</div>;
  
  const { statistics, materials, timeline, unusedMedia } = data;
  
  // Calculate additional statistics
  const usedMaterials = statistics.totalMaterials - (unusedMedia?.length || 0);
  const usagePercentage = statistics.totalMaterials > 0 
    ? Math.round((usedMaterials / statistics.totalMaterials) * 100) 
    : 0;
  
  // Get material counts by type
  const videosCount = materials.videos?.length || 0;
  const audiosCount = materials.audios?.length || 0;
  const textsCount = materials.texts?.length || 0;
  const imagesCount = materials.images?.length || 0;
  
  return (
    <div className="dashboard-container">
      <Row>
        <Col>
          <Card className="mb-4">
            <Card.Header>
              <h5 className="mb-0">Project Overview</h5>
            </Card.Header>
            <Card.Body>
              <div className="stats-container">
                <div className="stat-card">
                  <div className="stat-label">Total Duration</div>
                  <div className="stat-value">{formatDuration(timeline.duration / 1000000)}</div>
                  <div className="stat-description">Total timeline length</div>
                </div>
                
                <div className="stat-card">
                  <div className="stat-label">Tracks</div>
                  <div className="stat-value">{timeline.tracks.length}</div>
                  <div className="stat-description">Timeline tracks</div>
                </div>
                
                <div className="stat-card">
                  <div className="stat-label">Segments</div>
                  <div className="stat-value">{timeline.segments.length}</div>
                  <div className="stat-description">Timeline segments</div>
                </div>
                
                <div className="stat-card">
                  <div className="stat-label">Media Usage</div>
                  <div className="stat-value">{usagePercentage}%</div>
                  <div className="stat-description">
                    {usedMaterials} of {statistics.totalMaterials} materials used
                  </div>
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>
      
      <Row>
        <Col md={6}>
          <Card className="mb-4">
            <Card.Header>
              <h5 className="mb-0">Media Library</h5>
            </Card.Header>
            <Card.Body>
              <div className="stats-container">
                <div className="stat-card">
                  <div className="stat-label">Videos</div>
                  <div className="stat-value">{videosCount}</div>
                </div>
                
                <div className="stat-card">
                  <div className="stat-label">Audio</div>
                  <div className="stat-value">{audiosCount}</div>
                </div>
                
                <div className="stat-card">
                  <div className="stat-label">Text</div>
                  <div className="stat-value">{textsCount}</div>
                </div>
                
                <div className="stat-card">
                  <div className="stat-label">Images</div>
                  <div className="stat-value">{imagesCount}</div>
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>
        
        <Col md={6}>
          <Card className="mb-4">
            <Card.Header>
              <h5 className="mb-0">Unused Media</h5>
            </Card.Header>
            <Card.Body>
              <div className="stats-container">
                <div className="stat-card">
                  <div className="stat-label">Unused Media Files</div>
                  <div className="stat-value">{unusedMedia?.length || 0}</div>
                  <div className="stat-description">Files in library but not in timeline</div>
                </div>
                
                <div className="stat-card">
                  <div className="stat-label">Usage Efficiency</div>
                  <div className="stat-value"
                       style={{ color: usagePercentage > 80 ? 'var(--used-media)' : 'var(--unused-media)' }}>
                    {usagePercentage}%
                  </div>
                  <div className="stat-description">Media usage efficiency</div>
                </div>
              </div>
              
              <div className="mt-3">
                <a href="#unused" onClick={() => document.querySelector('a[href="#unused"]').click()} 
                  className="btn btn-outline-danger">
                  View Unused Media
                </a>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>
      
      <Row>
        <Col>
          <Card>
            <Card.Header>
              <h5 className="mb-0">Timeline Preview</h5>
            </Card.Header>
            <Card.Body>
              <div className="timeline-preview">
                {timeline.tracks.map((track, index) => (
                  <div key={track.id} className="timeline-track">
                    <div className="track-label">{track.name}</div>
                    
                    {/* Render a simplified view of segments */}
                    {timeline.segments
                      .filter(segment => segment.trackIndex === track.index)
                      .map((segment, i) => {
                        const startPercent = (segment.startTime / timeline.duration) * 100;
                        const widthPercent = (segment.duration / timeline.duration) * 100;
                        
                        return (
                          <div
                            key={`${segment.id}-${i}`}
                            className={`timeline-segment track-${segment.trackIndex}`}
                            style={{
                              left: `${startPercent}%`,
                              width: `${widthPercent}%`
                            }}
                            title={`${formatDuration(segment.startTime / 1000000)} - ${formatDuration((segment.startTime + segment.duration) / 1000000)}`}
                          />
                        );
                      })}
                  </div>
                ))}
              </div>
              
              <div className="mt-3">
                <a href="#timeline" onClick={() => document.querySelector('a[href="#timeline"]').click()}
                  className="btn btn-outline-primary">
                  View Full Timeline
                </a>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </div>
  );
}

export default Dashboard;