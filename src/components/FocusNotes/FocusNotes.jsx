import React, { useState, useEffect, useRef } from 'react';
import { ChevronLeft, ChevronRight, Check } from 'lucide-react';
import { focusNotesSlides } from '../../data/focusNotes';
import './FocusNotes.css';

export function FocusNotes() {
  const [currentIndex, setCurrentIndex] = useState(0);
  const containerRef = useRef(null);

  const totalSlides = focusNotesSlides.length;
  const currentSlide = focusNotesSlides[currentIndex];

  const handlePrev = () => {
    setCurrentIndex((prev) => (prev === 0 ? totalSlides - 1 : prev - 1));
  };

  const handleNext = () => {
    setCurrentIndex((prev) => (prev === totalSlides - 1 ? 0 : prev + 1));
  };

  const handleIndicatorClick = (index) => {
    setCurrentIndex(index);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'ArrowLeft') {
      e.preventDefault();
      handlePrev();
    } else if (e.key === 'ArrowRight') {
      e.preventDefault();
      handleNext();
    }
  };

  return (
    <section
      className="focus-notes-carousel"
      aria-label="Focus Notes"
      tabIndex={0}
      onKeyDown={handleKeyDown}
      ref={containerRef}
    >
      <div className="focus-notes-inner">
        {/* Left Content */}
        <div className="focus-notes-content">
          <div className="focus-notes-meta">
            <span className="focus-notes-tag">{currentSlide.tag}</span>
            <span className="focus-notes-counter" aria-live="polite">
              {currentSlide.indexStr}
            </span>
          </div>

          <h2 className="focus-notes-heading">{currentSlide.heading}</h2>
          <p className="focus-notes-subtitle">{currentSlide.subtitle}</p>

          {/* Slide Indicator Bars (Figma matched) */}
          <div className="focus-notes-indicators" role="tablist" aria-label="Slide indicators">
            {focusNotesSlides.map((slide, idx) => (
              <button
                key={slide.id}
                type="button"
                className={`indicator-bar ${idx === currentIndex ? 'active' : ''}`}
                onClick={() => handleIndicatorClick(idx)}
                role="tab"
                aria-selected={idx === currentIndex}
                aria-label={`Go to slide ${idx + 1}`}
              />
            ))}
          </div>
        </div>

        {/* Right Floating Task Card (Figma Reference) */}
        <div className="focus-notes-right">
          <div className="floating-task-card">
            <div className="floating-card-header">
              <span className="floating-check-icon">
                <Check size={13} strokeWidth={3} />
              </span>
              <span className="floating-card-tag">{currentSlide.cardTag}</span>
            </div>
            <div className="floating-card-title">{currentSlide.cardTitle}</div>
            <div className="floating-progress-wrapper">
              <div
                className="floating-progress-track"
                role="progressbar"
                aria-valuenow={currentSlide.progress}
                aria-valuemin={0}
                aria-valuemax={100}
              >
                <div
                  className="floating-progress-fill"
                  style={{ width: `${currentSlide.progress}%` }}
                />
              </div>
              <span className="floating-progress-text">{currentSlide.progress}%</span>
            </div>
          </div>

          {/* Navigation Controls */}
          <div className="focus-notes-controls">
            <button
              type="button"
              className="carousel-nav-btn prev-btn"
              onClick={handlePrev}
              aria-label="Previous slide"
            >
              <ChevronLeft size={18} />
            </button>
            <button
              type="button"
              className="carousel-nav-btn next-btn"
              onClick={handleNext}
              aria-label="Next slide"
            >
              <ChevronRight size={18} />
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
