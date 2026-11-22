import React from 'react';
import { X, Command } from 'lucide-react';
import './KeyboardShortcutsModal.css';

export function KeyboardShortcutsModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  const shortcuts = [
    { key: '⌘ / Ctrl + K', description: 'Open Global Command Palette' },
    { key: '⌘ / Ctrl + Shift + F', description: 'Trigger Global Search' },
    { key: 'N', description: 'Quickly create a new task (from anywhere)' },
    { key: '?', description: 'Open this Keyboard Shortcuts cheatsheet' },
    { key: 'Esc', description: 'Close any active modal, dialog, or palette' },
    { key: '↑ / ↓', description: 'Navigate items within the Command Palette' },
    { key: 'Enter', description: 'Execute selected command / Open search result' },
  ];

  return (
    <div className="shortcuts-modal-backdrop" onClick={onClose} role="presentation">
      <div
        className="shortcuts-modal-dialog"
        role="dialog"
        aria-modal="true"
        aria-label="Keyboard Shortcuts"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="shortcuts-modal-header">
          <div className="shortcuts-title-group">
            <Command size={18} className="shortcuts-header-icon" />
            <h2 className="shortcuts-modal-title">Keyboard Shortcuts</h2>
          </div>
          <button
            type="button"
            className="shortcuts-close-btn"
            onClick={onClose}
            aria-label="Close shortcuts modal"
          >
            <X size={18} />
          </button>
        </div>

        <div className="shortcuts-list">
          {shortcuts.map((s, idx) => (
            <div key={idx} className="shortcut-row">
              <span className="shortcut-desc">{s.description}</span>
              <kbd className="shortcut-key-badge">{s.key}</kbd>
            </div>
          ))}
        </div>

        <div className="shortcuts-modal-footer">
          <button type="button" className="shortcuts-done-btn" onClick={onClose}>
            Got it
          </button>
        </div>
      </div>
    </div>
  );
}
