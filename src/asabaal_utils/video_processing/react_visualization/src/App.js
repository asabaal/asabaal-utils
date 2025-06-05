import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import ProjectOverview from './components/ProjectOverview/ProjectOverview';
import MediaExplorer from './components/MediaExplorer/MediaExplorer';
import TimelineVisualizer from './components/TimelineVisualizer/TimelineVisualizer';
import StructureExplorer from './components/StructureExplorer/StructureExplorer';
import './App.css';

function App() {
  const [projectData, setProjectData] = useState(null);
  const [mediaInfo, setMediaInfo] = useState({ all_items: [], total_count: 0, type_counts: {} });
  const [timelineInfo, setTimelineInfo] = useState({ tracks: [], clips: [], total_tracks: 0, total_clips: 0 });
  const [relationshipInfo, setRelationshipInfo] = useState({ relationships: [], unused_media: [] });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Function to analyze a project file
  const analyzeProject = async (file) => {
    setLoading(true);
    setError(null);
    
    try {
      // In a real implementation, this would be an API call to the Python backend
      // For now, we'll simulate the response
      const formData = new FormData();
      formData.append('project_file', file);
      
      // Simulated API response - in production, this would be:
      // const response = await fetch('/api/analyze-project', { method: 'POST', body: formData });
      // const data = await response.json();
      
      // Simulate processing time
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Mock data - would come from backend in real implementation
      const data = {
        // Project structure data would be here
        media_info: {
          all_items: [
            { id: 'video1', name: 'interview.mp4', path: '/videos/interview.mp4', type: 'video', duration: 120 },
            { id: 'video2', name: 'b-roll.mp4', path: '/videos/b-roll.mp4', type: 'video', duration: 45 },
            { id: 'audio1', name: 'background.mp3', path: '/audio/background.mp3', type: 'audio', duration: 180 },
            { id: 'image1', name: 'logo.png', path: '/images/logo.png', type: 'image' }
          ],
          total_count: 4,
          type_counts: { video: 2, audio: 1, image: 1 }
        },
        timeline_info: {
          tracks: [
            { id: 'track1', index: 0, type: 'video' },
            { id: 'track2', index: 1, type: 'audio' }
          ],
          clips: [
            { 
              id: 'clip1', 
              track_id: 'track1', 
              track_index: 0, 
              clip_index: 0, 
              material_id: 'video1',
              timeline_start: 0,
              timeline_duration: 15000000 // in microseconds
            },
            { 
              id: 'clip2', 
              track_id: 'track1', 
              track_index: 0, 
              clip_index: 1, 
              material_id: 'video2',
              timeline_start: 15000000,
              timeline_duration: 10000000 
            },
            { 
              id: 'clip3', 
              track_id: 'track2', 
              track_index: 1, 
              clip_index: 0, 
              material_id: 'audio1',
              timeline_start: 0,
              timeline_duration: 25000000 
            }
          ],
          total_tracks: 2,
          total_clips: 3
        },
        relationships: {
          relationships: [
            { source: 'video1', target: 'clip1', type: 'media_to_clip', source_type: 'id' },
            { source: 'video2', target: 'clip2', type: 'media_to_clip', source_type: 'id' },
            { source: 'audio1', target: 'clip3', type: 'media_to_clip', source_type: 'id' }
          ],
          unused_media: [
            { id: 'image1', name: 'logo.png', path: '/images/logo.png', type: 'image' }
          ]
        }
      };
      
      setProjectData(data);
      setMediaInfo(data.media_info);
      setTimelineInfo(data.timeline_info);
      setRelationshipInfo(data.relationships);
    } catch (err) {
      setError('Failed to analyze project: ' + err.message);
      console.error('Error analyzing project:', err);
    } finally {
      setLoading(false);
    }
  };

  // Function to handle file upload
  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      analyzeProject(file);
    }
  };

  return (
    <Router>
      <div className="app">
        <header className="app-header">
          <nav className="navbar navbar-expand-lg navbar-dark">
            <div className="container-fluid">
              <Link className="navbar-brand" to="/">
                <i className="fas fa-project-diagram me-2"></i>
                CapCut Project Explorer
              </Link>
              <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span className="navbar-toggler-icon"></span>
              </button>
              <div className="collapse navbar-collapse" id="navbarNav">
                <ul className="navbar-nav">
                  <li className="nav-item">
                    <Link className="nav-link" to="/">Overview</Link>
                  </li>
                  <li className="nav-item">
                    <Link className="nav-link" to="/media">Media</Link>
                  </li>
                  <li className="nav-item">
                    <Link className="nav-link" to="/timeline">Timeline</Link>
                  </li>
                  <li className="nav-item">
                    <Link className="nav-link" to="/structure">Structure</Link>
                  </li>
                </ul>
              </div>
              
              {/* File upload input */}
              <div className="d-flex">
                <input 
                  type="file" 
                  className="form-control form-control-sm me-2" 
                  accept=".json" 
                  onChange={handleFileUpload} 
                  disabled={loading}
                />
                {loading && (
                  <div className="spinner-border spinner-border-sm text-light" role="status">
                    <span className="visually-hidden">Loading...</span>
                  </div>
                )}
              </div>
            </div>
          </nav>
        </header>

        <main className="app-content container-fluid">
          {error && (
            <div className="alert alert-danger mt-3">
              {error}
            </div>
          )}

          {!projectData && !loading && (
            <div className="upload-prompt card mt-5">
              <div className="card-body text-center">
                <h5 className="card-title">Upload a CapCut Project File</h5>
                <p className="card-text">
                  Select a CapCut project file (draft_content.json) to start analyzing.
                </p>
                <input 
                  type="file" 
                  className="form-control mx-auto" 
                  style={{ maxWidth: '400px' }}
                  accept=".json" 
                  onChange={handleFileUpload}
                />
              </div>
            </div>
          )}

          {projectData && (
            <Routes>
              <Route 
                path="/" 
                element={
                  <ProjectOverview 
                    mediaInfo={mediaInfo} 
                    timelineInfo={timelineInfo} 
                    relationshipInfo={relationshipInfo} 
                  />
                } 
              />
              <Route 
                path="/media" 
                element={
                  <MediaExplorer 
                    mediaInfo={mediaInfo} 
                    relationshipInfo={relationshipInfo} 
                  />
                } 
              />
              <Route 
                path="/timeline" 
                element={
                  <TimelineVisualizer 
                    timelineInfo={timelineInfo} 
                    mediaInfo={mediaInfo}
                  />
                } 
              />
              <Route 
                path="/structure" 
                element={
                  <StructureExplorer 
                    projectData={projectData} 
                  />
                } 
              />
            </Routes>
          )}
        </main>

        <footer className="app-footer text-center py-3">
          <div className="container">
            <span className="text-muted">
              CapCut Project Visualizer • Built with React
            </span>
          </div>
        </footer>
      </div>
    </Router>
  );
}

export default App;