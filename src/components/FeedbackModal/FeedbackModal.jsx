import React, { useState } from 'react';
import { Star, MessageSquare, Check, X, Send } from 'lucide-react';
import { growthApi } from '../../services/growthApi';
import './FeedbackModal.css';

export default function FeedbackModal({ isOpen, onClose }) {
  const [category, setCategory] = useState('feature_request');
  const [rating, setRating] = useState(5);
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!description.trim()) return;

    setSubmitting(true);
    try {
      await growthApi.submitFeedback({
        category,
        rating,
        description,
      });
      growthApi.trackEvent('feedback_submitted', { category, rating });
      setSubmitted(true);
      setTimeout(() => {
        setSubmitted(false);
        setDescription('');
        onClose();
      }, 1500);
    } catch (err) {
      console.error('Error submitting feedback:', err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="feedback-overlay" role="dialog" aria-modal="true" aria-labelledby="feedback-title">
      <div className="feedback-card">
        <button className="feedback-close-btn" onClick={onClose} aria-label="Close feedback modal">
          <X size={18} />
        </button>

        <div className="feedback-header">
          <div className="feedback-badge">
            <MessageSquare size={14} />
            <span>Product Feedback</span>
          </div>
          <h2 id="feedback-title">Help us improve FocusBoard</h2>
          <p className="feedback-subtext">Share your thoughts, report issues, or request new features directly with our team.</p>
        </div>

        {submitted ? (
          <div className="feedback-success">
            <div className="feedback-success-icon">
              <Check size={28} />
            </div>
            <h3>Thank you for your feedback!</h3>
            <p>Your suggestions directly shape our product roadmap.</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="feedback-form">
            <div className="feedback-field">
              <label>Feedback Category</label>
              <select value={category} onChange={(e) => setCategory(e.target.value)}>
                <option value="feature_request">Feature Request / Enhancement</option>
                <option value="bug_report">Bug Report / Issue</option>
                <option value="ux_improvement">User Experience / Design</option>
                <option value="general">General Compliment or Thought</option>
              </select>
            </div>

            <div className="feedback-field">
              <label>How satisfied are you with FocusBoard?</label>
              <div className="feedback-rating-stars">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    className={`star-btn ${star <= rating ? 'active' : ''}`}
                    onClick={() => setRating(star)}
                    aria-label={`Rate ${star} star`}
                  >
                    <Star size={22} fill={star <= rating ? 'currentColor' : 'none'} />
                  </button>
                ))}
              </div>
            </div>

            <div className="feedback-field">
              <label htmlFor="feedback-desc">Your Notes or Request</label>
              <textarea
                id="feedback-desc"
                rows={4}
                placeholder="What worked well, or what could be better?"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                required
              />
            </div>

            <div className="feedback-footer">
              <button type="button" className="feedback-cancel-btn" onClick={onClose}>
                Cancel
              </button>
              <button
                type="submit"
                className="feedback-submit-btn"
                disabled={submitting || !description.trim()}
              >
                {submitting ? 'Submitting...' : 'Send Feedback'}
                <Send size={15} />
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
