import { useEffect } from 'react';

/**
 * Global Keyboard Shortcut Hook
 * Handles Cmd/Ctrl+K, Cmd/Ctrl+Shift+F, 'N' for new task, '?' for shortcuts dialog, and Escape.
 */
export function useKeyboardShortcuts({
  onToggleCommandPalette,
  onOpenSearch,
  onNewTask,
  onToggleShortcutsModal,
  onEscape,
}) {
  useEffect(() => {
    const handleKeyDown = (e) => {
      const isInput = ['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement?.tagName) ||
                      document.activeElement?.isContentEditable;

      const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
      const cmdOrCtrl = isMac ? e.metaKey : e.ctrlKey;

      // 1. Cmd/Ctrl + Shift + F -> Global Search
      if (cmdOrCtrl && e.shiftKey && e.key.toLowerCase() === 'f') {
        e.preventDefault();
        onOpenSearch?.();
        return;
      }

      // 2. Cmd/Ctrl + K -> Command Palette
      if (cmdOrCtrl && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        onToggleCommandPalette?.();
        return;
      }

      // 3. Escape -> Dismiss Modals / Palettes
      if (e.key === 'Escape') {
        onEscape?.();
        return;
      }

      // Skip single-key shortcuts when typing inside form inputs
      if (isInput) return;

      // 4. 'N' -> Quick Create Task
      if (e.key === 'n' || e.key === 'N') {
        e.preventDefault();
        onNewTask?.();
        return;
      }

      // 5. '?' -> Open Shortcut Cheatsheet
      if (e.key === '?') {
        e.preventDefault();
        onToggleShortcutsModal?.();
        return;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onToggleCommandPalette, onOpenSearch, onNewTask, onToggleShortcutsModal, onEscape]);
}
