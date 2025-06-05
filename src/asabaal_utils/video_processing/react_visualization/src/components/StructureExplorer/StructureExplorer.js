import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import './StructureExplorer.css';

const StructureExplorer = ({ projectData }) => {
  const treeContainerRef = useRef(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState([]);

  // Create the tree visualization
  useEffect(() => {
    if (!projectData || !treeContainerRef.current) return;
    
    // Clear previous visualization
    d3.select(treeContainerRef.current).selectAll('*').remove();
    
    // Create structure data for visualization
    const structureData = createStructureData(projectData);
    
    // Visualization dimensions
    const container = treeContainerRef.current;
    const width = container.clientWidth;
    const height = 600;
    
    // Create SVG container
    const svg = d3.select(container)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .append('g')
      .attr('transform', 'translate(40, 0)');
    
    // Create tree layout
    const treeLayout = d3.tree().size([height, width - 160]);
    
    // Create root hierarchy
    const root = d3.hierarchy(structureData);
    
    // Assign positions to nodes
    treeLayout(root);
    
    // Add links between nodes
    svg.selectAll('.link')
      .data(root.links())
      .enter()
      .append('path')
      .attr('class', 'link')
      .attr('d', d3.linkHorizontal()
        .x(d => d.y)
        .y(d => d.x));
    
    // Add node groups
    const nodes = svg.selectAll('.node')
      .data(root.descendants())
      .enter()
      .append('g')
      .attr('class', 'node')
      .attr('transform', d => `translate(${d.y},${d.x})`)
      .on('click', (event, d) => {
        setSelectedNode(d);
      });
    
    // Add circles to nodes
    nodes.append('circle')
      .attr('r', d => {
        // Size based on node type
        if (d.children) return Math.min(5 + d.children.length, 10);
        return d.data.size ? Math.min(3 + Math.sqrt(d.data.size), 8) : 4;
      })
      .style('fill', d => {
        // Color based on node type
        if (d.data.type === 'object') return '#3498db';
        if (d.data.type === 'array') return '#2ecc71';
        if (d.data.type === 'text' || d.data.type === 'string') return '#e67e22';
        if (d.data.type === 'longtext') return '#e74c3c';
        if (d.data.type === 'number') return '#f1c40f';
        return '#9b59b6';
      });
    
    // Add text labels to nodes
    nodes.append('text')
      .attr('dy', '.35em')
      .attr('x', d => d.children ? -12 : 12)
      .style('text-anchor', d => d.children ? 'end' : 'start')
      .text(d => d.data.name)
      .style('font-size', '12px');
    
    // Add tooltips
    nodes.append('title')
      .text(d => `${d.data.name}\nType: ${d.data.type}\nSize: ${d.data.size || 'N/A'}`);
      
  }, [projectData]);

  // Handle search
  useEffect(() => {
    if (!searchTerm.trim() || !projectData) {
      setSearchResults([]);
      return;
    }
    
    // Perform search
    const results = searchInObject(projectData, searchTerm.toLowerCase());
    setSearchResults(results);
  }, [searchTerm, projectData]);

  // Create tree structure data from project data
  const createStructureData = (data) => {
    const rootNode = {
      name: 'Project Root',
      children: []
    };
    
    // Add top-level keys
    for (const key in data) {
      const value = data[key];
      const node = { name: key };
      
      if (typeof value === 'object' && value !== null) {
        if (Array.isArray(value)) {
          node.type = 'array';
          node.size = value.length;
          
          // Add sample items for arrays
          if (value.length > 0) {
            node.children = [];
            const sampleCount = Math.min(value.length, 5);
            
            for (let i = 0; i < sampleCount; i++) {
              const childValue = value[i];
              const childType = getTypeFromValue(childValue);
              const childSize = getSizeFromValue(childValue);
              
              node.children.push({
                name: `[${i}]`,
                type: childType,
                size: childSize
              });
            }
            
            if (value.length > 5) {
              node.children.push({
                name: `... ${value.length - 5} more items`,
                type: 'ellipsis',
                size: 1
              });
            }
          }
        } else {
          node.type = 'object';
          node.size = Object.keys(value).length;
          
          // Add sample properties for objects
          node.children = [];
          const keys = Object.keys(value);
          const sampleCount = Math.min(keys.length, 10);
          
          for (let i = 0; i < sampleCount; i++) {
            const childKey = keys[i];
            const childValue = value[childKey];
            const childType = getTypeFromValue(childValue);
            const childSize = getSizeFromValue(childValue);
            
            node.children.push({
              name: childKey,
              type: childType,
              size: childSize
            });
          }
          
          if (keys.length > 10) {
            node.children.push({
              name: `... ${keys.length - 10} more properties`,
              type: 'ellipsis',
              size: 1
            });
          }
        }
      } else {
        node.type = getTypeFromValue(value);
        node.size = getSizeFromValue(value);
      }
      
      rootNode.children.push(node);
    }
    
    return rootNode;
  };

  // Get a descriptive type from a value
  const getTypeFromValue = (value) => {
    if (value === null) return 'null';
    if (Array.isArray(value)) return 'array';
    
    const type = typeof value;
    
    if (type === 'string') {
      return value.length > 100 ? 'longtext' : 'text';
    }
    
    return type;
  };

  // Get a size estimate from a value
  const getSizeFromValue = (value) => {
    if (value === null) return 1;
    if (Array.isArray(value)) return value.length;
    if (typeof value === 'object') return Object.keys(value).length;
    if (typeof value === 'string') return Math.min(value.length / 10, 100);
    
    return 1;
  };

  // Search in object recursively
  const searchInObject = (obj, term, path = '', results = []) => {
    if (!obj || typeof obj !== 'object') return results;
    
    // Search in object properties
    if (!Array.isArray(obj)) {
      for (const key in obj) {
        const value = obj[key];
        const currentPath = path ? `${path}.${key}` : key;
        
        // Check if key matches
        if (key.toLowerCase().includes(term)) {
          results.push({ path: currentPath, value });
        }
        
        // Check if value matches (if it's a primitive)
        if (typeof value === 'string' && value.toLowerCase().includes(term)) {
          results.push({ path: currentPath, value });
        } else if (typeof value === 'number' && String(value).includes(term)) {
          results.push({ path: currentPath, value });
        }
        
        // Recursively search in nested objects
        if (value && typeof value === 'object') {
          searchInObject(value, term, currentPath, results);
        }
      }
    } 
    // Search in arrays
    else {
      for (let i = 0; i < obj.length; i++) {
        const value = obj[i];
        const currentPath = `${path}[${i}]`;
        
        // Check if value matches (if it's a primitive)
        if (typeof value === 'string' && value.toLowerCase().includes(term)) {
          results.push({ path: currentPath, value });
        } else if (typeof value === 'number' && String(value).includes(term)) {
          results.push({ path: currentPath, value });
        }
        
        // Recursively search in nested objects
        if (value && typeof value === 'object') {
          searchInObject(value, term, currentPath, results);
        }
      }
    }
    
    return results;
  };

  // Get a value from a path
  const getValueAtPath = (obj, path) => {
    const parts = path.split('.');
    let current = obj;
    
    for (const part of parts) {
      if (part.includes('[')) {
        const key = part.substring(0, part.indexOf('['));
        const indexStr = part.substring(part.indexOf('[') + 1, part.indexOf(']'));
        const index = parseInt(indexStr, 10);
        
        if (!current[key] || !Array.isArray(current[key])) return undefined;
        current = current[key][index];
      } else {
        if (current === undefined || current === null) return undefined;
        current = current[part];
      }
    }
    
    return current;
  };

  // Format a value for display
  const formatValue = (value) => {
    if (value === null) return 'null';
    if (value === undefined) return 'undefined';
    
    const type = typeof value;
    
    if (type === 'object') {
      if (Array.isArray(value)) {
        if (value.length === 0) return '[]';
        return `[Array with ${value.length} items]`;
      }
      return `{Object with ${Object.keys(value).length} properties}`;
    }
    
    if (type === 'string') {
      if (value.length > 100) {
        return `"${value.substring(0, 100)}..."`;
      }
      return `"${value}"`;
    }
    
    return String(value);
  };

  // Format a value as JSON (for node details)
  const formatJson = (value) => {
    if (value === null) return 'null';
    if (value === undefined) return 'undefined';
    
    try {
      return JSON.stringify(value, null, 2);
    } catch (e) {
      return String(value);
    }
  };

  // Handle search input
  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
  };

  // Navigate to a node in the tree
  const navigateToNode = (path) => {
    // This is a placeholder - in a real implementation, 
    // we would highlight or expand to the node in the tree
    alert(`Navigation to path "${path}" is not yet implemented.`);
  };

  return (
    <div className="structure-explorer">
      <h2 className="page-title mb-4">Structure Explorer</h2>
      
      <div className="row">
        {/* Left column - Tree visualization */}
        <div className="col-md-8">
          <div className="card">
            <div className="card-body">
              <div className="d-flex justify-content-between align-items-center mb-3">
                <h5 className="card-title mb-0">Project Structure</h5>
                
                {/* Search input */}
                <div className="search-container">
                  <div className="input-group">
                    <input
                      type="text"
                      className="form-control form-control-sm"
                      placeholder="Search in project..."
                      value={searchTerm}
                      onChange={handleSearchChange}
                    />
                    <span className="input-group-text">
                      <i className="fas fa-search"></i>
                    </span>
                  </div>
                </div>
              </div>
              
              {/* Tree visualization */}
              <div className="tree-container" ref={treeContainerRef}></div>
              
              {/* Search results */}
              {searchTerm && searchResults.length > 0 && (
                <div className="search-results mt-3">
                  <h6>Search Results ({searchResults.length})</h6>
                  
                  <div className="search-results-list">
                    {searchResults.slice(0, 20).map((result, index) => (
                      <div key={index} className="search-result-item">
                        <div 
                          className="search-result-path"
                          onClick={() => navigateToNode(result.path)}
                        >
                          {result.path}
                        </div>
                        <div className="search-result-value">
                          {formatValue(result.value)}
                        </div>
                      </div>
                    ))}
                    
                    {searchResults.length > 20 && (
                      <div className="text-muted text-center mt-2">
                        Showing 20 of {searchResults.length} results
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
        
        {/* Right column - Node details */}
        <div className="col-md-4">
          <div className="card">
            <div className="card-body">
              <h5 className="card-title">Node Details</h5>
              
              {selectedNode ? (
                <div className="node-details">
                  <h6>{selectedNode.data.name}</h6>
                  
                  <div className="details-row">
                    <div className="details-label">Type:</div>
                    <div className="details-value text-capitalize">{selectedNode.data.type}</div>
                  </div>
                  
                  {selectedNode.data.size && (
                    <div className="details-row">
                      <div className="details-label">Size:</div>
                      <div className="details-value">{selectedNode.data.size}</div>
                    </div>
                  )}
                  
                  {/* Path to this node */}
                  <div className="details-row">
                    <div className="details-label">Path:</div>
                    <div className="details-value">
                      <code>{getNodePath(selectedNode)}</code>
                    </div>
                  </div>
                  
                  {/* Value preview */}
                  <div className="mt-4">
                    <h6>Value Preview</h6>
                    
                    <div className="value-preview">
                      {(() => {
                        const path = getNodePath(selectedNode);
                        if (!path) return <div className="text-muted">Root node</div>;
                        
                        const value = getValueAtPath(projectData, path);
                        if (value === undefined) return <div className="text-muted">Unable to resolve path</div>;
                        
                        return (
                          <pre className="json-preview">
                            {formatJson(value)}
                          </pre>
                        );
                      })()}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center text-muted py-5">
                  <i className="fas fa-sitemap fa-3x mb-3"></i>
                  <p>Select a node in the tree to view details</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Get path to a node
const getNodePath = (node) => {
  if (!node || !node.parent) return '';
  
  const path = [];
  let current = node;
  
  while (current.parent) {
    path.unshift(current.data.name);
    current = current.parent;
  }
  
  return path.join('.');
};

export default StructureExplorer;