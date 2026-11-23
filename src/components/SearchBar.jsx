import React from 'react';
import { Search, X } from 'lucide-react';
import { useTasks } from '../hooks/useTasks';
import './TaskFilters/TaskFilters.css';

/**
 * Reusable SearchBar Component (Step 12 in Implementation Guide)
 * Supports case-insensitive searching, partial keyword match, and instant clear button.
 * Can be used with explicit props or default to useTasks context.
 */
export function SearchBar({ value, onChange, onClear, placeholder = 'Search tasks...' }) {
  let contextSearch = '';
  let setContextSearch = null;

  try {
    const tasksContext = useTasks();
    if (tasksContext) {
      contextSearch = tasksContext.searchQuery;
      setContextSearch = tasksContext.setSearchQuery;
    }
  } catch {
    // Standalone usage outside TaskProvider
  }

  const query = value !== undefined ? value : contextSearch;
  const handleChange = (e) => {
    if (onChange) {
      onChange(e);
    } else if (setContextSearch) {
      setContextSearch(e.target.value);
    }
  };

  const handleClear = () => {
    if (onClear) {
      onClear();
    } else if (onChange) {
      onChange({ target: { value: '' } });
    } else if (setContextSearch) {
      setContextSearch('');
    }
  };

  return (
    <div className="search-input-wrapper" role="search">
      <Search className="search-icon" size={16} aria-hidden="true" />
      <input
        type="text"
        className="search-field"
        placeholder={placeholder}
        value={query}
        onChange={handleChange}
        aria-label="Search tasks by title"
      />
      {query && (
        <button
          type="button"
          className="clear-search-btn"
          onClick={handleClear}
          aria-label="Clear search query"
        >
          <X size={14} />
        </button>
      )}
    </div>
  );
}

export default SearchBar;
