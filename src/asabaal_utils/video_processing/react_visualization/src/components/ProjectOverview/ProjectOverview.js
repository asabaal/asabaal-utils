import React, { useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import * as d3 from 'd3';
import './ProjectOverview.css';

const ProjectOverview = ({ mediaInfo, timelineInfo, relationshipInfo }) => {
  const mediaPieChartRef = useRef(null);
  const mediaTypeChartRef = useRef(null);

  // Create media usage pie chart using D3
  useEffect(() => {
    if (!mediaInfo || !relationshipInfo || !mediaPieChartRef.current) return;

    // Clear previous chart
    d3.select(mediaPieChartRef.current).selectAll('*').remove();

    const usedCount = mediaInfo.total_count - (relationshipInfo.unused_media?.length || 0);
    const unusedCount = relationshipInfo.unused_media?.length || 0;

    if (mediaInfo.total_count === 0) return;

    const width = mediaPieChartRef.current.clientWidth;
    const height = 250;
    const radius = Math.min(width, height) / 2;

    // Create SVG
    const svg = d3.select(mediaPieChartRef.current)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .append('g')
      .attr('transform', `translate(${width / 2}, ${height / 2})`);

    // Create pie chart data
    const pie = d3.pie().value(d => d.value);
    const data = pie([
      { name: 'Used', value: usedCount, color: '#2ecc71' },
      { name: 'Unused', value: unusedCount, color: '#e74c3c' }
    ]);

    // Create arc generator
    const arc = d3.arc()
      .innerRadius(radius * 0.6) // Donut chart
      .outerRadius(radius * 0.9);

    // Create outer arc for labels
    const outerArc = d3.arc()
      .innerRadius(radius * 1.1)
      .outerRadius(radius * 1.1);

    // Add pie slices
    svg.selectAll('path')
      .data(data)
      .enter()
      .append('path')
      .attr('d', arc)
      .attr('fill', d => d.data.color)
      .attr('stroke', '#222')
      .attr('stroke-width', 1)
      .style('cursor', 'pointer')
      .on('click', (event, d) => {
        // Navigate to media tab with appropriate filter
        window.location.href = `/media?filter=${d.data.name.toLowerCase()}`;
      });

    // Add percentage labels inside pie
    svg.selectAll('text.percentage')
      .data(data)
      .enter()
      .append('text')
      .attr('class', 'percentage')
      .attr('transform', d => `translate(${arc.centroid(d)})`)
      .attr('dy', '0.35em')
      .style('text-anchor', 'middle')
      .style('font-size', '16px')
      .style('font-weight', 'bold')
      .style('fill', '#fff')
      .text(d => `${Math.round((d.data.value / mediaInfo.total_count) * 100)}%`);

    // Add labels with lines
    svg.selectAll('polyline')
      .data(data)
      .enter()
      .append('polyline')
      .attr('points', d => {
        const pos = outerArc.centroid(d);
        pos[0] = radius * (d.startAngle + (d.endAngle - d.startAngle) / 2 < Math.PI ? 1.2 : -1.2);
        return [arc.centroid(d), outerArc.centroid(d), pos];
      })
      .style('fill', 'none')
      .style('stroke', d => d.data.color)
      .style('stroke-width', 1);

    // Add external labels
    svg.selectAll('text.label')
      .data(data)
      .enter()
      .append('text')
      .attr('class', 'label')
      .attr('transform', d => {
        const pos = outerArc.centroid(d);
        pos[0] = radius * (d.startAngle + (d.endAngle - d.startAngle) / 2 < Math.PI ? 1.3 : -1.3);
        return `translate(${pos})`;
      })
      .style('text-anchor', d => d.startAngle + (d.endAngle - d.startAngle) / 2 < Math.PI ? 'start' : 'end')
      .style('font-size', '14px')
      .style('fill', '#eee')
      .text(d => `${d.data.name}: ${d.data.value}`);

  }, [mediaInfo, relationshipInfo]);

  // Create media type chart
  useEffect(() => {
    if (!mediaInfo || !mediaTypeChartRef.current) return;

    // Clear previous chart
    d3.select(mediaTypeChartRef.current).selectAll('*').remove();

    // Prepare data
    const data = Object.entries(mediaInfo.type_counts || {}).map(([type, count]) => ({
      type,
      count,
      color: type === 'video' ? '#f39c12' : type === 'audio' ? '#9b59b6' : '#1abc9c'
    }));

    if (data.length === 0) return;

    const width = mediaTypeChartRef.current.clientWidth;
    const height = 250;
    const margin = { top: 20, right: 30, bottom: 40, left: 50 };
    const chartWidth = width - margin.left - margin.right;
    const chartHeight = height - margin.top - margin.bottom;

    // Create SVG
    const svg = d3.select(mediaTypeChartRef.current)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .append('g')
      .attr('transform', `translate(${margin.left}, ${margin.top})`);

    // Create scales
    const x = d3.scaleBand()
      .domain(data.map(d => d.type))
      .range([0, chartWidth])
      .padding(0.3);

    const y = d3.scaleLinear()
      .domain([0, d3.max(data, d => d.count)])
      .nice()
      .range([chartHeight, 0]);

    // Add X axis
    svg.append('g')
      .attr('transform', `translate(0, ${chartHeight})`)
      .call(d3.axisBottom(x))
      .selectAll('text')
      .style('text-anchor', 'middle')
      .style('fill', '#eee')
      .style('font-size', '12px')
      .attr('dy', '1em');

    // Add Y axis
    svg.append('g')
      .call(d3.axisLeft(y).ticks(5))
      .selectAll('text')
      .style('fill', '#eee')
      .style('font-size', '12px');

    // Add axis titles
    svg.append('text')
      .attr('text-anchor', 'middle')
      .attr('x', chartWidth / 2)
      .attr('y', chartHeight + margin.bottom - 5)
      .style('fill', '#eee')
      .style('font-size', '12px')
      .text('Media Type');

    svg.append('text')
      .attr('text-anchor', 'middle')
      .attr('transform', `rotate(-90)`)
      .attr('x', -chartHeight / 2)
      .attr('y', -margin.left + 15)
      .style('fill', '#eee')
      .style('font-size', '12px')
      .text('Count');

    // Add bars
    svg.selectAll('.bar')
      .data(data)
      .enter()
      .append('rect')
      .attr('class', 'bar')
      .attr('x', d => x(d.type))
      .attr('y', d => y(d.count))
      .attr('width', x.bandwidth())
      .attr('height', d => chartHeight - y(d.count))
      .attr('fill', d => d.color)
      .attr('rx', 4)
      .attr('ry', 4)
      .style('cursor', 'pointer')
      .on('click', (event, d) => {
        // Navigate to media tab with type filter
        window.location.href = `/media?type=${d.type}`;
      });

    // Add labels on top of bars
    svg.selectAll('.label')
      .data(data)
      .enter()
      .append('text')
      .attr('class', 'label')
      .attr('x', d => x(d.type) + x.bandwidth() / 2)
      .attr('y', d => y(d.count) - 5)
      .attr('text-anchor', 'middle')
      .style('fill', '#eee')
      .style('font-size', '12px')
      .text(d => d.count);

  }, [mediaInfo]);

  return (
    <div className="project-overview">
      <h2 className="page-title mb-4">Project Overview</h2>
      
      {/* Stats Cards */}
      <div className="row">
        <div className="col-md-3">
          <div className="card stats-card">
            <div className="card-body">
              <div className="stats-number">{mediaInfo.total_count || 0}</div>
              <div className="stats-label">Media Files</div>
            </div>
          </div>
        </div>
        <div className="col-md-3">
          <div className="card stats-card">
            <div className="card-body">
              <div className="stats-number">{relationshipInfo.unused_media?.length || 0}</div>
              <div className="stats-label">Unused Media</div>
            </div>
          </div>
        </div>
        <div className="col-md-3">
          <div className="card stats-card">
            <div className="card-body">
              <div className="stats-number">{timelineInfo.total_tracks || 0}</div>
              <div className="stats-label">Timeline Tracks</div>
            </div>
          </div>
        </div>
        <div className="col-md-3">
          <div className="card stats-card">
            <div className="card-body">
              <div className="stats-number">{timelineInfo.total_clips || 0}</div>
              <div className="stats-label">Timeline Clips</div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Charts */}
      <div className="row mt-4">
        <div className="col-md-6">
          <div className="card">
            <div className="card-body">
              <h5 className="card-title">Media Usage</h5>
              <div ref={mediaPieChartRef} className="chart-container"></div>
              <div className="text-center mt-3">
                <Link to="/media" className="btn btn-primary">
                  <i className="fas fa-photo-video me-2"></i>
                  Explore Media Files
                </Link>
              </div>
            </div>
          </div>
        </div>
        <div className="col-md-6">
          <div className="card">
            <div className="card-body">
              <h5 className="card-title">Media Types</h5>
              <div ref={mediaTypeChartRef} className="chart-container"></div>
              <div className="text-center mt-3">
                <Link to="/timeline" className="btn btn-primary">
                  <i className="fas fa-film me-2"></i>
                  Explore Timeline
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Unused Media Section */}
      {relationshipInfo.unused_media && relationshipInfo.unused_media.length > 0 && (
        <div className="row mt-4">
          <div className="col-md-12">
            <div className="card">
              <div className="card-header bg-warning">
                <h5 className="card-title mb-0 text-dark">
                  <i className="fas fa-exclamation-triangle me-2"></i>
                  Unused Media Files ({relationshipInfo.unused_media.length})
                </h5>
              </div>
              <div className="card-body">
                <p>These files are in your project but not used in the timeline:</p>
                <div className="unused-media-list">
                  {relationshipInfo.unused_media.slice(0, 5).map((media, index) => (
                    <div key={index} className="media-item unused">
                      <div className="row">
                        <div className="col-md-1">
                          <i className={`fas fa-${media.type === 'video' ? 'video' : media.type === 'audio' ? 'music' : 'image'} fa-2x media-type-${media.type}`}></i>
                        </div>
                        <div className="col-md-11">
                          <h6>{media.name}</h6>
                          <p className="text-muted mb-0">{media.path}</p>
                          {media.duration && (
                            <p className="mb-0"><small>Duration: {formatDuration(media.duration)}</small></p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                  {relationshipInfo.unused_media.length > 5 && (
                    <div className="text-center mt-3">
                      <Link to="/media?filter=unused" className="btn btn-outline-warning">
                        Show All {relationshipInfo.unused_media.length} Unused Files
                      </Link>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
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

export default ProjectOverview;