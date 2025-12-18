        // Physics parameters
        let physicsParams = {
            k_spring: 10.0,
            k_repel: 0.1,
            k_barrier: 1.0,
            L0: 1.0,
            use_surface_anchors: true  // Surface anchors always active
        };
        
        // Network instance
        let network = null;
        let nodes = null;
        let edges = null;
        
        // Text measurement canvas
        let textMeasurementCanvas = null;
        let textMeasurementContext = null;
        
        // Surface anchor system functions
        function surfacePointToward(node, targetX, targetY) {
            const dx = targetX - node.x;
            const dy = targetY - node.y;
            const angle = Math.atan2(dy, dx);
            
            switch (node.shape) {
                case 'box':
                    return surfacePointBox(node, angle);
                case 'circle':
                    return surfacePointCircle(node, angle);
                case 'ellipse':
                    return surfacePointEllipse(node, angle);
                case 'diamond':
                    return surfacePointDiamond(node, angle);
                default:
                    return {x: node.x, y: node.y};
            }
        }
        
        function surfacePointBox(node, angle) {
            const halfWidth = node.size.width / 2;
            const halfHeight = node.size.height / 2;
            
            // Calculate intersection with box edges
            const tanAngle = Math.tan(angle);
            let x, y;
            
            if (Math.abs(tanAngle) <= halfHeight / halfWidth) {
                // Intersects with left or right edge
                x = Math.cos(angle) > 0 ? halfWidth : -halfWidth;
                y = x * tanAngle;
            } else {
                // Intersects with top or bottom edge
                y = Math.sin(angle) > 0 ? halfHeight : -halfHeight;
                x = y / tanAngle;
            }
            
            return {
                x: node.x + x,
                y: node.y + y
            };
        }
        
        function surfacePointCircle(node, angle) {
            const radius = node.size.width / 2; // Assuming circular
            return {
                x: node.x + radius * Math.cos(angle),
                y: node.y + radius * Math.sin(angle)
            };
        }
        
        function surfacePointEllipse(node, angle) {
            const a = node.size.width / 2;  // Semi-major axis
            const b = node.size.height / 2; // Semi-minor axis
            
            // Parametric equation for ellipse surface point
            const cosAngle = Math.cos(angle);
            const sinAngle = Math.sin(angle);
            
            // Calculate surface point using ellipse parametric form
            const denominator = Math.sqrt((b * cosAngle) ** 2 + (a * sinAngle) ** 2);
            const t = a * b / denominator;
            
            return {
                x: node.x + t * cosAngle,
                y: node.y + t * sinAngle
            };
        }
        
        function surfacePointDiamond(node, angle) {
            const halfWidth = node.size.width / 2;
            const halfHeight = node.size.height / 2;
            
            // Normalize angle to [0, 2π]
            let normalizedAngle = ((angle % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI);
            
            // Diamond has 4 edges, each spanning π/2 radians
            const edgeIndex = Math.floor(normalizedAngle / (Math.PI / 2));
            const edgeAngle = normalizedAngle - edgeIndex * (Math.PI / 2);
            
            let x, y;
            
            switch (edgeIndex) {
                case 0: // Right edge
                    x = halfWidth * (1 - edgeAngle / (Math.PI / 2));
                    y = halfHeight * (2 * edgeAngle / (Math.PI / 2) - 1);
                    break;
                case 1: // Bottom edge
                    x = halfWidth * (1 - 2 * edgeAngle / (Math.PI / 2));
                    y = halfHeight * (1 - edgeAngle / (Math.PI / 2));
                    break;
                case 2: // Left edge
                    x = -halfWidth * (edgeAngle / (Math.PI / 2));
                    y = halfHeight * (1 - 2 * edgeAngle / (Math.PI / 2));
                    break;
                case 3: // Top edge
                    x = -halfWidth * (1 - edgeAngle / (Math.PI / 2));
                    y = -halfHeight * (2 * edgeAngle / (Math.PI / 2) - 1);
                    break;
            }
            
            return {
                x: node.x + x,
                y: node.y + y
            };
        }
        
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
                params: {k_spring: 5.0, k_repel: 1.0, k_barrier: 1.0, L0: 1.0}
            },
            'mixed_shapes': {
                nodes: [
                    {id: 'a', label: 'Box', x: -150, y: 0, shape: 'box', color: '#ff6b6b'},
                    {id: 'b', label: 'Circle', x: 0, y: 0, shape: 'circle', color: '#4ecdc4'},
                    {id: 'c', label: 'Diamond', x: 150, y: 0, shape: 'diamond', color: '#45b7d1'},
                    {id: 'd', label: 'Ellipse', x: 75, y: 100, shape: 'ellipse', color: '#f39c12'}
                ],
                edges: [
                    {from: 'a', to: 'b'},
                    {from: 'b', to: 'c'},
                    {from: 'c', to: 'd'},
                    {from: 'd', to: 'a'}
                ],
                params: {k_spring: 5.0, k_repel: 2.0, k_barrier: 1.0, L0: 1.0}
            },
            'surface_anchor_test': {
                nodes: [
                    {id: 'entry', label: 'Entry', x: -200, y: 0, shape: 'ellipse', color: '#90ee90'},
                    {id: 'process', label: 'Process', x: -100, y: 0, shape: 'box', color: '#ffd700'},
                    {id: 'decision', label: 'Decision', x: 0, y: 0, shape: 'diamond', color: '#ffa500'},
                    {id: 'output', label: 'Output', x: 100, y: 0, shape: 'ellipse', color: '#87ceeb'},
                    {id: 'exit', label: 'Exit', x: 200, y: 0, shape: 'ellipse', color: '#ff6b6b'}
                ],
                edges: [
                    {from: 'entry', to: 'process'},
                    {from: 'process', to: 'decision'},
                    {from: 'decision', to: 'output'},
                    {from: 'output', to: 'exit'}
                ],
                params: {k_spring: 8.0, k_repel: 1.5, k_barrier: 2.0, L0: 1.2}
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
        
        // Overlap detection functions
        function isPointInBox(node, x, y) {
            const halfWidth = node.size / 2;
            const halfHeight = node.size / 2;
            const relX = x - node.x;
            const relY = y - node.y;
            return Math.abs(relX) <= halfWidth && Math.abs(relY) <= halfHeight;
        }
        
        function isPointInCircle(node, x, y) {
            const dx = x - node.x;
            const dy = y - node.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            const radius = node.size / 2;
            return distance <= radius;
        }
        
        function isPointInEllipse(node, x, y) {
            const dx = x - node.x;
            const dy = y - node.y;
            const a = node.size / 2;
            const b = node.size / 2;
            return (dx * dx) / (a * a) + (dy * dy) / (b * b) <= 1;
        }
        
        function isPointInDiamond(node, x, y) {
            const dx = Math.abs(x - node.x);
            const dy = Math.abs(y - node.y);
            const halfSize = node.size / 2;
            return (dx / halfSize + dy / halfSize) <= 1;
        }
        
        function isPointInShape(node, x, y) {
            switch (node.shape) {
                case 'box':
                    return isPointInBox(node, x, y);
                case 'circle':
                    return isPointInCircle(node, x, y);
                case 'ellipse':
                    return isPointInEllipse(node, x, y);
                case 'diamond':
                    return isPointInDiamond(node, x, y);
                default:
                    return isPointInBox(node, x, y);
            }
        }
        
        function calculatePenetrationDepth(node1, node2) {
            switch (node1.shape) {
                case 'box':
                    return calculateBoxPenetration(node1, node2);
                case 'circle':
                    return calculateCirclePenetration(node1, node2);
                case 'ellipse':
                    return calculateEllipsePenetration(node1, node2);
                case 'diamond':
                    return calculateDiamondPenetration(node1, node2);
                default:
                    return calculateBoxPenetration(node1, node2);
            }
        }
        
        function calculateBoxPenetration(node1, node2) {
            const halfSize1 = node1.size / 2;
            const halfSize2 = node2.size / 2;
            
            const dx = Math.abs(node2.x - node1.x);
            const dy = Math.abs(node2.y - node1.y);
            
            const overlapX = (halfSize1 + halfSize2) - dx;
            const overlapY = (halfSize1 + halfSize2) - dy;
            
            if (overlapX > 0 && overlapY > 0) {
                return -Math.min(overlapX, overlapY);
            }
            return null;
        }
        
        function calculateCirclePenetration(node1, node2) {
            const dx = node2.x - node1.x;
            const dy = node2.y - node1.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            const radius1 = node1.size / 2;
            const radius2 = node2.size / 2;
            
            if (distance < radius1 + radius2) {
                return -(radius1 + radius2 - distance);
            }
            return null;
        }
        
        function calculateEllipsePenetration(node1, node2) {
            return calculateBoxPenetration(node1, node2);
        }
        
        function calculateDiamondPenetration(node1, node2) {
            return calculateBoxPenetration(node1, node2);
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
                    smooth: false
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
        
        // Update labels in real-time
        function updateLabels() {
            const nodeALabel = document.getElementById('nodeALabel').value;
            const nodeBLabel = document.getElementById('nodeBLabel').value;
            const nodeCLabel = document.getElementById('nodeCLabel').value;
            
            // Update node labels in the dataset
            const currentNodes = nodes.get();
            const updatedNodes = currentNodes.map(node => {
                let newLabel = node.label;
                if (node.id === 'a') newLabel = nodeALabel;
                if (node.id === 'b') newLabel = nodeBLabel;
                if (node.id === 'c') newLabel = nodeCLabel;
                
                // Recalculate size based on new label
                const size = calculateNodeSize(newLabel, 14, 20);
                nodeSizes[node.id] = size;
                
                return {
                    ...node,
                    label: newLabel,
                    size: Math.max(size.width, size.height)
                };
            });
            
            // Update network
            nodes.update(updatedNodes);
            
            // Update physics calculations
            setTimeout(() => {
                updatePhysics();
            }, 50);
        }
        
        // Load scenario
        function loadScenario() {
            const scenarioName = document.getElementById('scenarioSelect').value;
            const scenario = scenarios[scenarioName];
            
            if (!scenario) return;
            
            // Update physics parameters
            physicsParams = {...physicsParams, ...scenario.params};
            updateParameterDisplays();
            
            // Update label inputs with scenario labels
            const nodeA = scenario.nodes.find(n => n.id === 'a');
            const nodeB = scenario.nodes.find(n => n.id === 'b');
            const nodeC = scenario.nodes.find(n => n.id === 'c');
            
            if (nodeA) document.getElementById('nodeALabel').value = nodeA.label;
            if (nodeB) document.getElementById('nodeBLabel').value = nodeB.label;
            if (nodeC) document.getElementById('nodeCLabel').value = nodeC ? nodeC.label : '';
            
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
            // Surface anchors are always active
            physicsParams.use_surface_anchors = true;
            
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
            updateEnergyDisplay(energy, nodePositions, edgeList);
            updateNodeDisplay(nodePositions, nodeForces);
            updateNodeForcesDisplay(nodeForces);
            updateEdgeInfoDisplay(nodePositions, edgeList);
            updateEdgeForcesDisplay(edgeForces);
            updateDistanceSummaryDisplay(nodePositions, edgeList);
        }
        

        
        // Calculate system energy
        function calculateSystemEnergy(positions, edgeList) {
            let springEnergy = 0;
            let repulsionEnergy = 0;
            let barrierEnergy = 0;
            
            const nodeList = Object.keys(positions);
            
            // Spring energy (for connected nodes) - always using surface anchors
            edgeList.forEach(edge => {
                const node1 = {x: positions[edge.from].x, y: positions[edge.from].y, shape: nodes.get(edge.from).shape, size: nodeSizes[edge.from]};
                const node2 = {x: positions[edge.to].x, y: positions[edge.to].y, shape: nodes.get(edge.to).shape, size: nodeSizes[edge.to]};
                
                // Always use surface anchor points for energy calculation
                const pos1 = surfacePointToward(node1, node2.x, node2.y);
                const pos2 = surfacePointToward(node2, node1.x, node1.y);
                
                const distance = Math.sqrt(Math.pow(pos2.x - pos1.x, 2) + Math.pow(pos2.y - pos1.y, 2));
                
                // Adjust rest length for surface anchors
                const effectiveL0 = physicsParams.L0 * 1.5;
                
                const stretch = distance - effectiveL0;
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
            
            // Spring forces (for connected nodes) - always using surface anchors
            edgeList.forEach(edge => {
                const node1 = {x: positions[edge.from].x, y: positions[edge.from].y, shape: nodes.get(edge.from).shape, size: nodeSizes[edge.from]};
                const node2 = {x: positions[edge.to].x, y: positions[edge.to].y, shape: nodes.get(edge.to).shape, size: nodeSizes[edge.to]};
                
                // Always use surface anchor points for spring forces
                const pos1 = surfacePointToward(node1, node2.x, node2.y);
                const pos2 = surfacePointToward(node2, node1.x, node1.y);
                
                const dx = pos2.x - pos1.x;
                const dy = pos2.y - pos1.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance > 0) {
                    // Adjust rest length for surface anchors
                    const effectiveL0 = physicsParams.L0 * 1.5;  // Scale up for surface anchors
                    
                    const force = physicsParams.k_spring * (distance - effectiveL0);
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
                const node1 = {x: positions[edge.from].x, y: positions[edge.from].y, shape: nodes.get(edge.from).shape, size: nodeSizes[edge.from]};
                const node2 = {x: positions[edge.to].x, y: positions[edge.to].y, shape: nodes.get(edge.to).shape, size: nodeSizes[edge.to]};
                
                let pos1, pos2;
                
                // Always use surface anchor points for edge calculations
                pos1 = surfacePointToward(node1, node2.x, node2.y);
                pos2 = surfacePointToward(node2, node1.x, node1.y);
                
                const dx = pos2.x - pos1.x;
                const dy = pos2.y - pos1.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                // Adjust rest length for surface anchors
                const effectiveL0 = physicsParams.L0 * 1.5;
                const springForce = physicsParams.k_spring * (distance - effectiveL0);
                
                edgeForces.push({
                    edge: `${edge.from}-${edge.to}`,
                    distance: distance,
                    restLength: effectiveL0,
                    springForce: springForce,
                    direction: {x: dx/distance, y: dy/distance},
                    surfacePoints: {
                        from: pos1,
                        to: pos2
                    }
                });
            });
            
            return edgeForces;
        }
        
        function updateDistanceSummaryDisplay(positions, edgeList) {
            const container = document.getElementById('distanceSummaryContainer');
            container.innerHTML = '';
            
            if (!edgeList || edgeList.length === 0) {
                container.innerHTML = '<div class="force-item"><span class="force-name">No edges found</span></div>';
                return;
            }
            
            // Calculate all edge distances
            const edgeDistances = edgeList.map(edge => {
                const node1 = {x: positions[edge.from].x, y: positions[edge.from].y, shape: nodes.get(edge.from).shape, size: nodeSizes[edge.from].width};
                const node2 = {x: positions[edge.to].x, y: positions[edge.to].y, shape: nodes.get(edge.to).shape, size: nodeSizes[edge.to].width};
                
                // Check for overlap
                const penetration1 = calculatePenetrationDepth(node1, node2);
                const penetration2 = calculatePenetrationDepth(node2, node1);
                
                let distance, isOverlapping = false;
                if (penetration1 !== null || penetration2 !== null) {
                    distance = penetration1 !== null ? penetration1 : penetration2;
                    isOverlapping = true;
                } else {
                    const surface1 = surfacePointToward(node1, node2.x, node2.y);
                    const surface2 = surfacePointToward(node2, node1.x, node1.y);
                    const dx = surface2.x - surface1.x;
                    const dy = surface2.y - surface1.y;
                    distance = Math.sqrt(dx * dx + dy * dy);
                }
                
                return {
                    edge: `${edge.from.toUpperCase()}-${edge.to.toUpperCase()}`,
                    distance: distance,
                    isOverlapping: isOverlapping,
                    centerDistance: Math.sqrt(Math.pow(node2.x - node1.x, 2) + Math.pow(node2.y - node1.y, 2))
                };
            });
            
            // Calculate summary statistics
            const totalEdges = edgeDistances.length;
            const overlappingEdges = edgeDistances.filter(e => e.isOverlapping).length;
            const avgSurfaceDistance = edgeDistances.reduce((sum, e) => sum + e.distance, 0) / totalEdges;
            const avgCenterDistance = edgeDistances.reduce((sum, e) => sum + e.centerDistance, 0) / totalEdges;
            const minSurfaceDistance = Math.min(...edgeDistances.map(e => e.distance));
            const maxSurfaceDistance = Math.max(...edgeDistances.map(e => e.distance));
            
            const summaryDiv = document.createElement('div');
            summaryDiv.innerHTML = `
                <div class="distance-highlight" style="background: ${overlappingEdges > 0 ? '#f8d7da' : '#fff3cd'}; border: 1px solid ${overlappingEdges > 0 ? '#f5c6cb' : '#ffeaa7'}; margin-bottom: 15px;">
                    <div class="distance-title" style="color: ${overlappingEdges > 0 ? '#721c24' : '#856404'};">System Distance Summary</div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px;">
                        <div style="text-align: center;">
                            <div style="font-size: 12px; color: #666;">Total Edges</div>
                            <div style="font-size: 18px; font-weight: bold; color: ${overlappingEdges > 0 ? 'red' : '#dc3545'};">${totalEdges}</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 12px; color: #666;">Overlapping</div>
                            <div style="font-size: 18px; font-weight: bold; color: ${overlappingEdges > 0 ? 'red' : '#28a745'};">${overlappingEdges}</div>
                        </div>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px;">
                        <div style="text-align: center;">
                            <div style="font-size: 12px; color: #666;">Avg Surface Distance</div>
                            <div style="font-size: 16px; font-weight: bold; color: #007bff;">${avgSurfaceDistance.toFixed(3)}</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 12px; color: #666;">Min Surface Distance</div>
                            <div style="font-size: 16px; font-weight: bold; color: ${minSurfaceDistance < 0 ? 'red' : '#28a745'};">${minSurfaceDistance.toFixed(3)}</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 12px; color: #666;">Max Surface Distance</div>
                            <div style="font-size: 16px; font-weight: bold; color: #007bff;">${maxSurfaceDistance.toFixed(3)}</div>
                        </div>
                    </div>
                    ${overlappingEdges > 0 ? '<div style="font-size: 12px; color: #721c24; text-align: center; margin-top: 10px; font-style: italic;">⚠️ System has overlapping nodes</div>' : ''}
                </div>
                
                <div style="margin-top: 15px;">
                    <div style="font-weight: bold; color: #495057; margin-bottom: 10px; border-bottom: 1px solid #dee2e6; padding-bottom: 5px;">Individual Edge Distances</div>
                    ${edgeDistances.map(edge => `
                        <div class="force-item" style="background: ${edge.isOverlapping ? '#f8d7da' : '#f8f9fa'};">
                            <span class="force-name">${edge.edge}:</span>
                            <span class="force-value" style="color: ${edge.isOverlapping ? 'red' : '#007bff'}; font-weight: bold;">${edge.distance.toFixed(3)}</span>
                            <span style="font-size: 11px; color: #666;">(center: ${edge.centerDistance.toFixed(3)})</span>
                        </div>
                    `).join('')}
                </div>
            `;
            container.appendChild(summaryDiv);
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
        function updateEnergyDisplay(energy, positions, edgeList) {
            document.getElementById('springEnergy').textContent = energy.spring.toFixed(3);
            document.getElementById('repulsionEnergy').textContent = energy.repulsion.toFixed(3);
            document.getElementById('barrierEnergy').textContent = energy.barrier.toFixed(3);
            document.getElementById('totalEnergy').textContent = energy.total.toFixed(3);
            
            // Enhanced energy display with distance correlations
            if (positions && edgeList && edgeList.length > 0) {
                const energyDetails = calculateEnergyDistanceCorrelations(positions, edgeList, energy);
                updateEnergyCorrelationDisplay(energyDetails);
            }
        }
        
        function calculateEnergyDistanceCorrelations(positions, edgeList, energy) {
            const correlations = [];
            
            edgeList.forEach(edge => {
                const node1 = {x: positions[edge.from].x, y: positions[edge.from].y, shape: nodes.get(edge.from).shape, size: nodeSizes[edge.from].width};
                const node2 = {x: positions[edge.to].x, y: positions[edge.to].y, shape: nodes.get(edge.to).shape, size: nodeSizes[edge.to].width};
                
                // Calculate surface distance
                const penetration1 = calculatePenetrationDepth(node1, node2);
                const penetration2 = calculatePenetrationDepth(node2, node1);
                
                let surfaceDistance, isOverlapping = false;
                if (penetration1 !== null || penetration2 !== null) {
                    surfaceDistance = penetration1 !== null ? penetration1 : penetration2;
                    isOverlapping = true;
                } else {
                    const surface1 = surfacePointToward(node1, node2.x, node2.y);
                    const surface2 = surfacePointToward(node2, node1.x, node1.y);
                    const dx = surface2.x - surface1.x;
                    const dy = surface2.y - surface1.y;
                    surfaceDistance = Math.sqrt(dx * dx + dy * dy);
                }
                
                // Calculate rest length and stretch/compression
                const restLength = physicsParams.L0;
                const stretchPercentage = ((surfaceDistance - restLength) / restLength) * 100;
                
                correlations.push({
                    edge: `${edge.from.toUpperCase()}-${edge.to.toUpperCase()}`,
                    surfaceDistance: surfaceDistance,
                    restLength: restLength,
                    stretchPercentage: stretchPercentage,
                    isOverlapping: isOverlapping,
                    centerDistance: Math.sqrt(Math.pow(node2.x - node1.x, 2) + Math.pow(node2.y - node1.y, 2))
                });
            });
            
            return correlations;
        }
        
        function updateEnergyCorrelationDisplay(correlations) {
            // Find or create energy correlation container
            let correlationContainer = document.getElementById('energyCorrelationContainer');
            if (!correlationContainer) {
                // Add it after the energy display
                const energyDisplay = document.querySelector('.energy-display');
                correlationContainer = document.createElement('div');
                correlationContainer.id = 'energyCorrelationContainer';
                correlationContainer.style.cssText = 'margin-top: 15px; padding: 10px; background: #f8f9fa; border-radius: 4px; border: 1px solid #dee2e6;';
                energyDisplay.parentNode.insertBefore(correlationContainer, energyDisplay.nextSibling);
            }
            
            const avgStretch = correlations.reduce((sum, c) => sum + c.stretchPercentage, 0) / correlations.length;
            const overlappingEdges = correlations.filter(c => c.isOverlapping).length;
            
            correlationContainer.innerHTML = `
                <div style="font-weight: bold; color: #495057; margin-bottom: 8px; font-size: 13px;">Distance-Energy Correlations</div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 10px;">
                    <div style="text-align: center; padding: 5px; background: white; border-radius: 3px;">
                        <div style="font-size: 11px; color: #666;">Avg Stretch</div>
                        <div style="font-size: 14px; font-weight: bold; color: ${Math.abs(avgStretch) > 10 ? 'red' : '#28a745'};">${avgStretch.toFixed(1)}%</div>
                    </div>
                    <div style="text-align: center; padding: 5px; background: white; border-radius: 3px;">
                        <div style="font-size: 11px; color: #666;">Overlapping</div>
                        <div style="font-size: 14px; font-weight: bold; color: ${overlappingEdges > 0 ? 'red' : '#28a745'};">${overlappingEdges}</div>
                    </div>
                </div>
                <div style="font-size: 11px; color: #6c757d;">
                    ${correlations.map(c => `
                        <div style="margin: 3px 0; padding: 2px 5px; background: ${c.isOverlapping ? '#f8d7da' : 'white'}; border-radius: 2px;">
                            <span style="font-weight: bold;">${c.edge}:</span>
                            <span style="color: ${c.isOverlapping ? 'red' : '#007bff'};">${c.surfaceDistance.toFixed(3)}</span>
                            <span style="color: #666;">(${c.stretchPercentage > 0 ? '+' : ''}${c.stretchPercentage.toFixed(1)}%)</span>
                        </div>
                    `).join('')}
                </div>
            `;
        }
        
        function updateNodeDisplay(positions, forces) {
            const container = document.getElementById('nodeInfoContainer');
            container.innerHTML = '';
            
            Object.keys(positions).forEach(nodeId => {
                const pos = positions[nodeId];
                const force = forces[nodeId];
                const forceMag = Math.sqrt(force.x * force.x + force.y * force.y);
                const nodeSize = nodeSizes[nodeId];
                const nodeData = nodes.get(nodeId);
                
                // Calculate surface anchor points and overlap status
                let surfacePoints = [];
                let overlappingNodes = [];
                
                Object.keys(positions).forEach(otherId => {
                    if (otherId !== nodeId) {
                        const otherPos = positions[otherId];
                        const otherNodeData = nodes.get(otherId);
                        const otherSize = nodeSizes[otherId];
                        
                        const currentNode = {x: pos.x, y: pos.y, shape: nodeData.shape, size: nodeSize.width};
                        const otherNode = {x: otherPos.x, y: otherPos.y, shape: otherNodeData.shape, size: otherSize.width};
                        
                        // Check for overlap
                        const penetration = calculatePenetrationDepth(currentNode, otherNode);
                        if (penetration !== null) {
                            overlappingNodes.push(otherId.toUpperCase());
                        }
                        
                        // Calculate surface anchor point
                        const surfacePoint = isPointInShape(otherNode, pos.x, pos.y) ? 
                            {x: otherPos.x, y: otherPos.y, isOverlap: true} :
                            surfacePointToward(currentNode, otherPos.x, otherPos.y);
                        
                        surfacePoints.push({
                            targetNode: otherId.toUpperCase(),
                            point: surfacePoint,
                            distance: penetration !== null ? penetration : 
                                Math.sqrt(Math.pow(surfacePoint.x - pos.x, 2) + Math.pow(surfacePoint.y - pos.y, 2))
                        });
                    }
                });
                
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
                        <span>Shape:</span>
                        <span class="force-value">${nodeData.shape}</span>
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
                    ${overlappingNodes.length > 0 ? `
                    <div class="node-detail" style="background-color: #f8d7da; border-left: 3px solid #dc3545;">
                        <span style="color: #721c24; font-weight: bold;">Overlapping With:</span>
                        <span class="force-value" style="color: #dc3545; font-weight: bold;">${overlappingNodes.join(', ')}</span>
                    </div>
                    ` : ''}
                    <div style="margin-top: 10px; padding: 8px; background: #f8f9fa; border-radius: 4px;">
                        <div style="font-weight: bold; color: #495057; margin-bottom: 5px;">Surface Anchor Points</div>
                        ${surfacePoints.map(sp => `
                        <div class="node-detail">
                            <span>To ${sp.targetNode}:</span>
                            <span class="force-value" style="color: ${sp.point.isOverlap ? 'red' : '#007bff'};">
                                ${sp.point.isOverlap ? 'OVERLAP' : `(${sp.point.x.toFixed(1)}, ${sp.point.y.toFixed(1)})`}
                            </span>
                        </div>
                        <div class="node-detail">
                            <span>Distance:</span>
                            <span class="force-value" style="color: ${sp.distance < 0 ? 'red' : '#007bff'};">${sp.distance.toFixed(3)}</span>
                        </div>
                        `).join('')}
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
                const node1 = {x: positions[edge.from].x, y: positions[edge.from].y, shape: nodes.get(edge.from).shape, size: nodeSizes[edge.from]};
                const node2 = {x: positions[edge.to].x, y: positions[edge.to].y, shape: nodes.get(edge.to).shape, size: nodeSizes[edge.to]};
                
                // Check for overlap first
                const penetration1 = calculatePenetrationDepth(node1, node2);
                const penetration2 = calculatePenetrationDepth(node2, node1);
                
                let distance, pos1, pos2, isOverlapping = false;
                
                if (penetration1 !== null || penetration2 !== null) {
                    // Nodes overlap - use negative distance
                    distance = penetration1 !== null ? penetration1 : penetration2;
                    isOverlapping = true;
                    pos1 = {x: node2.x, y: node2.y};
                    pos2 = {x: node1.x, y: node1.y};
                } else {
                    // No overlap - calculate surface anchor points
                    const surface1 = surfacePointToward(node1, node2.x, node2.y);
                    const surface2 = surfacePointToward(node2, node1.x, node1.y);
                    
                    // Use surface anchor points for all calculations
                    pos1 = surface1;
                    pos2 = surface2;
                    const dx = pos2.x - pos1.x;
                    const dy = pos2.y - pos1.y;
                    distance = Math.sqrt(dx * dx + dy * dy);
                }
                
                const angle = Math.atan2(pos2.y - pos1.y, pos2.x - pos1.x) * (180 / Math.PI);
                
                // Calculate edge properties with surface anchor rest length
                const effectiveL0 = physicsParams.L0 * 1.5;
                const stretch = distance - effectiveL0;
                const stretchPercent = (stretch / effectiveL0) * 100;
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
                    <div class="node-detail" style="background-color: #e8f5e8;">
                        <span>Surface-to-Surface:</span>
                        <span class="force-value" style="color: ${isOverlapping ? 'red' : '#2e7d32'}; font-weight: bold;">${distance.toFixed(3)}</span>
                    </div>
                    <div class="node-detail">
                        <span>Center-to-Center:</span>
                        <span class="force-value">${Math.sqrt(Math.pow(node2.x - node1.x, 2) + Math.pow(node2.y - node1.y, 2)).toFixed(3)}</span>
                    </div>
                    <div class="node-detail">
                        <span>Difference:</span>
                        <span class="force-value">${(distance - Math.sqrt(Math.pow(node2.x - node1.x, 2) + Math.pow(node2.y - node1.y, 2))).toFixed(3)}</span>
                    </div>
                    ${isOverlapping ? '<div class="node-detail"><span style="color: red; font-weight: bold;">Status:</span><span class="force-value" style="color: red; font-weight: bold;">NODES OVERLAP</span></div>' : ''}
                    <div class="distance-highlight" style="background: ${isOverlapping ? '#f8d7da' : '#fff3cd'}; border: 1px solid ${isOverlapping ? '#f5c6cb' : '#ffeaa7'}; margin-top: 10px; padding: 8px; border-radius: 4px;">
                        <div class="distance-title" style="color: ${isOverlapping ? '#721c24' : '#856404'}; font-weight: bold; margin-bottom: 5px;">Mathematical Distance</div>
                        <div class="distance-value" style="color: ${isOverlapping ? 'red' : '#dc3545'}; font-size: 16px; font-weight: bold; text-align: center;">${distance.toFixed(3)} units</div>
                        ${isOverlapping ? '<div style="font-size: 12px; color: #721c24; text-align: center; margin-top: 5px;">Negative value indicates overlap</div>' : ''}
                    </div>
                    <div class="node-detail">
                        <span>Rest Length:</span>
                        <span class="force-value">${effectiveL0.toFixed(3)}</span>
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
