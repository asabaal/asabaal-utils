import React, { useState, useEffect, useRef } from 'react';
import { Card, Form } from 'react-bootstrap';
import { formatDuration } from '../utils/formatters';
import * as d3 from 'd3';

function Timeline({ data }) {
  const [selectedSegment, setSelectedSegment] = useState(null);
  const [zoom, setZoom] = useState(1);
  const timelineRef = useRef(null);
  
  if (!data || !data.timeline) return <div>No timeline data available</div>;
  
  const { timeline, materials } = data;
  
  // Get material details for a segment
  const getMaterialForSegment = (segment) => {
    if (!segment || !segment.materialId) return null;
    
    // Search in all material types
    for (const type in materials) {
      const materialArray = materials[type];
      const material = materialArray.find(m => m.id === segment.materialId);
      if (material) return { ...material, type };
    }
    
    return null;
  };
  
  // Handle zoom change
  const handleZoomChange = (e) => {
    setZoom(parseFloat(e.target.value));
  };
  
  // Handle segment click
  const handleSegmentClick = (segment) => {
    setSelectedSegment(segment);
  };
  
  // Calculate timeline width based on zoom
  const timelineWidth = `${100 * zoom}%`;
  
  return (
    <div>
      <Card className="mb-4">
        <Card.Header className="d-flex justify-content-between align-items-center">
          <h5 className="mb-0">Timeline Analysis</h5>
          <div style={{ width: '200px' }}>
            <Form.Label htmlFor="zoom-control">Zoom: {zoom}x</Form.Label>
            <Form.Range
              id="zoom-control"
              min="0.5"
              max="5"
              step="0.1"
              value={zoom}
              onChange={handleZoomChange}
            />
          </div>
        </Card.Header>
        <Card.Body>
          <div className="timeline-container" ref={timelineRef}>
            <div style={{ width: timelineWidth, position: 'relative' }}>
              {/* Time markers */}
              <div className="timeline-markers" style={{ height: '20px', position: 'relative', marginBottom: '10px' }}>
                {Array.from({ length: Math.ceil(timeline.duration / 60000000) + 1 }).map((_, i) => (
                  <div
                    key={`marker-${i}`}
                    style={{
                      position: 'absolute',
                      left: `${(i * 60000000 / timeline.duration) * 100}%`,
                      height: '20px',
                      borderLeft: i === 0 ? 'none' : '1px solid var(--border-color)',
                      paddingLeft: '5px',
                      fontSize: '12px',
                      color: 'var(--text-muted)'
                    }}
                  >
                    {formatDuration(i * 60)}
                  </div>
                ))}
              </div>
              
              {/* Tracks */}
              {timeline.tracks.map((track) => (
                <div key={track.id} className="timeline-track">
                  <div 
                    style={{
                      position: 'absolute',
                      left: '0',
                      top: '0',
                      padding: '2px 5px',
                      fontSize: '12px',
                      backgroundColor: 'var(--bg-dark)',
                      borderRadius: '3px',
                      zIndex: 5
                    }}
                  >
                    {track.name}
                  </div>
                  
                  {/* Segments */}
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
                          onClick={() => handleSegmentClick(segment)}
                        />
                      );
                    })}
                </div>
              ))}
            </div>
          </div>
        </Card.Body>
      </Card>
      
      {selectedSegment && (
        <Card>
          <Card.Header>
            <h5 className="mb-0">Segment Details</h5>
          </Card.Header>
          <Card.Body>
            <div className="row">
              <div className="col-md-6">
                <h6>Timeline Information</h6>
                <p><strong>Track:</strong> {timeline.tracks.find(t => t.index === selectedSegment.trackIndex)?.name}</p>
                <p><strong>Start Time:</strong> {formatDuration(selectedSegment.startTime / 1000000)}</p>
                <p><strong>End Time:</strong> {formatDuration((selectedSegment.startTime + selectedSegment.duration) / 1000000)}</p>
                <p><strong>Duration:</strong> {formatDuration(selectedSegment.duration / 1000000)}</p>
              </div>
              
              <div className="col-md-6">
                <h6>Material Information</h6>
                {selectedSegment.materialId ? (
                  (() => {
                    const material = getMaterialForSegment(selectedSegment);
                    
                    if (material) {
                      return (
                        <>
                          <p><strong>Material ID:</strong> {material.id}</p>
                          <p><strong>Type:</strong> {material.type}</p>
                          <p><strong>Name:</strong> {material.name || 'Unnamed'}</p>
                          {material.path && <p><strong>Path:</strong> {material.path}</p>}
                          {material.duration && <p><strong>Duration:</strong> {formatDuration(material.duration)}</p>}
                        </>
                      );
                    } else {
                      return <p>Material ID: {selectedSegment.materialId} (details not found)</p>;
                    }
                  })()
                ) : (
                  <p>No material associated with this segment</p>
                )}
              </div>
            </div>
          </Card.Body>
        </Card>
      )}
    </div>
  );
}

export default Timeline;