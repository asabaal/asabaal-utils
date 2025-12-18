        // Physics parameters
        let physicsParams = {
            k_spring: 10.0,
            k_repel: 0.1,
            k_barrier: 1.0,
            L0: 1.0
        };
        
        // Network instance
        let network = null;
        let nodes = null;
        let edges = null;
        
        // Text measurement canvas
        let textMeasurementCanvas = null;
        let textMeasurementContext = null;
        
        // Scenario definitions
        const scenarios = {
            '2_node_attraction': {
                nodes: [
                    {id: 'a', label: 'A', x: -200, y: 0, shape: 'box', color: '#ff6b6b'},
                    {id: 'b', label: 'B', x: 200, y: 0, shape: 'box', color: '#4ecdc4'}
                ],
                edges: [
                    {from: 'a', to: 'b'}
                ],
                params: {k_spring: 10.0, k_repel: 0.1, k_barrier: 1.0, L0: 1.0}
            },
            '2_node_repulsion': {
                nodes: [
                    {id: 'a', label: 'A', x: -50, y: 0, shape: 'box', color: '#ff6b6b'},
                    {id: 'b', label: 'B', x: 50, y: 0, shape: 'box', color: '#4ecdc4'}
                ],
                edges: [
                    {from: 'a', to: 'b'}
                ],
                params: {k_spring: 0.1, k_repel: 10.0, k_barrier: 1.0, L0: 1.0}
            },
            '2_node_equilibrium': {
                nodes: [
                    {id: 'a', label: 'A', x: -100, y: 0, shape: 'box', color: '#ff6b6b'},
                    {id: 'b', label: 'B', x: 100, y: 0, shape: 'box', color: '#4ecdc4'}
                ],
                edges: [
                    {from: 'a', to: 'b'}
                ],
                params: {k_spring: 2.0, k_repel: 2.0, k_barrier: 1.0, L0: 1.0}
            },
            '3_node_triangle': {
                nodes: [
                    {id: 'a', label: 'A', x: 0, y: -150, shape: 'box', color: '#ff6b6b'},
                    {id: 'b', label: 'B', x: -130, y: 75, shape: 'box', color: '#4ecdc4'},
                    {id: 'c', label: 'C', x: 130, y: 75, shape: 'box', color: '#45b7d1'}
                ],
                edges: [
                    {from: 'a', to: 'b'},
                    {from: 'b', to: 'c'},
                    {from: 'c', to: 'a'}
                ],
                params: {k_spring: 10.0, k_repel: 0.1, k_barrier: 1.0, L0: 1.0}
            },
            '3_node_chain': {
                nodes: [
                    {id: 'a', label: 'A', x: -200, y: 0, shape: 'box', color: '#ff6b6b'},
                    {id: 'b', label: 'B', x: 0, y: 0, shape: 'box', color: '#4ecdc4'},
                    {id: 'c', label: 'C', x: 200, y: 0, shape: 'box', color: '#45b7d1'}
                ],
                edges: [
                    {from: 'a', to: 'b'},
                    {from: 'b', to: 'c'}
                ],
                params: {k_spring: 5.0, k_repel: 1.0, k_barrier: 1.0, L0: 1.0}
            },
            '3_node_edge_barrier': {
                nodes: [
                    {id: 'a', label: 'A', x: -100, y: -50, shape: 'box', color: '#ff6b6b'},
                    {id: 'b', label: 'B', x: 100, y: -50, shape: 'box', color: '#4ecdc4'},
                    {id: 'c', label: 'C', x: 0, y: 100, shape: 'box', color: '#45b7d1'}
                ],
                edges: [
                    {from: 'a', to: 'b'}
                ],
                params: {k_spring: 5.0, k_repel: 1.0, k_barrier: 10.0, L0: 1.0}
            },
            'test_long_labels': {
                nodes: [
                    {id: 'a', label: 'Short', x: -150, y: 0, shape: 'box', color: '#ff6b6b'},
                    {id: 'b', label: 'Medium Length Label', x: 150, y: 0, shape: 'box', color: '#4ecdc4'},
                    {id: 'c', label: 'Very Long Label Text Here', x: 0, y: 150, shape: 'box', color: '#45b7d1'}
                ],
                edges: [
                    {from: 'a', to: 'b'},
                    {from: 'b', to: 'c'}
                ],
                params: {k_spring: 2.0, k_repel: 1.0, k_barrier: 1.0, L0: 1.0}
            }
        };
        
        // Store node sizes for physics calculations
        let nodeSizes = {};
        
        // Initialize text measurement
        function initTextMeasurement() {
            textMeasurementCanvas = document.createElement('canvas');
            textMeasurementContext = textMeasurementCanvas.getContext('2d');
        }
        
        // Measure text dimensions
        function measureText(text, font = '14px Arial') {
            textMeasurementContext.font = font;
            const metrics = textMeasurementContext.measureText(text);
            return {
                width: metrics.width,
                height: parseInt(font.match(/\d+/)[0]) * 1.2  // Approximate line height
            };
        }
        
        // Calculate node size based on label
        function calculateNodeSize(label, fontSize = 14, padding = 20) {
            const font = `${fontSize}px Arial`;
            const textDimensions = measureText(label, font);
            
            return {
                width: textDimensions.width + padding * 2,
                height: textDimensions.height + padding * 2,
                textWidth: textDimensions.width,
                textHeight: textDimensions.height,
                padding: padding
            };
        }
        
        // Initialize network
        function initNetwork() {
            const container = document.getElementById('network');
            
            // Initialize text measurement first
            initTextMeasurement();
            
            const data = {
                nodes: new vis.DataSet([]),
                edges: new vis.DataSet([])
            };
            
            const options = {
                physics: {
                    enabled: false  // Disable physics, we'll handle manually
                },
                interaction: {
                    dragNodes: true,
                    dragView: true,
                    zoomView: true
                },
                nodes: {
                    shape: 'box',
                    margin: 10,
                    font: {
                        size: 14,
                        color: '#333'
                    },
                    borderWidth: 2,
                    borderWidthSelected: 3
                },
                edges: {
                    width: 2,
                    color: { color: '#666' },
                    smooth: {
                        type: 'continuous'
                    }
                }
            };
            
            network = new vis.Network(container, data, options);
            
            // Add event listener for node dragging
            network.on("dragging", function(params) {
                if (params.nodes.length > 0) {
                    updatePhysics();
                }
            });
            
            network.on("dragEnd", function(params) {
                if (params.nodes.length > 0) {
                    updatePhysics();
                }
            });
        }
        
        // Load scenario
        function loadScenario() {
            const scenarioName = document.getElementById('scenarioSelect').value;
            const scenario = scenarios[scenarioName];
            
            if (!scenario) return;
            
            // Update physics parameters
            physicsParams = {...physicsParams, ...scenario.params};
            updateParameterDisplays();
            
            // Calculate node sizes based on labels
            nodeSizes = {};
            const nodesWithSizes = scenario.nodes.map(node => {
                const size = calculateNodeSize(node.label, 14, 20);
                nodeSizes[node.id] = size;
                return {
                    ...node,
                    size: Math.max(size.width, size.height)  // Use larger dimension for vis.js
                };
            });
            
            // Update network
            nodes = new vis.DataSet(nodesWithSizes);
            edges = new vis.DataSet(scenario.edges);
            network.setData({nodes: nodes, edges: edges});
            
            // Update physics calculations with small delay to ensure network is ready
            setTimeout(() => {
                updatePhysics();
            }, 100);
        }
        
        // Update parameter displays
        function updateParameterDisplays() {
            document.getElementById('kSpring').value = physicsParams.k_spring;
            document.getElementById('kSpringValue').textContent = physicsParams.k_spring.toFixed(1);
            document.getElementById('kRepel').value = physicsParams.k_repel;
            document.getElementById('kRepelValue').textContent = physicsParams.k_repel.toFixed(2);
            document.getElementById('kBarrier').value = physicsParams.k_barrier;
            document.getElementById('kBarrierValue').textContent = physicsParams.k_barrier.toFixed(1);
            document.getElementById('L0').value = physicsParams.L0;
            document.getElementById('L0Value').textContent = physicsParams.L0.toFixed(1);
        }
        
        // Update physics from controls
        function updatePhysics() {
            // Get current parameter values
            physicsParams.k_spring = parseFloat(document.getElementById('kSpring').value);
            physicsParams.k_repel = parseFloat(document.getElementById('kRepel').value);
            physicsParams.k_barrier = parseFloat(document.getElementById('kBarrier').value);
            physicsParams.L0 = parseFloat(document.getElementById('L0').value);
            
            // Update displays
            updateParameterDisplays();
            
            // Calculate and display physics
            calculateAndDisplayPhysics();
        }
        
        // Calculate and display physics
        function calculateAndDisplayPhysics() {
            const nodePositions = network.getPositions();
            const edgeList = edges.get();
            
            // Calculate energies and forces
            const energy = calculateSystemEnergy(nodePositions, edgeList);
            const nodeForces = calculateNodeForces(nodePositions, edgeList);
            const edgeForces = calculateEdgeForces(nodePositions, edgeList);
            
            // Update displays
            updateEnergyDisplay(energy);
            updateNodeDisplay(nodePositions, nodeForces);
            updateNodeForcesDisplay(nodeForces);
            updateEdgeInfoDisplay(nodePositions, edgeList);
            updateEdgeForcesDisplay(edgeForces);
        }
        
        // Calculate physics and update display
        function calculateAndDisplayPhysics() {
            const nodePositions = network.getPositions();
            const edgeList = edges.get();
            
            // Calculate energies and forces
            const energy = calculateSystemEnergy(nodePositions, edgeList);
            const nodeForces = calculateNodeForces(nodePositions, edgeList);
            const edgeForces = calculateEdgeForces(nodePositions, edgeList);
            
            // Update displays
            updateEnergyDisplay(energy);
            updateNodeDisplay(nodePositions, nodeForces);
            updateNodeForcesDisplay(nodeForces);
            updateEdgeForcesDisplay(edgeForces);
        }
        
        // Calculate system energy
        function calculateSystemEnergy(positions, edgeList) {
            let springEnergy = 0;
            let repulsionEnergy = 0;
            let barrierEnergy = 0;
            
            const nodeList = Object.keys(positions);
            
            // Spring energy (for connected nodes)
            edgeList.forEach(edge => {
                const pos1 = positions[edge.from];
                const pos2 = positions[edge.to];
                const distance = Math.sqrt(Math.pow(pos2.x - pos1.x, 2) + Math.pow(pos2.y - pos1.y, 2));
                const stretch = distance - physicsParams.L0;
                springEnergy += 0.5 * physicsParams.k_spring * stretch * stretch;
            });
            
            // Repulsion energy (between all node pairs)
            for (let i = 0; i < nodeList.length; i++) {
                for (let j = i + 1; j < nodeList.length; j++) {
                    const pos1 = positions[nodeList[i]];
                    const pos2 = positions[nodeList[j]];
                    const distance = Math.sqrt(Math.pow(pos2.x - pos1.x, 2) + Math.pow(pos2.y - pos1.y, 2));
                    if (distance > 0) {
                        repulsionEnergy += physicsParams.k_repel / distance;
                    }
                }
            }
            
            // Barrier energy (for non-incident nodes near edges)
            nodeList.forEach(nodeId => {
                edgeList.forEach(edge => {
                    if (edge.from !== nodeId && edge.to !== nodeId) {
                        const pos = positions[nodeId];
                        const pos1 = positions[edge.from];
                        const pos2 = positions[edge.to];
                        const distance = pointToLineDistance(pos, pos1, pos2);
                        if (distance > 0 && distance < 2.0) {
                            barrierEnergy += physicsParams.k_barrier * Math.exp(-distance);
                        }
                    }
                });
            });
            
            return {
                spring: springEnergy,
                repulsion: repulsionEnergy,
                barrier: barrierEnergy,
                total: springEnergy + repulsionEnergy + barrierEnergy
            };
        }
        
        // Calculate forces on each node with size-aware physics
        function calculateNodeForces(positions, edgeList) {
            const forces = {};
            const nodeList = Object.keys(positions);
            
            // Initialize forces
            nodeList.forEach(nodeId => {
                forces[nodeId] = {x: 0, y: 0, spring: {x: 0, y: 0}, repulsion: {x: 0, y: 0}, barrier: {x: 0, y: 0}};
            });
            
            // Spring forces (for connected nodes)
            edgeList.forEach(edge => {
                const pos1 = positions[edge.from];
                const pos2 = positions[edge.to];
                const dx = pos2.x - pos1.x;
                const dy = pos2.y - pos1.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance > 0) {
                    const force = physicsParams.k_spring * (distance - physicsParams.L0);
                    const fx = force * dx / distance;
                    const fy = force * dy / distance;
                    
                    forces[edge.from].spring.x += fx;
                    forces[edge.from].spring.y += fy;
                    forces[edge.to].spring.x -= fx;
                    forces[edge.to].spring.y -= fy;
                }
            });
            
            // Size-aware repulsion forces (between all node pairs)
            for (let i = 0; i < nodeList.length; i++) {
                for (let j = i + 1; j < nodeList.length; j++) {
                    const nodeId1 = nodeList[i];
                    const nodeId2 = nodeList[j];
                    const pos1 = positions[nodeId1];
                    const pos2 = positions[nodeId2];
                    const size1 = nodeSizes[nodeId1];
                    const size2 = nodeSizes[nodeId2];
                    
                    // Calculate distance between node edges, not centers
                    const dx = pos2.x - pos1.x;
                    const dy = pos2.y - pos1.y;
                    const centerDistance = Math.sqrt(dx * dx + dy * dy);
                    
                    // Minimum distance to prevent overlap based on node sizes
                    const minDistance = (Math.max(size1.width, size1.height) + Math.max(size2.width, size2.height)) / 2;
                    const effectiveDistance = Math.max(centerDistance - minDistance, 0.1);
                    
                    if (effectiveDistance > 0) {
                        const force = physicsParams.k_repel / (effectiveDistance * effectiveDistance);
                        const fx = force * dx / centerDistance;
                        const fy = force * dy / centerDistance;
                        
                        forces[nodeId1].repulsion.x -= fx;
                        forces[nodeId1].repulsion.y -= fy;
                        forces[nodeId2].repulsion.x += fx;
                        forces[nodeId2].repulsion.y += fy;
                    }
                }
            }
            
            // Size-aware barrier forces (for non-incident nodes near edges)
            nodeList.forEach(nodeId => {
                edgeList.forEach(edge => {
                    if (edge.from !== nodeId && edge.to !== nodeId) {
                        const pos = positions[nodeId];
                        const nodeSize = nodeSizes[nodeId];
                        const pos1 = positions[edge.from];
                        const pos2 = positions[edge.to];
                        
                        // Calculate distance from node edge to line segment
                        const closestPoint = closestPointOnLine(pos, pos1, pos2);
                        const dx = pos.x - closestPoint.x;
                        const dy = pos.y - closestPoint.y;
                        const centerDistance = Math.sqrt(dx * dx + dy * dy);
                        
                        // Account for node size in barrier distance calculation
                        const nodeRadius = Math.max(nodeSize.width, nodeSize.height) / 2;
                        const effectiveDistance = Math.max(centerDistance - nodeRadius, 0.1);
                        
                        if (effectiveDistance < 2.0) {
                            const force = physicsParams.k_barrier * Math.exp(-effectiveDistance);
                            const fx = force * dx / centerDistance;
                            const fy = force * dy / centerDistance;
                            
                            forces[nodeId].barrier.x += fx;
                            forces[nodeId].barrier.y += fy;
                        }
                    }
                });
            });
            
            // Calculate total forces
            nodeList.forEach(nodeId => {
                forces[nodeId].x = forces[nodeId].spring.x + forces[nodeId].repulsion.x + forces[nodeId].barrier.x;
                forces[nodeId].y = forces[nodeId].spring.y + forces[nodeId].repulsion.y + forces[nodeId].barrier.y;
            });
            
            return forces;
        }
        
        // Calculate edge forces
        function calculateEdgeForces(positions, edgeList) {
            const edgeForces = [];
            
            edgeList.forEach(edge => {
                const pos1 = positions[edge.from];
                const pos2 = positions[edge.to];
                const dx = pos2.x - pos1.x;
                const dy = pos2.y - pos1.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                const springForce = physicsParams.k_spring * (distance - physicsParams.L0);
                
                edgeForces.push({
                    edge: `${edge.from}-${edge.to}`,
                    distance: distance,
                    restLength: physicsParams.L0,
                    springForce: springForce,
                    direction: {x: dx/distance, y: dy/distance}
                });
            });
            
            return edgeForces;
        }
        
        // Helper functions
        function pointToLineDistance(point, lineStart, lineEnd) {
            const A = point.x - lineStart.x;
            const B = point.y - lineStart.y;
            const C = lineEnd.x - lineStart.x;
            const D = lineEnd.y - lineStart.y;
            
            const dot = A * C + B * D;
            const lenSq = C * C + D * D;
            let param = -1;
            
            if (lenSq !== 0) param = dot / lenSq;
            
            let xx, yy;
            
            if (param < 0) {
                xx = lineStart.x;
                yy = lineStart.y;
            } else if (param > 1) {
                xx = lineEnd.x;
                yy = lineEnd.y;
            } else {
                xx = lineStart.x + param * C;
                yy = lineStart.y + param * D;
            }
            
            const dx = point.x - xx;
            const dy = point.y - yy;
            
            return Math.sqrt(dx * dx + dy * dy);
        }
        
        function closestPointOnLine(point, lineStart, lineEnd) {
            const A = point.x - lineStart.x;
            const B = point.y - lineStart.y;
            const C = lineEnd.x - lineStart.x;
            const D = lineEnd.y - lineStart.y;
            
            const dot = A * C + B * D;
            const lenSq = C * C + D * D;
            let param = -1;
            
            if (lenSq !== 0) param = dot / lenSq;
            
            if (param < 0) {
                return {x: lineStart.x, y: lineStart.y};
            } else if (param > 1) {
                return {x: lineEnd.x, y: lineEnd.y};
            } else {
                return {
                    x: lineStart.x + param * C,
                    y: lineStart.y + param * D
                };
            }
        }
        
        // Update display functions
        function updateEnergyDisplay(energy) {
            document.getElementById('springEnergy').textContent = energy.spring.toFixed(3);
            document.getElementById('repulsionEnergy').textContent = energy.repulsion.toFixed(3);
            document.getElementById('barrierEnergy').textContent = energy.barrier.toFixed(3);
            document.getElementById('totalEnergy').textContent = energy.total.toFixed(3);
        }
        
        function updateNodeDisplay(positions, forces) {
            const container = document.getElementById('nodeInfoContainer');
            container.innerHTML = '';
            
            Object.keys(positions).forEach(nodeId => {
                const pos = positions[nodeId];
                const force = forces[nodeId];
                const forceMag = Math.sqrt(force.x * force.x + force.y * force.y);
                const nodeSize = nodeSizes[nodeId];
                
                const nodeDiv = document.createElement('div');
                nodeDiv.className = 'node-info';
                nodeDiv.innerHTML = `
                    <div class="node-name">Node ${nodeId.toUpperCase()}</div>
                    <div class="node-detail">
                        <span>Position:</span>
                        <span class="force-value">(${pos.x.toFixed(1)}, ${pos.y.toFixed(1)})</span>
                    </div>
                    <div class="node-detail">
                        <span>Node Size:</span>
                        <span class="force-value">${nodeSize.width.toFixed(0)}×${nodeSize.height.toFixed(0)}</span>
                    </div>
                    <div class="node-detail">
                        <span>Text Width:</span>
                        <span class="force-value">${nodeSize.textWidth.toFixed(0)}px</span>
                    </div>
                    <div class="node-detail">
                        <span>Total Force:</span>
                        <span class="force-value">${forceMag.toFixed(3)}</span>
                    </div>
                    <div class="node-detail">
                        <span>Force Vector:</span>
                        <span class="force-vector">(${force.x.toFixed(3)}, ${force.y.toFixed(3)})</span>
                    </div>
                `;
                container.appendChild(nodeDiv);
            });
        }
        
        function updateNodeForcesDisplay(forces) {
            const container = document.getElementById('nodeForcesContainer');
            container.innerHTML = '';
            
            Object.keys(forces).forEach(nodeId => {
                const force = forces[nodeId];
                const springMag = Math.sqrt(force.spring.x * force.spring.x + force.spring.y * force.spring.y);
                const repulsionMag = Math.sqrt(force.repulsion.x * force.repulsion.x + force.repulsion.y * force.repulsion.y);
                const barrierMag = Math.sqrt(force.barrier.x * force.barrier.x + force.barrier.y * force.barrier.y);
                
                const forceDiv = document.createElement('div');
                forceDiv.innerHTML = `
                    <div class="force-item">
                        <span class="force-name">${nodeId.toUpperCase()} Spring:</span>
                        <span class="force-value">${springMag.toFixed(3)}</span>
                        <span class="force-vector">(${force.spring.x.toFixed(3)}, ${force.spring.y.toFixed(3)})</span>
                    </div>
                    <div class="force-item">
                        <span class="force-name">${nodeId.toUpperCase()} Repulsion:</span>
                        <span class="force-value">${repulsionMag.toFixed(3)}</span>
                        <span class="force-vector">(${force.repulsion.x.toFixed(3)}, ${force.repulsion.y.toFixed(3)})</span>
                    </div>
                    <div class="force-item">
                        <span class="force-name">${nodeId.toUpperCase()} Barrier:</span>
                        <span class="force-value">${barrierMag.toFixed(3)}</span>
                        <span class="force-vector">(${force.barrier.x.toFixed(3)}, ${force.barrier.y.toFixed(3)})</span>
                    </div>
                    <hr style="margin: 10px 0; border: 1px solid #eee;">
                `;
                container.appendChild(forceDiv);
            });
        }
        
        function updateEdgeForcesDisplay(edgeForces) {
            const edgeForcesContainer = document.getElementById('edgeForcesContainer');
            edgeForcesContainer.innerHTML = '';
            
            edgeForces.forEach(edgeForce => {
                const edgeDiv = document.createElement('div');
                edgeDiv.innerHTML = `
                    <div class="force-item">
                        <span class="force-name">Edge ${edgeForce.edge}:</span>
                        <span class="force-value">${Math.abs(edgeForce.springForce).toFixed(3)}</span>
                    </div>
                    <div class="force-item">
                        <span class="force-name">Distance:</span>
                        <span class="force-value">${edgeForce.distance.toFixed(3)}</span>
                    </div>
                    <div class="force-item">
                        <span class="force-name">Rest Length:</span>
                        <span class="force-value">${edgeForce.restLength.toFixed(3)}</span>
                    </div>
                    <div class="force-item">
                        <span class="force-name">Direction:</span>
                        <span class="force-vector">(${edgeForce.direction.x.toFixed(3)}, ${edgeForce.direction.y.toFixed(3)})</span>
                    </div>
                    <hr style="margin: 10px 0; border: 1px solid #eee;">
                `;
                edgeForcesContainer.appendChild(edgeDiv);
            });
        }
        
        function updateEdgeInfoDisplay(positions, edgeList) {
            const container = document.getElementById('edgeInfoContainer');
            container.innerHTML = '';
            
            if (!edgeList || edgeList.length === 0) {
                container.innerHTML = '<div class="force-item"><span class="force-name">No edges found</span></div>';
                return;
            }
            
            edgeList.forEach(edge => {
                const pos1 = positions[edge.from];
                const pos2 = positions[edge.to];
                const dx = pos2.x - pos1.x;
                const dy = pos2.y - pos1.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                const angle = Math.atan2(dy, dx) * (180 / Math.PI);
                
                // Calculate edge properties
                const stretch = distance - physicsParams.L0;
                const stretchPercent = (stretch / physicsParams.L0) * 100;
                const springForce = physicsParams.k_spring * stretch;
                
                // Calculate edge midpoint
                const midpoint = {
                    x: (pos1.x + pos2.x) / 2,
                    y: (pos1.y + pos2.y) / 2
                };
                
                const edgeDiv = document.createElement('div');
                edgeDiv.className = 'node-info';
                edgeDiv.innerHTML = `
                    <div class="node-name">Edge ${edge.from.toUpperCase()}-${edge.to.toUpperCase()}</div>
                    <div class="node-detail">
                        <span>Start Node:</span>
                        <span class="force-value">${edge.from.toUpperCase()}</span>
                    </div>
                    <div class="node-detail">
                        <span>End Node:</span>
                        <span class="force-value">${edge.to.toUpperCase()}</span>
                    </div>
                    <div class="node-detail">
                        <span>Length:</span>
                        <span class="force-value">${distance.toFixed(3)}</span>
                    </div>
                    <div class="node-detail">
                        <span>Rest Length:</span>
                        <span class="force-value">${physicsParams.L0.toFixed(3)}</span>
                    </div>
                    <div class="node-detail">
                        <span>Stretch:</span>
                        <span class="force-value">${stretch.toFixed(3)} (${stretchPercent.toFixed(1)}%)</span>
                    </div>
                    <div class="node-detail">
                        <span>Spring Force:</span>
                        <span class="force-value">${springForce.toFixed(3)}</span>
                    </div>
                    <div class="node-detail">
                        <span>Angle:</span>
                        <span class="force-value">${angle.toFixed(1)}°</span>
                    </div>
                    <div class="node-detail">
                        <span>Midpoint:</span>
                        <span class="force-vector">(${midpoint.x.toFixed(1)}, ${midpoint.y.toFixed(1)})</span>
                    </div>
                    <div class="node-detail">
                        <span>Direction:</span>
                        <span class="force-vector">(${(dx/distance).toFixed(3)}, ${(dy/distance).toFixed(3)})</span>
                    </div>
                `;
                container.appendChild(edgeDiv);
            });
        }
        
        // Initialize on load
        window.onload = function() {
            initNetwork();
            loadScenario();
        };
