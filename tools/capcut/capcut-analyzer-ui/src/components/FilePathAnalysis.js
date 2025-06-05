import React, { useState, useEffect, useRef } from 'react';
import { Card } from 'react-bootstrap';
import * as d3 from 'd3';

function FilePathAnalysis({ data }) {
  const [treeData, setTreeData] = useState(null);
  const chartRef = useRef(null);
  
  if (!data) return <div>No data available</div>;
  
  // Build directory tree from media paths
  useEffect(() => {
    if (!data.materials) return;
    
    // Collect all paths from materials
    const allPaths = [];
    
    for (const type in data.materials) {
      for (const item of data.materials[type]) {
        if (item.path) {
          allPaths.push({
            path: item.path,
            type: item.type,
            isUsed: !data.unusedMedia?.some(unused => unused.id === item.id || unused.path === item.path)
          });
        }
      }
    }
    
    // Build tree structure
    const root = { name: 'root', children: [] };
    
    for (const { path, type, isUsed } of allPaths) {
      const parts = path.split('/').filter(Boolean);
      let currentNode = root;
      
      // Process each path part
      for (let i = 0; i < parts.length; i++) {
        const part = parts[i];
        let existingNode = currentNode.children.find(child => child.name === part);
        
        if (!existingNode) {
          // Last part is the file
          const isFile = i === parts.length - 1;
          
          existingNode = {
            name: part,
            isFile,
            type: isFile ? type : 'directory',
            isUsed: isFile ? isUsed : undefined,
            children: []
          };
          
          currentNode.children.push(existingNode);
        }
        
        currentNode = existingNode;
      }
    }
    
    setTreeData(root);
  }, [data]);
  
  // Render tree visualization
  useEffect(() => {
    if (!treeData || !chartRef.current) return;
    
    // Clear previous chart
    d3.select(chartRef.current).selectAll('*').remove();
    
    // Set up dimensions
    const width = chartRef.current.clientWidth;
    const height = Math.max(500, treeData.children.length * 20);
    
    // Create SVG
    const svg = d3.select(chartRef.current)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .append('g')
      .attr('transform', 'translate(40,0)');
    
    // Set up tree layout
    const treeLayout = d3.tree().size([height, width - 160]);
    
    // Create root hierarchy
    const root = d3.hierarchy(treeData);
    
    // Assign positions
    treeLayout(root);
    
    // Add links
    svg.selectAll('.link')
      .data(root.links())
      .enter()
      .append('path')
      .attr('class', 'link')
      .attr('d', d3.linkHorizontal()
        .x(d => d.y)
        .y(d => d.x))
      .style('fill', 'none')
      .style('stroke', 'var(--border-color)')
      .style('stroke-width', '1.5px');
    
    // Add nodes
    const nodes = svg.selectAll('.node')
      .data(root.descendants())
      .enter()
      .append('g')
      .attr('class', 'node')
      .attr('transform', d => `translate(${d.y},${d.x})`);
    
    // Add circles to nodes
    nodes.append('circle')
      .attr('r', d => d.data.isFile ? 4 : 6)
      .style('fill', d => {
        if (d.data.isFile) {
          return d.data.isUsed ? 'var(--used-media)' : 'var(--unused-media)';
        }
        return 'var(--primary-color)';
      })
      .style('stroke', 'var(--bg-medium)')
      .style('stroke-width', '1.5px');
    
    // Add labels to nodes
    nodes.append('text')
      .attr('dy', '0.31em')
      .attr('x', d => d.children ? -8 : 8)
      .style('text-anchor', d => d.children ? 'end' : 'start')
      .style('font-size', '12px')
      .style('fill', 'var(--text-light)')
      .text(d => d.data.name)
      .append('title')
      .text(d => {
        if (d.data.isFile) {
          return `${d.data.name}\nType: ${d.data.type}\nStatus: ${d.data.isUsed ? 'Used' : 'Unused'}`;
        }
        return d.data.name;
      });
    
  }, [treeData]);
  
  return (
    <div>
      <Card className="mb-4">
        <Card.Header>
          <h5 className="mb-0">File Path Analysis</h5>
        </Card.Header>
        <Card.Body>
          <div ref={chartRef} style={{ width: '100%', height: '500px', overflow: 'auto' }} />
        </Card.Body>
      </Card>
      
      <Card>
        <Card.Header>
          <h5 className="mb-0">Directory Structure Overview</h5>
        </Card.Header>
        <Card.Body>
          <div className="row">
            <div className="col-md-12">
              <p>This visualization shows the directory structure of all media files in your project. Files are color-coded:</p>
              <ul>
                <li><span style={{ color: 'var(--used-media)' }}>●</span> Green nodes are used media files</li>
                <li><span style={{ color: 'var(--unused-media)' }}>●</span> Red nodes are unused media files</li>
                <li><span style={{ color: 'var(--primary-color)' }}>●</span> Blue nodes are directories</li>
              </ul>
              
              <p>This view can help you identify:</p>
              <ul>
                <li>Directories with high concentrations of unused media</li>
                <li>Organizational patterns in your project files</li>
                <li>Potential areas for cleanup and reorganization</li>
              </ul>
              
              <p><strong>Tip:</strong> Hover over any node to see details about that file or directory.</p>
            </div>
          </div>
        </Card.Body>
      </Card>
    </div>
  );
}

export default FilePathAnalysis;