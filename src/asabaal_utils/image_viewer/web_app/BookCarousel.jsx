/* index.html */
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Image Viewer</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>

/* main.jsx */
import React from 'react'
import ReactDOM from 'react-dom/client'
import BookCarousel from './BookCarousel'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BookCarousel />
  </React.StrictMode>,
)

/* BookCarousel.jsx */
import React, { useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

const BookCarousel = ({ images = [] }) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [displayMode, setDisplayMode] = useState(2);

  // Default alphabet cards when no images
  const defaultImages = Array.from('ABCDEFGHIJ').map((letter, index) => ({
    id: index,
    src: null,
    alt: `Letter ${letter}`,
    letter
  }));

  const carouselImages = images.length > 0 
    ? images.map((img, index) => ({
        id: index,
        src: img.src || img.url || img,
        alt: img.alt || `Image ${index + 1}`,
      }))
    : defaultImages;

  const next = () => setCurrentIndex((curr) => (curr + 1) % carouselImages.length);
  const prev = () => setCurrentIndex((curr) => (curr - 1 + carouselImages.length) % carouselImages.length);

  const generateLetterSVG = (letter) => (
    <svg viewBox="0 0 100 100" style={{ width: '100%', height: '100%' }}>
      <rect width="100" height="100" fill="#4F46E5" rx="4" ry="4" />
      <text
        x="50"
        y="50"
        dy=".3em"
        fill="white"
        fontSize="60"
        fontWeight="bold"
        textAnchor="middle"
        fontFamily="Arial, sans-serif"
      >
        {letter}
      </text>
    </svg>
  );

  const renderContent = (image) => {
    if (image.src) {
      return (
        <img 
          src={image.src} 
          alt={image.alt} 
          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
        />
      );
    }
    return generateLetterSVG(image.letter);
  };

  const CardWrapper = ({ children, style = {} }) => (
    <div
      style={{
        width: '256px',
        height: '256px',
        border: '2px solid white',
        borderRadius: '8px',
        overflow: 'hidden',
        ...style
      }}
    >
      {children}
    </div>
  );

  const renderImages = () => {
    if (displayMode === 1) {
      return (
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <CardWrapper>
            {renderContent(carouselImages[currentIndex])}
          </CardWrapper>
        </div>
      );
    }
    
    if (displayMode === 2) {
      const nextIndex = (currentIndex + 1) % carouselImages.length;
      return (
        <div style={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center',
          gap: '4px'
        }}>
          <CardWrapper
            style={{
              transform: 'perspective(1000px) rotateY(-30deg)',
              transformOrigin: 'right center',
            }}
          >
            {renderContent(carouselImages[currentIndex])}
          </CardWrapper>
          
          <CardWrapper
            style={{
              transform: 'perspective(1000px) rotateY(30deg)',
              transformOrigin: 'left center',
            }}
          >
            {renderContent(carouselImages[nextIndex])}
          </CardWrapper>
        </div>
      );
    }
    
    // Three image mode
    const prevIndex = (currentIndex - 1 + carouselImages.length) % carouselImages.length;
    const nextIndex = (currentIndex + 1) % carouselImages.length;
    
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
        <div style={{ position: 'relative' }}>
          <CardWrapper
            style={{
              position: 'absolute',
              left: '-280px',
              transform: 'perspective(1000px) rotateY(-30deg)',
              opacity: 0.7,
            }}
          >
            {renderContent(carouselImages[prevIndex])}
          </CardWrapper>
          
          <CardWrapper>
            {renderContent(carouselImages[currentIndex])}
          </CardWrapper>
          
          <CardWrapper
            style={{
              position: 'absolute',
              right: '-280px',
              transform: 'perspective(1000px) rotateY(30deg)',
              opacity: 0.7,
            }}
          >
            {renderContent(carouselImages[nextIndex])}
          </CardWrapper>
        </div>
      </div>
    );
  };

  const handleFileUpload = (event) => {
    const files = Array.from(event.target.files);
    const uploadedImages = files.map((file) => ({
      id: Math.random(),
      src: URL.createObjectURL(file),
      alt: file.name
    }));
    setCurrentIndex(0);
    images.length = 0;
    images.push(...uploadedImages);
  };

  const handleClear = () => {
    images.forEach(img => {
      if (img.src && img.src.startsWith('blob:')) {
        URL.revokeObjectURL(img.src);
      }
    });
    images.length = 0;
    setCurrentIndex(0);
  };

  const buttonStyle = {
    padding: '8px 16px',
    borderRadius: '4px',
    cursor: 'pointer',
    border: 'none',
    color: 'white',
  };

  return (
    <div style={{ 
      width: '100%', 
      maxWidth: '1200px', 
      margin: '0 auto', 
      padding: '32px' 
    }}>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        gap: '16px',
        marginBottom: '32px' 
      }}>
        {[1, 2, 3].map((num) => (
          <button
            key={num}
            onClick={() => setDisplayMode(num)}
            style={{
              ...buttonStyle,
              backgroundColor: displayMode === num ? '#3B82F6' : '#9CA3AF',
            }}
          >
            Show {num} {num === 1 ? 'Image' : 'Images'}
          </button>
        ))}
      </div>

      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        gap: '16px',
        marginBottom: '32px' 
      }}>
        <label style={{ ...buttonStyle, backgroundColor: '#3B82F6' }}>
          <span>Upload Images</span>
          <input
            type="file"
            multiple
            accept="image/*"
            onChange={handleFileUpload}
            style={{ display: 'none' }}
          />
        </label>
        <button
          onClick={handleClear}
          style={{ ...buttonStyle, backgroundColor: '#EF4444' }}
        >
          Clear Images
        </button>
      </div>

      <div style={{ 
        position: 'relative', 
        height: '384px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <button
          onClick={prev}
          style={{
            position: 'absolute',
            left: '16px',
            zIndex: 20,
            padding: '8px',
            backgroundColor: 'white',
            borderRadius: '50%',
            border: 'none',
            cursor: 'pointer',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          }}
          aria-label="Previous"
        >
          <ChevronLeft style={{ width: '24px', height: '24px' }} />
        </button>

        {renderImages()}

        <button
          onClick={next}
          style={{
            position: 'absolute',
            right: '16px',
            zIndex: 20,
            padding: '8px',
            backgroundColor: 'white',
            borderRadius: '50%',
            border: 'none',
            cursor: 'pointer',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          }}
          aria-label="Next"
        >
          <ChevronRight style={{ width: '24px', height: '24px' }} />
        </button>
      </div>

      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        gap: '8px',
        marginTop: '16px' 
      }}>
        {carouselImages.map((_, index) => (
          <button
            key={index}
            onClick={() => setCurrentIndex(index)}
            style={{
              width: index === currentIndex ? '16px' : '8px',
              height: '8px',
              borderRadius: '9999px',
              backgroundColor: index === currentIndex ? '#3B82F6' : '#D1D5DB',
              border: 'none',
              padding: 0,
              cursor: 'pointer',
              transition: 'all 300ms',
            }}
            aria-label={`Go to image ${index + 1}`}
          />
        ))}
      </div>
    </div>
  );
};

export default BookCarousel;