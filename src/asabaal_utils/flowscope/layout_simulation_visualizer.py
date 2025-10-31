#!/usr/bin/env python3
"""
Step-by-step simulation visualizer for the layout relaxer
Features:
- Step through simulation frame by frame
- Auto-play with adjustable frame rate
- Memory optimization for large simulations
- Interactive controls
"""

import json
import time
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

# Import layout relaxer components
try:
    from layout_relaxer import GraphLayout, _relax_iteration
except ImportError:
    # Fallback for testing
    class GraphLayout:
        def __init__(self):
            self.nodes = {}
            self.edges = []
            self.k_spring = 0.1
            self.k_repel = 50.0
            self.k_barrier = 100.0
            self.L0 = 2.0
            self.step = 0.01
            self.damping = 0.95
            self.edge_radius = 0.5
            self._vel = {}
        
        def add_node(self, name, label, shape, color, width, height, pos=(0.0, 0.0)):
            class Node:
                def __init__(self, name, label, shape, color, width, height, x, y):
                    self.name = name
                    self.label = label
                    self.shape = shape
                    self.color = color
                    self.width = width
                    self.height = height
                    self.x = x
                    self.y = y
            
            n = Node(name, label, shape, color, width, height, pos[0], pos[1])
            self.nodes[name] = n
            self._vel[name] = [0.0, 0.0]
        
        def add_edge(self, a, b):
            class Edge:
                def __init__(self, start, end):
                    self.start = start
                    self.end = end
            self.edges.append(Edge(a, b))
    
    def _relax_iteration(G):
        # Simple placeholder iteration
        pass

