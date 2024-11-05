import React, { useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

const BookCarousel = ({ images = [] }) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [displayMode, setDisplayMode] = useState(2);
  
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
    <svg viewBox="0 0 100 100" className="w-full h-full">
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
          className="w-full h-full object-cover"
        />
      );
    }
    return generateLetterSVG(image.letter);
  };

  const renderImages = () => {
    if (displayMode === 1) {
      return (
        <div className="flex justify-center">
          <div className="w-64 h-64 border-2 border-white rounded-lg overflow-hidden">
            {renderContent(carouselImages[currentIndex])}
          </div>
        </div>
      );
    }
    
    if (displayMode === 2) {
      const nextIndex = (currentIndex + 1) % carouselImages.length;
      return (
        <div className="flex justify-center items-center">
          <div className="flex -space-x-4">
            <div 
              className="w-64 h-64 border-2 border-white rounded-lg overflow-hidden transform-gpu transition-transform duration-500"
              style={{
                transform: 'perspective(1000px) translateX(32px) rotateY(-30deg)',
                transformOrigin: 'right center',
              }}
            >
              {renderContent(carouselImages[currentIndex])}
            </div>
            <div 
              className="w-64 h-64 border-2 border-white rounded-lg overflow-hidden transform-gpu transition-transform duration-500"
              style={{
                transform: 'perspective(1000px) translateX(-32px) rotateY(30deg)',
                transformOrigin: 'left center',
              }}
            >
              {renderContent(carouselImages[nextIndex])}
            </div>
          </div>
        </div>
      );
    }
    
    // Three image mode
    const prevIndex = (currentIndex - 1 + carouselImages.length) % carouselImages.length;
    const nextIndex = (currentIndex + 1) % carouselImages.length;
    
    return (
      <div className="flex justify-center items-center">
        <div className="relative flex justify-center">
          <div 
            className="absolute w-64 h-64 border-2 border-white rounded-lg overflow-hidden transform-gpu transition-transform duration-500"
            style={{
              transform: 'perspective(1000px) translateX(-160px) rotateY(-30deg)',
              opacity: 0.7,
              zIndex: 0,
            }}
          >
            {renderContent(carouselImages[prevIndex])}
          </div>
          
          <div 
            className="w-64 h-64 border-2 border-white rounded-lg overflow-hidden transform-gpu transition-transform duration-500"
            style={{
              zIndex: 1,
            }}
          >
            {renderContent(carouselImages[currentIndex])}
          </div>
          
          <div 
            className="absolute w-64 h-64 border-2 border-white rounded-lg overflow-hidden transform-gpu transition-transform duration-500"
            style={{
              transform: 'perspective(1000px) translateX(160px) rotateY(30deg)',
              opacity: 0.7,
              zIndex: 0,
            }}
          >
            {renderContent(carouselImages[nextIndex])}
          </div>
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

  return (
    <div className="w-full max-w-4xl mx-auto p-8">
      <div className="flex justify-center gap-4 mb-8">
        {[1, 2, 3].map((num) => (
          <button
            key={num}
            onClick={() => setDisplayMode(num)}
            className={`px-4 py-2 rounded transition-colors ${
              displayMode === num 
                ? 'bg-blue-500 text-white' 
                : 'bg-gray-200 hover:bg-gray-300'
            }`}
          >
            Show {num} {num === 1 ? 'Image' : 'Images'}
          </button>
        ))}
      </div>

      <div className="mb-8 flex justify-center gap-4">
        <label className="bg-blue-500 hover:bg-blue-600 px-4 py-2 rounded cursor-pointer text-white">
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
          className="bg-red-500 hover:bg-red-600 px-4 py-2 rounded text-white"
        >
          Clear Images
        </button>
      </div>

      <div className="relative h-96 flex items-center justify-center">
        <button
          onClick={prev}
          className="absolute left-4 z-20 p-2 bg-white rounded-full shadow-lg hover:bg-gray-100"
          aria-label="Previous"
        >
          <ChevronLeft className="w-6 h-6" />
        </button>

        <div className="flex-1 flex justify-center items-center">
          {renderImages()}
        </div>

        <button
          onClick={next}
          className="absolute right-4 z-20 p-2 bg-white rounded-full shadow-lg hover:bg-gray-100"
          aria-label="Next"
        >
          <ChevronRight className="w-6 h-6" />
        </button>
      </div>

      <div className="flex justify-center gap-2 mt-4">
        {carouselImages.map((_, index) => (
          <button
            key={index}
            onClick={() => setCurrentIndex(index)}
            className={`w-2 h-2 rounded-full transition-all duration-300 ${
              index === currentIndex ? 'bg-blue-500 w-4' : 'bg-gray-300'
            }`}
            aria-label={`Go to image ${index + 1}`}
          />
        ))}
      </div>
    </div>
  );
};

export default BookCarousel;