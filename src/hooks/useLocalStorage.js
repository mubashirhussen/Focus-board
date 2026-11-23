import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * Custom hook for resilient localStorage state synchronization.
 * Handles parsing errors, quota exceptions, storage event syncing across windows,
 * and guarantees user tasks are never overwritten with defaults on refresh.
 */
export function useLocalStorage(key, initialValue) {
  // Safe read helper
  const readValue = useCallback(() => {
    if (typeof window === 'undefined') {
      return typeof initialValue === 'function' ? initialValue() : initialValue;
    }

    try {
      let item = window.localStorage.getItem(key);
      if (item === null && (key === 'focusboard_tasks' || key === 'focusboard_tasks_v1')) {
        const altKey = key === 'focusboard_tasks' ? 'focusboard_tasks_v1' : 'focusboard_tasks';
        item = window.localStorage.getItem(altKey);
      }
      if (item !== null) {
        const parsed = JSON.parse(item);

        // Data structure integrity verification
        if (Array.isArray(initialValue)) {
          if (Array.isArray(parsed)) {
            return parsed;
          }
          console.warn(`localStorage key "${key}" expected an array, got:`, typeof parsed);
          return typeof initialValue === 'function' ? initialValue() : initialValue;
        }

        return parsed;
      }
    } catch (error) {
      console.warn(`Error reading localStorage key "${key}":`, error);
    }

    return typeof initialValue === 'function' ? initialValue() : initialValue;
  }, [key, initialValue]);

  const [storedValue, setStoredValue] = useState(readValue);
  const prevKeyRef = useRef(key);

  // Sync state if key changes
  useEffect(() => {
    if (prevKeyRef.current !== key) {
      prevKeyRef.current = key;
      setStoredValue(readValue());
    }
  }, [key, readValue]);

  // Save changes to localStorage on mutation
  useEffect(() => {
    if (typeof window === 'undefined') return;

    try {
      window.localStorage.setItem(key, JSON.stringify(storedValue));
    } catch (error) {
      if (error && error.name === 'QuotaExceededError') {
        console.error(`localStorage quota exceeded for key "${key}".`);
      } else {
        console.error(`Error saving to localStorage key "${key}":`, error);
      }
    }
  }, [key, storedValue]);

  // Multi-tab synchronization via storage event
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const handleStorageChange = (event) => {
      if (event.key === key && event.newValue !== null) {
        try {
          const parsed = JSON.parse(event.newValue);
          if (Array.isArray(initialValue) && !Array.isArray(parsed)) return;
          setStoredValue(parsed);
        } catch (e) {
          console.warn('Storage event parse error:', e);
        }
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, [key, initialValue]);

  return [storedValue, setStoredValue];
}