class LayoutSimulationVisualizer:
    def __init__(self, max_frames_in_memory: int = 100):
        """
        Initialize the visualizer
        
        Args:
            max_frames_in_memory: Maximum number of frames to keep in memory
        """
        self.frames = []
        self.current_frame = 0
        self.max_frames_in_memory = max_frames_in_memory
        self.frame_file = None
        self.is_playing = False
        self.fps = 2.0  # Default 2 FPS
        self.last_frame_time = 0
        
    def run_simulation(self, graph: GraphLayout, iterations: int = 200, 
                      capture_interval: int = 5, output_file: Optional[str] = None):
        """
        Run the layout relaxation simulation and capture frames
        
        Args:
            graph: The graph layout to simulate
            iterations: Number of iterations to run
            capture_interval: Capture every N iterations
            output_file: Optional file to save frames to
        """
        print(f"Running simulation for {iterations} iterations...")
        
        self.frame_file = output_file
        self.frames = []
        
        # Store initial state
        self._capture_frame(graph, 0, graph.step)
        
        # Run simulation
        for it in range(1, iterations + 1):
            # Linear cooling
            t = it / max(1, iterations - 1)
            step = 0.01 * (1.0 - t) + 0.001 * t
            graph.step = step
            
            # Run one iteration
            _relax_iteration(graph)
            
            # Capture frame
            if it % capture_interval == 0:
                self._capture_frame(graph, it, step)
                
                # Memory management: write to file if too many frames
                if len(self.frames) >= self.max_frames_in_memory and output_file:
                    self._write_frames_to_file()
                    self.frames = []
        
        # Write any remaining frames
        if output_file and self.frames:
            self._write_frames_to_file()
            
        print(f"Simulation complete. Captured {self._get_total_frames()} frames.")
        
    def _capture_frame(self, graph: GraphLayout, iteration: int, step: float):
        """Capture current state of the graph"""
        frame = {
            'iteration': iteration,
            'step': step,
            'nodes': {}
        }
        
        for name, node in graph.nodes.items():
            frame['nodes'][name] = {
                'x': node.x,
                'y': node.y,
                'label': node.label,
                'shape': node.shape,
                'color': node.color,
                'width': node.width,
                'height': node.height
            }
        
        self.frames.append(frame)
        
    def _write_frames_to_file(self):
        """Write accumulated frames to file"""
        if not self.frame_file:
            return
            
        # Append to file
        with open(self.frame_file, 'a' if os.path.exists(self.frame_file) else 'w') as f:
            for frame in self.frames:
                json.dump(frame, f)
                f.write('\n')
        
    def _get_total_frames(self) -> int:
        """Get total number of frames (including those written to file)"""
        if not self.frame_file or not os.path.exists(self.frame_file):
            return len(self.frames)
            
        # Count lines in file
        with open(self.frame_file, 'r') as f:
            file_frames = sum(1 for _ in f)
        
        return file_frames + len(self.frames)
    
    def load_frames(self, file_path: str):
        """Load frames from a file"""
        self.frames = []
        self.current_frame = 0
        
        with open(file_path, 'r') as f:
            for line in f:
                if line.strip():
                    self.frames.append(json.loads(line))
        
        print(f"Loaded {len(self.frames)} frames from {file_path}")
    
    def generate_html_visualizer(self, output_path: str):
        """Generate an HTML visualizer for the simulation"""
        html_content = self._create_html_visualizer()
        
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        print(f"HTML visualizer saved to {output_path}")
    
    def _create_html_visualizer(self) -> str:
        """Create the HTML content for the visualizer"""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Layout Relaxation Simulation</title>
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            height: 100vh;
            overflow: hidden;
        }}
        
        .container {{
            display: flex;
            flex-direction: column;
            height: 100vh;
            max-height: 100vh;
        }}
        
        .controls {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            flex-shrink: 0;
        }}
        
        .control-group {{
            display: inline-block;
            margin-right: 20px;
            margin-bottom: 10px;
        }}
        
        .control-group label {{
            display: inline-block;
            width: 120px;
            font-weight: bold;
        }}
        
        button {{
            padding: 8px 16px;
            margin: 2px;
            border: 1px solid #ccc;
            border-radius: 4px;
            background: #007bff;
            color: white;
            cursor: pointer;
            font-size: 14px;
        }}
        
        button:hover {{
            background: #0056b3;
        }}
        
        button:disabled {{
            background: #ccc;
            cursor: not-allowed;
        }}
        
        input[type="range"] {{
            width: 150px;
            margin: 0 10px;
        }}
        
        input[type="number"] {{
            width: 80px;
            padding: 4px;
        }}
        
        .visualization {{
            flex: 1;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            position: relative;
            overflow: hidden;
            min-height: 0;
            display: flex;
        }}
        
        .physics-panel {{
            flex: 0 0 300px;
            position: relative;
            border-right: 1px solid #ddd;
            background: #f8f9fa;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 11px;
            height: 100%;
            max-height: 100%;
        }}
        
        .graph-panel {{
            flex: 1;
            position: relative;
            border-right: 1px solid #ddd;
        }}
        
        .force-panel {{
            flex: 1;
            position: relative;
        }}
        
        .physics-section {{
            border-bottom: 1px solid #dee2e6;
            padding: 10px;
        }}
        
        .physics-title {{
            font-weight: bold;
            color: #495057;
            margin-bottom: 8px;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .physics-value {{
            margin: 3px 0;
            display: flex;
            justify-content: space-between;
        }}
        
        .physics-label {{
            color: #6c757d;
        }}
        
        .physics-number {{
            color: #212529;
            font-weight: bold;
        }}
        
        .physics-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 5px;
        }}
        
        .physics-table th,
        .physics-table td {{
            border: 1px solid #dee2e6;
            padding: 2px 4px;
            text-align: left;
            font-size: 10px;
        }}
        
        .physics-table th {{
            background: #e9ecef;
            font-weight: bold;
        }}
        
        #network {{
            width: 100%;
            height: 100%;
            min-height: 400px;
        }}
        
        #forceCanvas {{
            width: 100%;
            height: 100%;
            min-height: 400px;
        }}
        
        .info {{
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(255,255,255,0.9);
            padding: 10px;
            border-radius: 4px;
            font-size: 12px;
            max-width: 200px;
            z-index: 1000;
        }}
        
        .progress {{
            width: 100%;
            height: 20px;
            background: #f0f0f0;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }}
        
        .progress-bar {{
            height: 100%;
            background: #007bff;
            transition: width 0.3s ease;
        }}
        
        .error {{
            color: red;
            background: #ffebee;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
            display: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="controls">
            <div class="error" id="errorMsg"></div>
            
            <div class="control-group">
                <button id="playBtn" onclick="togglePlay()">Play</button>
                <button id="stepBtn" onclick="stepForward()">Step Forward</button>
                <button id="stepBackBtn" onclick="stepBackward()">Step Back</button>
                <button id="resetBtn" onclick="reset()">Reset</button>
            </div>
            
            <div class="control-group">
                <label>Frame:</label>
                <span id="frameInfo">0 / 0</span>
            </div>
            
            <div class="control-group">
                <label>FPS:</label>
                <input type="range" id="fpsSlider" min="0.5" max="10" step="0.5" value="2" onchange="updateFPS(this.value)">
                <span id="fpsValue">2.0</span>
            </div>
            
            <div class="control-group">
                <label>Speed:</label>
                <input type="number" id="speedInput" min="1" max="50" value="1" onchange="updateSpeed(this.value)">
                <span>frames/step</span>
            </div>
            
            <div class="progress">
                <div class="progress-bar" id="progressBar"></div>
            </div>
        </div>
        
        <div class="visualization">
            <div class="physics-panel">
                <div class="physics-section">
                    <div class="physics-title">Simulation Parameters</div>
                    <div class="physics-value">
                        <span class="physics-label">Iteration:</span>
                        <span class="physics-number" id="physicsIteration">0</span>
                    </div>
                    <div class="physics-value">
                        <span class="physics-label">Step Size:</span>
                        <span class="physics-number" id="physicsStepSize">0.0100</span>
                    </div>
                    <div class="physics-value">
                        <span class="physics-label">Spring K:</span>
                        <span class="physics-number">0.100</span>
                    </div>
                    <div class="physics-value">
                        <span class="physics-label">Repulsion K:</span>
                        <span class="physics-number">5000.0</span>
                    </div>
                    <div class="physics-value">
                        <span class="physics-label">Spring Length:</span>
                        <span class="physics-number">150.0</span>
                    </div>
                    <div class="physics-value">
                        <span class="physics-label">Damping:</span>
                        <span class="physics-number">0.850</span>
                    </div>
                </div>
                
                <div class="physics-section">
                    <div class="physics-title">System Energy</div>
                    <div class="physics-value">
                        <span class="physics-label">Total Energy:</span>
                        <span class="physics-number" id="physicsTotalEnergy">0.00</span>
                    </div>
                    <div class="physics-value">
                        <span class="physics-label">Spring Energy:</span>
                        <span class="physics-number" id="physicsSpringEnergy">0.00</span>
                    </div>
                    <div class="physics-value">
                        <span class="physics-label">Repulsion Energy:</span>
                        <span class="physics-number" id="physicsRepulsionEnergy">0.00</span>
                    </div>
                    <div class="physics-value">
                        <span class="physics-label">Kinetic Energy:</span>
                        <span class="physics-number" id="physicsKineticEnergy">0.00</span>
                    </div>
                </div>
                
                <div class="physics-section">
                    <div class="physics-title">Force Statistics</div>
                    <div class="physics-value">
                        <span class="physics-label">Avg Force:</span>
                        <span class="physics-number" id="physicsAvgForce">0.00</span>
                    </div>
                    <div class="physics-value">
                        <span class="physics-label">Max Force:</span>
                        <span class="physics-number" id="physicsMaxForce">0.00</span>
                    </div>
                    <div class="physics-value">
                        <span class="physics-label">Min Force:</span>
                        <span class="physics-number" id="physicsMinForce">0.00</span>
                    </div>
                    <div class="physics-value">
                        <span class="physics-label">Force StdDev:</span>
                        <span class="physics-number" id="physicsForceStdDev">0.00</span>
                    </div>
                </div>
                
                <div class="physics-section">
                    <div class="physics-title">Distance Statistics</div>
                    <div class="physics-value">
                        <span class="physics-label">Avg Distance:</span>
                        <span class="physics-number" id="physicsAvgDistance">0.00</span>
                    </div>
                    <div class="physics-value">
                        <span class="physics-label">Max Distance:</span>
                        <span class="physics-number" id="physicsMaxDistance">0.00</span>
                    </div>
                    <div class="physics-value">
                        <span class="physics-label">Min Distance:</span>
                        <span class="physics-number" id="physicsMinDistance">0.00</span>
                    </div>
                    <div class="physics-value">
                        <span class="physics-label">Distance StdDev:</span>
                        <span class="physics-number" id="physicsDistanceStdDev">0.00</span>
                    </div>
                </div>
                
                <div class="physics-section">
                    <div class="physics-title">Node Details</div>
                    <div id="nodeDetailsContainer">
                        <table class="physics-table">
                            <thead>
                                <tr>
                                    <th>Node</th>
                                    <th>Force</th>
                                    <th>Velocity</th>
                                    <th>Position</th>
                                </tr>
                            </thead>
                            <tbody id="nodeDetailsTable">
                            </tbody>
                        </table>
                    </div>
                </div>
                
                <div class="physics-section">
                    <div class="physics-title">Edge Details</div>
                    <div id="edgeDetailsContainer">
                        <table class="physics-table">
                            <thead>
                                <tr>
                                    <th>Edge</th>
                                    <th>Distance</th>
                                    <th>Spring Force</th>
                                    <th>Energy</th>
                                </tr>
                            </thead>
                            <tbody id="edgeDetailsTable">
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            
            <div class="graph-panel">
                <div id="network"></div>
                <div class="info">
                    <div><strong>Iteration:</strong> <span id="iteration">0</span></div>
                    <div><strong>Step Size:</strong> <span id="stepSize">0.01</span></div>
                    <div><strong>Nodes:</strong> <span id="nodeCount">0</span></div>
                    <div><strong>Playing:</strong> <span id="playingStatus">No</span></div>
                </div>
            </div>
            <div class="force-panel">
                <canvas id="forceCanvas"></canvas>
                <div class="info" style="left: 10px; right: auto;">
                    <div><strong>Total Energy:</strong> <span id="totalEnergy">0.00</span></div>
                    <div><strong>Avg Force:</strong> <span id="avgForce">0.00</span></div>
                    <div><strong>Avg Distance:</strong> <span id="avgDistance">0.00</span></div>
                    <div><strong>Max Force:</strong> <span id="maxForce">0.00</span></div>
                </div>
            </div>
        </div>
    </div>

    <script>
         // Simulation data
         const frames = {json.dumps(self.frames)};
         let currentFrame = 0;
         let isPlaying = false;
         let fps = 2.0;
         let speed = 1;
         let lastFrameTime = 0;
         let network = null;
         let animationId = null;
         let forceCanvas = null;
         let forceCtx = null;

        // Error handling
        function showError(message) {{
            const errorEl = document.getElementById('errorMsg');
            errorEl.textContent = message;
            errorEl.style.display = 'block';
            console.error(message);
        }}

        function hideError() {{
            document.getElementById('errorMsg').style.display = 'none';
        }}

        // Initialize network
        function initNetwork() {{
            try {{
                const container = document.getElementById('network');
                const data = {{
                    nodes: new vis.DataSet([]),
                    edges: new vis.DataSet([])
                }};
                
                const options = {{
                    physics: {{ enabled: false }},
                    interaction: {{
                        zoomView: true,
                        dragView: true
                    }},
                    layout: {{
                        hierarchical: {{ enabled: false }}
                    }},
                    nodes: {{
                        shape: 'box'
                    }},
                    edges: {{
                        smooth: {{ enabled: false }}
                    }}
                }};
                
                network = new vis.Network(container, data, options);
                console.log('Network initialized successfully');
            }} catch (error) {{
                showError('Failed to initialize network: ' + error.message);
            }}
        }}

        // Function to detect structure type
        function detectStructureType(nodeIds) {{
            const name = nodeIds.length > 0 ? nodeIds[0].toLowerCase() : '';
            if (name.includes('binary')) return 'binary';
            if (name.includes('loop')) return 'loop';
            if (name.includes('nested')) return 'nested';
            if (name.includes('multi')) return 'multi';
            return 'linear';
        }}

        // Function to create all edges for a structure
        function createAllEdges(nodeIds, type) {{
            const edges = [];
            const sortedIds = [...nodeIds].sort();
            
            // Linear connections (always present)
            for (let i = 0; i < sortedIds.length - 1; i++) {{
                edges.push([sortedIds[i], sortedIds[i + 1]]);
            }}
            
            // Structure-specific edges
            if (type === 'binary') {{
                for (let i = 1; i < sortedIds.length; i++) {{
                    const parentIndex = Math.floor((i - 1) / 2);
                    if (parentIndex < sortedIds.length && parentIndex !== i) {{
                        edges.push([sortedIds[parentIndex], sortedIds[i]]);
                    }}
                }}
            }} else if (type === 'loop') {{
                if (sortedIds.length > 3) {{
                    edges.push([sortedIds[sortedIds.length - 2], sortedIds[2]]);
                }}
            }}
            
            return edges;
        }}

        // Calculate forces for current frame
        function calculateForces(frame) {{
            const nodes = Object.entries(frame.nodes);
            const forces = {{}};
            const springStrength = 0.1;
            const springLength = 150;
            const repulsionStrength = 5000;
            
            // Initialize forces
            nodes.forEach(([id, node]) => {{
                forces[id] = {{ x: 0, y: 0 }};
            }});
            
            // Create edges
            const nodeIds = nodes.map(([id]) => id);
            const structureType = detectStructureType(nodeIds);
            const edges = createAllEdges(nodeIds, structureType);
            
            // Spring forces
            edges.forEach(([from, to]) => {{
                if (frame.nodes[from] && frame.nodes[to]) {{
                    const nodeA = frame.nodes[from];
                    const nodeB = frame.nodes[to];
                    const dx = (nodeB.x - nodeA.x) * 50;
                    const dy = (nodeB.y - nodeA.y) * 50;
                    const distance = Math.sqrt(dx * dx + dy * dy);
                    
                    if (distance > 0) {{
                        const force = springStrength * (distance - springLength);
                        const fx = (dx / distance) * force;
                        const fy = (dy / distance) * force;
                        
                        forces[from].x += fx;
                        forces[from].y += fy;
                        forces[to].x -= fx;
                        forces[to].y -= fy;
                    }}
                }}
            }});
            
            // Repulsion forces
            for (let i = 0; i < nodes.length; i++) {{
                for (let j = i + 1; j < nodes.length; j++) {{
                    const [idA, nodeA] = nodes[i];
                    const [idB, nodeB] = nodes[j];
                    
                    const dx = (nodeB.x - nodeA.x) * 50;
                    const dy = (nodeB.y - nodeA.y) * 50;
                    const distance = Math.sqrt(dx * dx + dy * dy);
                    
                    if (distance > 0 && distance < 500) {{
                        const force = repulsionStrength / (distance * distance);
                        const fx = (dx / distance) * force;
                        const fy = (dy / distance) * force;
                        
                        forces[idA].x -= fx;
                        forces[idA].y -= fy;
                        forces[idB].x += fx;
                        forces[idB].y += fy;
                    }}
                }}
            }}
            
            return forces;
        }}

        // Update network with current frame
        function updateNetwork() {{
            try {{
                if (currentFrame >= frames.length || currentFrame < 0) {{
                    console.warn('Invalid frame index:', currentFrame);
                    return;
                }}
                
                const frame = frames[currentFrame];
                if (!frame || !frame.nodes) {{
                    showError('Invalid frame data at index ' + currentFrame);
                    return;
                }}
                
                const nodes = [];
                const edges = [];
                const nodeIds = Object.keys(frame.nodes);
                
                // Create nodes
                Object.entries(frame.nodes).forEach(([id, nodeData]) => {{
                    nodes.push({{
                        id: id,
                        label: nodeData.label || id,
                        x: (nodeData.x || 0) * 50,
                        y: (nodeData.y || 0) * 50,
                        shape: nodeData.shape || 'box',
                        color: {{
                            background: nodeData.color || '#97c2fc',
                            border: '#333'
                        }},
                        font: {{
                            size: 12,
                            color: '#333'
                        }}
                    }});
                }});
                
                // Create edges
                const structureType = detectStructureType(nodeIds);
                const allEdges = createAllEdges(nodeIds, structureType);
                
                allEdges.forEach(([from, to]) => {{
                    edges.push({{
                        from: from,
                        to: to,
                        color: '#666',
                        width: 2,
                        arrows: 'to',
                        smooth: {{ enabled: false }}
                    }});
                }});
                
                network.setData({{ nodes: nodes, edges: edges }});
                updateInfo();
                updateForceField();
                updatePhysicsPanel(calculateForces(frame), frame);
                hideError();
                
            }} catch (error) {{
                showError('Error updating network: ' + error.message);
                console.error('Update network error:', error);
            }}
        }}

        // Update info display
        function updateInfo() {{
            try {{
                if (currentFrame >= frames.length || currentFrame < 0) return;
                
                const frame = frames[currentFrame];
                document.getElementById('frameInfo').textContent = `${{currentFrame}} / ${{frames.length - 1}}`;
                document.getElementById('iteration').textContent = frame.iteration || 0;
                document.getElementById('stepSize').textContent = (frame.step || 0).toFixed(4);
                document.getElementById('nodeCount').textContent = Object.keys(frame.nodes || {{}}).length;
                document.getElementById('playingStatus').textContent = isPlaying ? 'Yes' : 'No';
                
                const progress = frames.length > 1 ? (currentFrame / (frames.length - 1)) * 100 : 0;
                document.getElementById('progressBar').style.width = progress + '%';
            }} catch (error) {{
                console.error('Error updating info:', error);
            }}
        }}

        // Control functions
        function togglePlay() {{
            try {{
                isPlaying = !isPlaying;
                document.getElementById('playBtn').textContent = isPlaying ? 'Pause' : 'Play';
                
                if (isPlaying) {{
                    lastFrameTime = performance.now();
                    animate();
                }} else {{
                    if (animationId) {{
                        cancelAnimationFrame(animationId);
                        animationId = null;
                    }}
                }}
            }} catch (error) {{
                showError('Error toggling play: ' + error.message);
            }}
        }}

        function animate() {{
            if (!isPlaying) return;
            
            try {{
                const currentTime = performance.now();
                const deltaTime = currentTime - lastFrameTime;
                const frameInterval = 1000 / fps;
                
                if (deltaTime >= frameInterval) {{
                    stepForward();
                    lastFrameTime = currentTime;
                }}
                
                animationId = requestAnimationFrame(animate);
            }} catch (error) {{
                showError('Animation error: ' + error.message);
                isPlaying = false;
                document.getElementById('playBtn').textContent = 'Play';
            }}
        }}

        function stepForward() {{
            try {{
                if (currentFrame < frames.length - 1) {{
                    currentFrame += speed;
                    currentFrame = Math.min(currentFrame, frames.length - 1);
                    updateNetwork();
                }}
            }} catch (error) {{
                showError('Error stepping forward: ' + error.message);
            }}
        }}

        function stepBackward() {{
            try {{
                if (currentFrame > 0) {{
                    currentFrame -= speed;
                    currentFrame = Math.max(currentFrame, 0);
                    updateNetwork();
                }}
            }} catch (error) {{
                showError('Error stepping backward: ' + error.message);
            }}
        }}

        function reset() {{
            try {{
                currentFrame = 0;
                isPlaying = false;
                document.getElementById('playBtn').textContent = 'Play';
                if (animationId) {{
                    cancelAnimationFrame(animationId);
                    animationId = null;
                }}
                updateNetwork();
            }} catch (error) {{
                showError('Error resetting: ' + error.message);
            }}
        }}

        function updateFPS(value) {{
            fps = parseFloat(value);
            document.getElementById('fpsValue').textContent = fps.toFixed(1);
        }}

        function updateSpeed(value) {{
            speed = parseInt(value);
            speed = Math.max(1, Math.min(50, speed));
        }}

        // Initialize force canvas
        function initForceCanvas() {{
            forceCanvas = document.getElementById('forceCanvas');
            forceCtx = forceCanvas.getContext('2d');
            resizeForceCanvas();
        }}
        
        // Resize force canvas
        function resizeForceCanvas() {{
            const rect = forceCanvas.parentElement.getBoundingClientRect();
            forceCanvas.width = rect.width;
            forceCanvas.height = rect.height;
        }}
        
        // Update force field visualization
        function updateForceField() {{
            if (!forceCtx || currentFrame >= frames.length) return;
            
            const frame = frames[currentFrame];
            const forces = calculateForces(frame);
            
            // Clear canvas
            forceCtx.clearRect(0, 0, forceCanvas.width, forceCanvas.height);
            
            // Calculate actual node bounds for proper scaling
            const nodes = Object.values(frame.nodes);
            const padding = 40;
            
            // Find min/max coordinates of nodes (use same scaling as graph)
            const minX = Math.min(...nodes.map(n => n.x * 50));
            const maxX = Math.max(...nodes.map(n => n.x * 50));
            const minY = Math.min(...nodes.map(n => n.y * 50));
            const maxY = Math.max(...nodes.map(n => n.y * 50));
            
            const nodeWidth = maxX - minX || 100;
            const nodeHeight = maxY - minY || 100;
            
            // Calculate scale to fit nodes in canvas with padding
            const scaleX = (forceCanvas.width - 2 * padding) / nodeWidth;
            const scaleY = (forceCanvas.height - 2 * padding) / nodeHeight;
            const scale = Math.min(scaleX, scaleY, 2.0);
            
            // Center the visualization
            const centerX = forceCanvas.width / 2;
            const centerY = forceCanvas.height / 2;
            const offsetX = (minX + maxX) / 2 * scale; // Average offset * scale
            const offsetY = (minY + maxY) / 2 * scale;
            
            // Transform coordinates (match graph panel scaling)
            const transformX = (x) => centerX + x * 50 * scale - offsetX;
            const transformY = (y) => centerY + y * 50 * scale - offsetY;
            
            // Draw force field heatmap
            const gridSize = 25;
            const cellWidth = forceCanvas.width / gridSize;
            const cellHeight = forceCanvas.height / gridSize;
            
            for (let i = 0; i < gridSize; i++) {{
                for (let j = 0; j < gridSize; j++) {{
                    const x = (i + 0.5) * cellWidth;
                    const y = (j + 0.5) * cellHeight;
                    
                    let totalForce = 0;
                    Object.entries(frame.nodes).forEach(([id, node]) => {{
                        const nodeX = transformX(node.x);
                        const nodeY = transformY(node.y);
                        const dx = x - nodeX;
                        const dy = y - nodeY;
                        const distance = Math.sqrt(dx * dx + dy * dy);
                        
                        if (distance > 0 && distance < 200 * scale) {{
                            totalForce += 3000 / (distance * distance);
                        }}
                    }});
                    
                    const intensity = Math.min(totalForce / 8, 1);
                    const hue = (1 - intensity) * 240; // Blue to red
                    forceCtx.fillStyle = `hsla(${{hue}}, 100%, 50%, 0.25)`;
                    forceCtx.fillRect(i * cellWidth, j * cellHeight, cellWidth, cellHeight);
                }}
            }}
            
            // Draw nodes and force vectors
            Object.entries(frame.nodes).forEach(([id, node]) => {{
                const x = transformX(node.x);
                const y = transformY(node.y);
                
                // Draw node
                forceCtx.fillStyle = 'white';
                forceCtx.strokeStyle = 'black';
                forceCtx.lineWidth = 2;
                forceCtx.beginPath();
                forceCtx.arc(x, y, 8, 0, Math.PI * 2);
                forceCtx.fill();
                forceCtx.stroke();
                
                // Draw node label
                forceCtx.fillStyle = 'black';
                forceCtx.font = '10px Arial';
                forceCtx.textAlign = 'center';
                forceCtx.textBaseline = 'middle';
                forceCtx.fillText(id, x, y);
                
                // Draw force vector
                const force = forces[id];
                const forceMag = Math.sqrt(force.x * force.x + force.y * force.y);
                if (forceMag > 0.05) {{
                    const vectorScale = Math.min(forceMag * scale * 0.5, 60);
                    const endX = x + (force.x / forceMag) * vectorScale;
                    const endY = y + (force.y / forceMag) * vectorScale;
                    
                    forceCtx.strokeStyle = 'red';
                    forceCtx.lineWidth = 2;
                    forceCtx.beginPath();
                    forceCtx.moveTo(x, y);
                    forceCtx.lineTo(endX, endY);
                    forceCtx.stroke();
                    
                    // Arrowhead
                    const angle = Math.atan2(force.y, force.x);
                    const arrowSize = 6;
                    forceCtx.beginPath();
                    forceCtx.moveTo(endX, endY);
                    forceCtx.lineTo(endX - arrowSize * Math.cos(angle - 0.5), endY - arrowSize * Math.sin(angle - 0.5));
                    forceCtx.lineTo(endX - arrowSize * Math.cos(angle + 0.5), endY - arrowSize * Math.sin(angle + 0.5));
                    forceCtx.closePath();
                    forceCtx.fillStyle = 'red';
                    forceCtx.fill();
                }}
            }});
            
            updateForceMetrics(forces, frame);
        }}
        
        // Update force metrics
        function updateForceMetrics(forces, frame) {{
            const forceValues = Object.values(forces);
            const avgForce = forceValues.reduce((sum, f) => sum + Math.sqrt(f.x * f.x + f.y * f.y), 0) / forceValues.length;
            const maxForce = Math.max(...forceValues.map(f => Math.sqrt(f.x * f.x + f.y * f.y)));
            
            let totalDistance = 0;
            let edgeCount = 0;
            const nodeIds = Object.keys(frame.nodes);
            const structureType = detectStructureType(nodeIds);
            const edges = createAllEdges(nodeIds, structureType);
            
            edges.forEach(([from, to]) => {{
                if (frame.nodes[from] && frame.nodes[to]) {{
                    const nodeA = frame.nodes[from];
                    const nodeB = frame.nodes[to];
                    const dx = (nodeB.x - nodeA.x) * 50;
                    const dy = (nodeB.y - nodeA.y) * 50;
                    totalDistance += Math.sqrt(dx * dx + dy * dy);
                    edgeCount++;
                }}
            }});
            const avgDistance = edgeCount > 0 ? totalDistance / edgeCount : 0;
            
            // Calculate total energy
            let totalEnergy = 0;
            edges.forEach(([from, to]) => {{
                if (frame.nodes[from] && frame.nodes[to]) {{
                    const nodeA = frame.nodes[from];
                    const nodeB = frame.nodes[to];
                    const dx = (nodeB.x - nodeA.x) * 50;
                    const dy = (nodeB.y - nodeA.y) * 50;
                    const distance = Math.sqrt(dx * dx + dy * dy);
                    totalEnergy += 0.5 * 0.1 * Math.pow(distance - 150, 2);
                }}
            }});
            
            document.getElementById('totalEnergy').textContent = totalEnergy.toFixed(2);
            document.getElementById('avgForce').textContent = avgForce.toFixed(2);
            document.getElementById('avgDistance').textContent = avgDistance.toFixed(2);
            document.getElementById('maxForce').textContent = maxForce.toFixed(2);
        }}
        
        // Update physics panel with detailed information
        function updatePhysicsPanel(forces, frame) {{
            // Update basic parameters
            document.getElementById('physicsIteration').textContent = frame.iteration || 0;
            document.getElementById('physicsStepSize').textContent = (frame.step || 0).toFixed(4);
            
            // Calculate detailed energy breakdown
            const energyBreakdown = calculateEnergyBreakdown(forces, frame);
            document.getElementById('physicsTotalEnergy').textContent = energyBreakdown.total.toFixed(2);
            document.getElementById('physicsSpringEnergy').textContent = energyBreakdown.spring.toFixed(2);
            document.getElementById('physicsRepulsionEnergy').textContent = energyBreakdown.repulsion.toFixed(2);
            document.getElementById('physicsKineticEnergy').textContent = energyBreakdown.kinetic.toFixed(2);
            
            // Calculate force statistics
            const forceStats = calculateForceStatistics(forces);
            document.getElementById('physicsAvgForce').textContent = forceStats.avg.toFixed(2);
            document.getElementById('physicsMaxForce').textContent = forceStats.max.toFixed(2);
            document.getElementById('physicsMinForce').textContent = forceStats.min.toFixed(2);
            document.getElementById('physicsForceStdDev').textContent = forceStats.stdDev.toFixed(2);
            
            // Calculate distance statistics
            const distanceStats = calculateDistanceStatistics(frame);
            document.getElementById('physicsAvgDistance').textContent = distanceStats.avg.toFixed(2);
            document.getElementById('physicsMaxDistance').textContent = distanceStats.max.toFixed(2);
            document.getElementById('physicsMinDistance').textContent = distanceStats.min.toFixed(2);
            document.getElementById('physicsDistanceStdDev').textContent = distanceStats.stdDev.toFixed(2);
            
            // Update node details table
            updateNodeDetailsTable(forces, frame);
            
            // Update edge details table
            updateEdgeDetailsTable(frame);
        }}
        
        // Calculate detailed energy breakdown
        function calculateEnergyBreakdown(forces, frame) {{
            let springEnergy = 0;
            let repulsionEnergy = 0;
            let kineticEnergy = 0;
            
            const springStrength = 0.1;
            const springLength = 150;
            const repulsionStrength = 5000;
            
            // Spring energy
            const nodeIds = Object.keys(frame.nodes);
            const structureType = detectStructureType(nodeIds);
            const edges = createAllEdges(nodeIds, structureType);
            
            edges.forEach(([from, to]) => {{
                if (frame.nodes[from] && frame.nodes[to]) {{
                    const nodeA = frame.nodes[from];
                    const nodeB = frame.nodes[to];
                    const dx = (nodeB.x - nodeA.x) * 50;
                    const dy = (nodeB.y - nodeA.y) * 50;
                    const distance = Math.sqrt(dx * dx + dy * dy);
                    springEnergy += 0.5 * springStrength * Math.pow(distance - springLength, 2);
                }}
            }});
            
            // Repulsion energy
            const nodes = Object.entries(frame.nodes);
            for (let i = 0; i < nodes.length; i++) {{
                for (let j = i + 1; j < nodes.length; j++) {{
                    const [idA, nodeA] = nodes[i];
                    const [idB, nodeB] = nodes[j];
                    const dx = (nodeB.x - nodeA.x) * 50;
                    const dy = (nodeB.y - nodeA.y) * 50;
                    const distance = Math.sqrt(dx * dx + dy * dy);
                    if (distance > 0 && distance < 500) {{
                        repulsionEnergy += repulsionStrength / distance;
                    }}
                }}
            }}
            
            // Kinetic energy (simplified - based on forces)
            Object.values(forces).forEach(force => {{
                const forceMag = Math.sqrt(force.x * force.x + force.y * force.y);
                kineticEnergy += 0.5 * forceMag * forceMag;
            }});
            
            return {{
                total: springEnergy + repulsionEnergy + kineticEnergy,
                spring: springEnergy,
                repulsion: repulsionEnergy,
                kinetic: kineticEnergy
            }};
        }}
        
        // Calculate force statistics
        function calculateForceStatistics(forces) {{
            const forceMagnitudes = Object.values(forces).map(f => Math.sqrt(f.x * f.x + f.y * f.y));
            const avg = forceMagnitudes.reduce((sum, f) => sum + f, 0) / forceMagnitudes.length;
            const max = Math.max(...forceMagnitudes);
            const min = Math.min(...forceMagnitudes);
            
            const variance = forceMagnitudes.reduce((sum, f) => sum + Math.pow(f - avg, 2), 0) / forceMagnitudes.length;
            const stdDev = Math.sqrt(variance);
            
            return {{ avg, max, min, stdDev }};
        }}
        
        // Calculate distance statistics
        function calculateDistanceStatistics(frame) {{
            const nodeIds = Object.keys(frame.nodes);
            const structureType = detectStructureType(nodeIds);
            const edges = createAllEdges(nodeIds, structureType);
            const distances = [];
            
            edges.forEach(([from, to]) => {{
                if (frame.nodes[from] && frame.nodes[to]) {{
                    const nodeA = frame.nodes[from];
                    const nodeB = frame.nodes[to];
                    const dx = (nodeB.x - nodeA.x) * 50;
                    const dy = (nodeB.y - nodeA.y) * 50;
                    const distance = Math.sqrt(dx * dx + dy * dy);
                    distances.push(distance);
                }}
            }});
            
            if (distances.length === 0) return {{ avg: 0, max: 0, min: 0, stdDev: 0 }};
            
            const avg = distances.reduce((sum, d) => sum + d, 0) / distances.length;
            const max = Math.max(...distances);
            const min = Math.min(...distances);
            
            const variance = distances.reduce((sum, d) => sum + Math.pow(d - avg, 2), 0) / distances.length;
            const stdDev = Math.sqrt(variance);
            
            return {{ avg, max, min, stdDev }};
        }}
        
        // Update node details table
        function updateNodeDetailsTable(forces, frame) {{
            const tbody = document.getElementById('nodeDetailsTable');
            tbody.innerHTML = '';
            
            Object.entries(frame.nodes).forEach(([id, node]) => {{
                const force = forces[id];
                const forceMag = Math.sqrt(force.x * force.x + force.y * force.y);
                
                const row = tbody.insertRow();
                row.insertCell(0).textContent = id;
                row.insertCell(1).textContent = forceMag.toFixed(2);
                row.insertCell(2).textContent = "(" + force.x.toFixed(1) + ", " + force.y.toFixed(1) + ")";
                row.insertCell(3).textContent = "(" + node.x.toFixed(1) + ", " + node.y.toFixed(1) + ")";
            }});
        }}
        
        // Update edge details table
        function updateEdgeDetailsTable(frame) {{
            const tbody = document.getElementById('edgeDetailsTable');
            tbody.innerHTML = '';
            
            const nodeIds = Object.keys(frame.nodes);
            const structureType = detectStructureType(nodeIds);
            const edges = createAllEdges(nodeIds, structureType);
            const springStrength = 0.1;
            const springLength = 150;
            
            edges.forEach(([from, to]) => {{
                if (frame.nodes[from] && frame.nodes[to]) {{
                    const nodeA = frame.nodes[from];
                    const nodeB = frame.nodes[to];
                    const dx = (nodeB.x - nodeA.x) * 50;
                    const dy = (nodeB.y - nodeA.y) * 50;
                    const distance = Math.sqrt(dx * dx + dy * dy);
                    const springForce = Math.abs(springStrength * (distance - springLength));
                    const energy = 0.5 * springStrength * Math.pow(distance - springLength, 2);
                    
                    const row = tbody.insertRow();
                    row.insertCell(0).textContent = from + "→" + to;
                    row.insertCell(1).textContent = distance.toFixed(2);
                    row.insertCell(2).textContent = springForce.toFixed(2);
                    row.insertCell(3).textContent = energy.toFixed(2);
                }}
            }});
        }}
        
        // Handle window resize
        window.onresize = function() {{
            if (network) {{
                network.redraw();
                network.fit();
            }}
            if (forceCanvas) {{
                resizeForceCanvas();
                updateForceField();
            }}
        }};

         // Initialize on load
         window.onload = function() {{
             console.log('Page loaded, initializing...');
             try {{
                 if (frames.length === 0) {{
                     showError('No simulation frames available');
                     return;
                 }}
                 
                 initNetwork();
                 initForceCanvas();
                 updateNetwork();
                 console.log('Initialization complete');
             }} catch (error) {{
                 showError('Initialization error: ' + error.message);
                 console.error('Init error:', error);
             }}
         }};
    </script>
</body>
</html>
        """

def create_test_graph():
    """Create a test graph for simulation"""
    G = GraphLayout()
    
    # Conservative physics parameters
    G.k_spring = 0.1
    G.k_repel = 50.0
    G.k_barrier = 100.0
    G.L0 = 2.0
    G.step = 0.01
    G.damping = 0.95
    G.edge_radius = 0.5
    
    # Legend-based styles
    STYLES = {
        "Entry":       dict(shape="ellipse", color="#90ee90"),
        "Exit":        dict(shape="ellipse", color="#ff6b6b"),
        "Assignment":  dict(shape="box",     color="#ffd700"),
        "Conditional": dict(shape="diamond", color="#ffa500"),
        "Loop":        dict(shape="diamond", color="#ff9999"),
        "Statement":   dict(shape="box",     color="#97c2fc"),
        "Return":      dict(shape="box",     color="#90ee90"),
        "Try":         dict(shape="box",     color="#dda0dd"),
        "Except":      dict(shape="box",     color="#f0e68c"),
        "Merge":       dict(shape="circle",  color="#d3d3d3"),
    }
    
    # Create a more complex test graph
    G.add_node("n0", "entry",    **STYLES["Entry"],      width=1.8, height=1.2, pos=(0.0, 0.0))
    G.add_node("n1", "cond1",    **STYLES["Conditional"],width=2.2, height=1.6, pos=(2.0, 2.0))
    G.add_node("n2", "assign1",  **STYLES["Assignment"], width=2.8, height=1.2, pos=(-2.0, 4.0))
    G.add_node("n3", "loop",     **STYLES["Loop"],       width=2.0, height=1.6, pos=( 2.0, 4.0))
    G.add_node("n4", "assign2",  **STYLES["Assignment"], width=2.5, height=1.2, pos=(4.0, 6.0))
    G.add_node("n5", "cond2",    **STYLES["Conditional"],width=2.2, height=1.6, pos=(0.0, 6.0))
    G.add_node("n6", "assign3",  **STYLES["Assignment"], width=2.0, height=1.2, pos=(-2.0, 8.0))
    G.add_node("n7", "merge1",   **STYLES["Merge"],      width=1.2, height=1.2, pos=(2.0, 8.0))
    G.add_node("n8", "merge2",   **STYLES["Merge"],      width=1.2, height=1.2, pos=(0.0, 10.0))
    G.add_node("n9", "return",   **STYLES["Return"],     width=2.2, height=1.2, pos=(0.0, 12.0))
    G.add_node("n10","exit",     **STYLES["Exit"],       width=1.8, height=1.2, pos=(0.0, 14.0))

    # Add edges
    G.add_edge("n0", "n1")
    G.add_edge("n1", "n2")  # true branch
    G.add_edge("n1", "n3")  # false branch
    G.add_edge("n3", "n4")
    G.add_edge("n4", "n3")  # loop back
    G.add_edge("n3", "n5")  # loop exit
    G.add_edge("n5", "n6")  # true branch
    G.add_edge("n5", "n7")  # false branch
    G.add_edge("n2", "n8")
    G.add_edge("n6", "n8")
    G.add_edge("n7", "n8")
    G.add_edge("n8", "n9")
    G.add_edge("n9", "n10")
    
    return G

def main():
    parser = argparse.ArgumentParser(description='Layout Relaxation Simulation Visualizer')
    parser.add_argument('--iterations', type=int, default=300, help='Number of iterations')
    parser.add_argument('--capture-interval', type=int, default=5, help='Capture every N iterations')
    parser.add_argument('--max-memory-frames', type=int, default=100, help='Max frames in memory')
    parser.add_argument('--output-dir', type=str, default='.', help='Output directory')
    parser.add_argument('--load-frames', type=str, help='Load frames from file')
    
    args = parser.parse_args()
    
    visualizer = LayoutSimulationVisualizer(max_frames_in_memory=args.max_memory_frames)
    
    if args.load_frames:
        # Load existing frames
        visualizer.load_frames(args.load_frames)
    else:
        # Run new simulation
        graph = create_test_graph()
        frames_file = os.path.join(args.output_dir, 'simulation_frames.json')
        visualizer.run_simulation(
            graph, 
            iterations=args.iterations,
            capture_interval=args.capture_interval,
            output_file=frames_file
        )
        
        # Reload frames for visualization
        visualizer.load_frames(frames_file)
    
    # Generate HTML visualizer
    html_file = os.path.join(args.output_dir, 'layout_simulation.html')
    visualizer.generate_html_visualizer(html_file)
    
    print(f"\\nSimulation complete! Open {html_file} to view the interactive visualization.")

if __name__ == "__main__":
    main()