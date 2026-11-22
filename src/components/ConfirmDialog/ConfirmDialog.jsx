import React, { useEffect, useRef } from 'react';
import { AlertTriangle, X } from 'lucide-react';
import './ConfirmDialog.css';

export function ConfirmDialog({
  isOpen,
  title = 'Delete Task',
  message = 'Are you sure you want to delete this task? This action cannot be undone.',
  confirmLabel = 'Delete',
  cancelLabel = 'Cancel',
  onConfirm,
  onCancel,
}) {
  const cancelBtnRef = useRef(null);

  useEffect(() => {
    if (isOpen) {
      cancelBtnRef.current?.focus();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div
      className="confirm-dialog-backdrop"
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-dialog-title"
    >
      <div className="confirm-dialog-card">
        <div className="confirm-dialog-header">
          <div className="confirm-icon-danger" aria-hidden="true">
            <AlertTriangle size={20} />
          </div>
          <div className="confirm-text-group">
            <h3 id="confirm-dialog-title" className="confirm-dialog-title">
              {title}
            </h3>
            <p className="confirm-dialog-message">{message}</p>
          </div>
        </div>

        <div className="confirm-dialog-actions">
          <button
            type="button"
            ref={cancelBtnRef}
            className="confirm-btn confirm-btn--cancel"
            onClick={onCancel}
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            className="confirm-btn confirm-btn--danger"
            onClick={onConfirm}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
