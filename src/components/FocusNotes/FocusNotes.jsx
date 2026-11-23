import React, { useState, useRef } from 'react';
import { ChevronLeft, ChevronRight, Check, Clock, Sparkles } from 'lucide-react';
import { focusNotesSlides } from '../../data/focusNotes';
import './FocusNotes.css';

export function FocusNotes() {
  const [currentIndex, setCurrentIndex] = useState(0);
  const containerRef = useRef(null);
  const touchStartXRef = useRef(null);

  const totalSlides = focusNotesSlides.length;
  const currentSlide = focusNotesSlides[currentIndex];

  const isFirstSlide = currentIndex === 0;
  const isLastSlide = currentIndex === totalSlides - 1;

  const handlePrev = () => {
    setCurrentIndex((prev) => (prev - 1 + totalSlides) % totalSlides);
  };

  const handleNext = () => {
    setCurrentIndex((prev) => (prev + 1) % totalSlides);
  };

  const handleIndicatorClick = (index) => {
    setCurrentIndex(index);
  };

  // Keyboard navigation (ArrowLeft & ArrowRight)
  const handleKeyDown = (e) => {
    if (e.key === 'ArrowLeft') {
      e.preventDefault();
      handlePrev();
    } else if (e.key === 'ArrowRight') {
      e.preventDefault();
      handleNext();
    }
  };

  // Touch swipe support for mobile
  const handleTouchStart = (e) => {
    touchStartXRef.current = e.touches[0].clientX;
  };

  const handleTouchEnd = (e) => {
    if (touchStartXRef.current === null) return;
    const touchEndX = e.changedTouches[0].clientX;
    const diff = touchStartXRef.current - touchEndX;

    if (Math.abs(diff) > 40) {
      if (diff > 0) {
        // Swiped left -> next
        handleNext();
      } else {
        // Swiped right -> prev
        handlePrev();
      }
    }
    touchStartXRef.current = null;
  };

  return (
    <section
      className="focus-notes-carousel"
      aria-label="Focus Notes carousel"
      tabIndex={0}
      onKeyDown={handleKeyDown}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
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

          {/* Mobile-only inline progress bar matching Figma 390px */}
          <div className="mobile-focus-progress" aria-hidden="true">
            <div className="mobile-progress-track">
              <div
                className="mobile-progress-fill"
                style={{ width: `${currentSlide.progress}%` }}
              />
            </div>
            <span className="mobile-progress-label">{currentSlide.progress}%</span>
          </div>

          {/* Slide Indicator Bars (Figma matched) */}
          <div className="focus-notes-indicators" role="tablist" aria-label="Slide navigation indicators">
            {focusNotesSlides.map((slide, idx) => (
              <button
                key={slide.id}
                type="button"
                className={`indicator-bar ${idx === currentIndex ? 'active' : ''}`}
                onClick={() => handleIndicatorClick(idx)}
                role="tab"
                aria-selected={idx === currentIndex}
                aria-label={`Go to slide ${idx + 1}: ${slide.heading}`}
              />
            ))}
          </div>
        </div>

        {/* Right Section: Desktop Floating Task Card & Navigation Controls */}
        <div className="focus-notes-right">
          <div className="floating-task-card" aria-hidden="true">
            <div className="floating-card-header">
              <span className={`floating-check-icon ${currentSlide.isCompleted ? 'is-done' : ''}`}>
                {currentSlide.isCompleted ? (
                  <Check size={12} strokeWidth={3} />
                ) : (
                  <Clock size={11} strokeWidth={2.5} />
                )}
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
              title="Previous slide"
            >
              <ChevronLeft size={18} />
            </button>
            <button
              type="button"
              className="carousel-nav-btn next-btn"
              onClick={handleNext}
              aria-label="Next slide"
              title="Next slide"
            >
              <ChevronRight size={18} />
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
