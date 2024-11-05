import React, { useEffect, useState } from 'react';
import BookCarousel from './components/BookCarousel';
import './index.css';

function App() {
  const [images, setImages] = useState([]);

  useEffect(() => {
    // Try to load config.json for when running with Python
    fetch('/config.json')
      .then(response => response.json())
      .then(data => {
        if (data.images && data.images.length > 0) {
          setImages(data.images);
        }
      })
      .catch(error => {
        console.log('Using default images:', error);
      });
  }, []);

  const handleFileUpload = (event) => {
    const files = Array.from(event.target.files);
    const uploadedImages = files.map((file) => ({
      id: Math.random(),
      src: URL.createObjectURL(file),
      alt: file.name
    }));
    setImages(uploadedImages);
  };

  const handleClear = () => {
    // Clear any existing object URLs to prevent memory leaks
    images.forEach(img => {
      if (img.src && img.src.startsWith('blob:')) {
        URL.revokeObjectURL(img.src);
      }
    });
    setImages([]); // This will trigger the default letter cards
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-4">
      <h1 className="text-2xl font-bold text-center mb-4">3D Book Viewer</h1>
      
      {/* File upload and clear buttons */}
      <div className="mb-8 flex justify-center gap-4">
        <label className="bg-blue-500 hover:bg-blue-600 px-4 py-2 rounded-lg cursor-pointer transition-colors">
          <span>Upload Images</span>
          <input
            type="file"
            multiple
            accept="image/*"
            onChange={handleFileUpload}
            className="hidden"
          />
        </label>
        <button
          onClick={handleClear}
          className="bg-red-500 hover:bg-red-600 px-4 py-2 rounded-lg transition-colors"
        >
          Clear Images
        </button>
      </div>

      <BookCarousel images={images} />
    </div>
  );
}

export default App;