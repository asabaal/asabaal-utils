"""
Physics Debug Visualizer for Layout Relaxer
Split-window visualization showing graph and force field analysis
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk
import colorsys
from scipy.spatial.distance import cdist
from layout_relaxer import LayoutRelaxer

class PhysicsDebugVisualizer:
    def __init__(self, root, structure_data, initial_positions):
        self.root = root
        self.root.title("Physics Debug Visualizer - Force Field Analysis")
        
        self.structure_data = structure_data
        self.positions = initial_positions.copy()
        self.velocities = np.zeros_like(self.positions)
        self.forces = np.zeros_like(self.positions)
        
        # Physics parameters
        self.spring_strength = 0.1
        self.spring_length = 150.0
        self.repulsion_strength = 5000.0
        self.damping = 0.85
        self.dt = 0.01
        
        # Simulation state
        self.is_running = False
        self.step_count = 0
        self.fps = 30
        self.auto_play = False
        
        # Energy tracking
        self.energy_history = []
        self.force_magnitude_history = []
        self.distance_history = []
        
        self.setup_ui()
        self.update_visualization()
        
    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Graph visualization
        left_frame = ttk.LabelFrame(main_frame, text="Graph Visualization", padding=10)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        self.fig_graph = plt.Figure(figsize=(8, 8), dpi=80)
        self.ax_graph = self.fig_graph.add_subplot(111)
        self.canvas_graph = FigureCanvasTkAgg(self.fig_graph, left_frame)
        self.canvas_graph.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Right panel - Force field visualization
        right_frame = ttk.LabelFrame(main_frame, text="Force Field Analysis", padding=10)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        self.fig_forces = plt.Figure(figsize=(8, 8), dpi=80)
        self.ax_forces = self.fig_forces.add_subplot(111)
        self.canvas_forces = FigureCanvasTkAgg(self.fig_forces, right_frame)
        self.canvas_forces.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        
        # Control panel
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Simulation controls
        ttk.Button(control_frame, text="Step", command=self.step_simulation).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Reset", command=self.reset_simulation).pack(side=tk.LEFT, padx=2)
        
        self.auto_play_btn = ttk.Button(control_frame, text="Auto Play", command=self.toggle_auto_play)
        self.auto_play_btn.pack(side=tk.LEFT, padx=2)
        
        # FPS control
        ttk.Label(control_frame, text="FPS:").pack(side=tk.LEFT, padx=(10, 2))
        self.fps_var = tk.IntVar(value=30)
        fps_spinbox = ttk.Spinbox(control_frame, from_=1, to=120, textvariable=self.fps_var, width=8)
        fps_spinbox.pack(side=tk.LEFT, padx=2)
        fps_spinbox.bind('<Return>', lambda e: self.update_fps())
        
        # Physics parameters
        ttk.Label(control_frame, text="Spring:").pack(side=tk.LEFT, padx=(10, 2))
        self.spring_var = tk.DoubleVar(value=0.1)
        spring_scale = ttk.Scale(control_frame, from_=0.01, to=1.0, variable=self.spring_var, 
                                 orient=tk.HORIZONTAL, length=100, command=lambda v: self.update_physics())
        spring_scale.pack(side=tk.LEFT, padx=2)
        
        ttk.Label(control_frame, text="Repulsion:").pack(side=tk.LEFT, padx=(10, 2))
        self.repulsion_var = tk.DoubleVar(value=5000.0)
        repulsion_scale = ttk.Scale(control_frame, from_=100, to=20000, variable=self.repulsion_var,
                                   orient=tk.HORIZONTAL, length=100, command=lambda v: self.update_physics())
        repulsion_scale.pack(side=tk.LEFT, padx=2)
        
        # Status display
        self.status_label = ttk.Label(control_frame, text="Step: 0 | Energy: 0.00 | Avg Force: 0.00")
        self.status_label.pack(side=tk.LEFT, padx=(20, 0))
        
    def calculate_forces(self):
        """Calculate all forces acting on nodes"""
        n = len(self.positions)
        self.forces = np.zeros_like(self.positions)
        
        # Spring forces (attraction along edges)
        for edge in self.structure_data['edges']:
            i, j = edge['source'], edge['target']
            delta = self.positions[j] - self.positions[i]
            distance = np.linalg.norm(delta)
            
            if distance > 0:
                direction = delta / distance
                spring_force = self.spring_strength * (distance - self.spring_length) * direction
                self.forces[i] += spring_force
                self.forces[j] -= spring_force
        
        # Repulsion forces (all nodes repel each other)
        for i in range(n):
            for j in range(i + 1, n):
                delta = self.positions[j] - self.positions[i]
                distance = np.linalg.norm(delta)
                
                if distance > 0 and distance < 500:  # Cutoff distance
                    direction = delta / distance
                    repulsion_force = self.repulsion_strength / (distance ** 2) * direction
                    self.forces[i] -= repulsion_force
                    self.forces[j] += repulsion_force
        
        # Centering force (keep nodes near origin)
        center_force = -0.01 * self.positions
        self.forces += center_force
        
    def step_simulation(self):
        """Perform one simulation step"""
        self.calculate_forces()
        
        # Update velocities and positions
        self.velocities += self.forces * self.dt
        self.velocities *= self.damping  # Apply damping
        self.positions += self.velocities * self.dt
        
        self.step_count += 1
        
        # Calculate metrics
        total_energy = self.calculate_total_energy()
        avg_force = np.mean(np.linalg.norm(self.forces, axis=1))
        avg_distance = self.calculate_average_distance()
        
        self.energy_history.append(total_energy)
        self.force_magnitude_history.append(avg_force)
        self.distance_history.append(avg_distance)
        
        # Update status
        self.status_label.config(
            text=f"Step: {self.step_count} | Energy: {total_energy:.2f} | Avg Force: {avg_force:.2f} | Avg Distance: {avg_distance:.2f}"
        )
        
        self.update_visualization()
        
    def calculate_total_energy(self):
        """Calculate total system energy"""
        energy = 0
        
        # Spring potential energy
        for edge in self.structure_data['edges']:
            i, j = edge['source'], edge['target']
            delta = self.positions[j] - self.positions[i]
            distance = np.linalg.norm(delta)
            spring_energy = 0.5 * self.spring_strength * (distance - self.spring_length) ** 2
            energy += spring_energy
        
        # Repulsion potential energy
        n = len(self.positions)
        for i in range(n):
            for j in range(i + 1, n):
                delta = self.positions[j] - self.positions[i]
                distance = np.linalg.norm(delta)
                if distance > 0 and distance < 500:
                    repulsion_energy = self.repulsion_strength / distance
                    energy += repulsion_energy
        
        # Kinetic energy
        kinetic_energy = 0.5 * np.sum(self.velocities ** 2)
        energy += kinetic_energy
        
        return energy
    
    def calculate_average_distance(self):
        """Calculate average distance between connected nodes"""
        if not self.structure_data['edges']:
            return 0
        
        total_distance = 0
        for edge in self.structure_data['edges']:
            i, j = edge['source'], edge['target']
            delta = self.positions[j] - self.positions[i]
            distance = np.linalg.norm(delta)
            total_distance += distance
        
        return total_distance / len(self.structure_data['edges'])
    
    def update_visualization(self):
        """Update both visualization panels"""
        self.update_graph_visualization()
        self.update_force_field_visualization()
        
    def update_graph_visualization(self):
        """Update left panel - graph visualization"""
        self.ax_graph.clear()
        
        # Draw edges
        for edge in self.structure_data['edges']:
            i, j = edge['source'], edge['target']
            x_coords = [self.positions[i, 0], self.positions[j, 0]]
            y_coords = [self.positions[i, 1], self.positions[j, 1]]
            self.ax_graph.plot(x_coords, y_coords, 'gray', alpha=0.6, linewidth=2)
        
        # Draw nodes
        for i, node in enumerate(self.structure_data['nodes']):
            color = self.get_node_color(i)
            self.ax_graph.scatter(self.positions[i, 0], self.positions[i, 1], 
                                c=[color], s=300, edgecolors='black', linewidth=2, zorder=5)
            self.ax_graph.text(self.positions[i, 0], self.positions[i, 1], 
                             node['id'], ha='center', va='center', fontweight='bold', zorder=6)
        
        # Draw force vectors
        for i in range(len(self.positions)):
            if np.linalg.norm(self.forces[i]) > 0.1:
                self.ax_graph.arrow(self.positions[i, 0], self.positions[i, 1],
                                   self.forces[i, 0] * 10, self.forces[i, 1] * 10,
                                   head_width=15, head_length=10, fc='red', ec='red', alpha=0.7)
        
        self.ax_graph.set_xlim(-500, 500)
        self.ax_graph.set_ylim(-500, 500)
        self.ax_graph.set_aspect('equal')
        self.ax_graph.grid(True, alpha=0.3)
        self.ax_graph.set_title(f"Graph Layout (Step {self.step_count})")
        
        self.canvas_graph.draw()
    
    def update_force_field_visualization(self):
        """Update right panel - force field and metrics"""
        self.ax_forces.clear()
        
        # Create force field heatmap
        x = np.linspace(-500, 500, 30)
        y = np.linspace(-500, 500, 30)
        X, Y = np.meshgrid(x, y)
        
        # Calculate force field at each grid point
        force_magnitude = np.zeros_like(X)
        
        for i in range(X.shape[0]):
            for j in range(X.shape[1]):
                pos = np.array([X[i, j], Y[i, j]])
                total_force = 0
                
                # Repulsion from all nodes
                for node_pos in self.positions:
                    delta = pos - node_pos
                    distance = np.linalg.norm(delta)
                    if distance > 0 and distance < 500:
                        total_force += self.repulsion_strength / (distance ** 2)
                
                force_magnitude[i, j] = total_force
        
        # Plot force field
        im = self.ax_forces.contourf(X, Y, force_magnitude, levels=20, cmap='viridis', alpha=0.6)
        
        # Overlay nodes and forces
        for i, node in enumerate(self.structure_data['nodes']):
            # Node position
            self.ax_forces.scatter(self.positions[i, 0], self.positions[i, 1], 
                                  c='white', s=200, edgecolors='black', linewidth=2, zorder=5)
            
            # Force vector
            if np.linalg.norm(self.forces[i]) > 0.1:
                self.ax_forces.arrow(self.positions[i, 0], self.positions[i, 1],
                                   self.forces[i, 0] * 20, self.forces[i, 1] * 20,
                                   head_width=20, head_length=15, fc='red', ec='red', 
                                   linewidth=2, alpha=0.8, zorder=6)
        
        self.ax_forces.set_xlim(-500, 500)
        self.ax_forces.set_ylim(-500, 500)
        self.ax_forces.set_aspect('equal')
        self.ax_forces.set_title("Force Field & Vectors")
        
        # Add energy history subplot
        if len(self.energy_history) > 1:
            ax_energy = self.fig_forces.add_axes([0.15, 0.02, 0.3, 0.15])
            ax_energy.plot(self.energy_history, 'b-', label='Energy')
            ax_energy.set_xlabel('Step')
            ax_energy.set_ylabel('Energy', color='b')
            ax_energy.tick_params(axis='y', labelcolor='b')
            
            ax_force = ax_energy.twinx()
            ax_force.plot(self.force_magnitude_history, 'r-', label='Avg Force')
            ax_force.set_ylabel('Avg Force', color='r')
            ax_force.tick_params(axis='y', labelcolor='r')
            
            ax_distance = self.fig_forces.add_axes([0.55, 0.02, 0.3, 0.15])
            ax_distance.plot(self.distance_history, 'g-', label='Avg Distance')
            ax_distance.set_xlabel('Step')
            ax_distance.set_ylabel('Avg Distance', color='g')
            ax_distance.tick_params(axis='y', labelcolor='g')
        
        self.canvas_forces.draw()
    
    def get_node_color(self, index):
        """Get color for node based on force magnitude"""
        force_mag = np.linalg.norm(self.forces[index])
        max_force = 10.0
        intensity = min(force_mag / max_force, 1.0)
        
        # Color from blue (low force) to red (high force)
        hue = (1.0 - intensity) * 0.67  # 0.67 is blue, 0 is red
        rgb = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        return rgb
    
    def toggle_auto_play(self):
        """Toggle auto-play mode"""
        self.auto_play = not self.auto_play
        if self.auto_play:
            self.auto_play_btn.config(text="Pause")
            self.auto_play_simulation()
        else:
            self.auto_play_btn.config(text="Auto Play")
    
    def auto_play_simulation(self):
        """Auto-play simulation"""
        if self.auto_play:
            self.step_simulation()
            delay = int(1000 / self.fps)
            self.root.after(delay, self.auto_play_simulation)
    
    def reset_simulation(self):
        """Reset simulation to initial state"""
        # Reset to initial positions (circular layout)
        n = len(self.structure_data['nodes'])
        radius = 200
        for i in range(n):
            angle = 2 * np.pi * i / n
            self.positions[i] = [radius * np.cos(angle), radius * np.sin(angle)]
        
        self.velocities = np.zeros_like(self.positions)
        self.forces = np.zeros_like(self.positions)
        self.step_count = 0
        self.energy_history = []
        self.force_magnitude_history = []
        self.distance_history = []
        
        self.update_visualization()
    
    def update_fps(self):
        """Update FPS from input"""
        self.fps = self.fps_var.get()
    
    def update_physics(self):
        """Update physics parameters"""
        self.spring_strength = self.spring_var.get()
        self.repulsion_strength = self.repulsion_var.get()

def main():
    """Test the physics debug visualizer"""
    # Load a structure
    structure_file = "structure_visualizations/simulations/linear_4_nodes.json"
    
    with open(structure_file, 'r') as f:
        structure_data = json.load(f)
    
    # Create initial positions
    n = len(structure_data['nodes'])
    initial_positions = np.zeros((n, 2))
    radius = 200
    for i in range(n):
        angle = 2 * np.pi * i / n
        initial_positions[i] = [radius * np.cos(angle), radius * np.sin(angle)]
    
    # Create GUI
    root = tk.Tk()
    root.geometry("1600x900")
    
    app = PhysicsDebugVisualizer(root, structure_data, initial_positions)
    
    root.mainloop()

if __name__ == "__main__":
    main()