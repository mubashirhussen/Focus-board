import React from 'react';
import { X } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { AuthFlow } from './AuthFlow';
import './AuthModal.css';

export function AuthModal() {
  const { isAuthModalOpen, closeAuthModal } = useAuth();

  if (!isAuthModalOpen) return null;

  return (
    <div
      className="auth-modal-backdrop"
      onClick={closeAuthModal}
      role="dialog"
      aria-modal="true"
      aria-label="FocusBoard Authentication"
    >
      <div className="auth-modal-card-wrap" onClick={(e) => e.stopPropagation()}>
        <button
          type="button"
          className="auth-modal-close"
          onClick={closeAuthModal}
          aria-label="Close authentication modal"
        >
          <X size={18} />
        </button>
        <AuthFlow onSuccess={closeAuthModal} onCancel={closeAuthModal} />
      </div>
    </div>
  );
}
