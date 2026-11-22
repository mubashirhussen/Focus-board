import React from 'react';
import './StatCard.css';

export function StatCard({
  icon: Icon,
  label,
  value,
  subtitle,
  variant = 'default',
  onClick,
  active = false,
}) {
  return (
    <div
      className={`stat-card stat-card--${variant} ${active ? 'is-active' : ''} ${
        onClick ? 'is-clickable' : ''
      }`}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={(e) => {
        if (onClick && (e.key === 'Enter' || e.key === ' ')) {
          e.preventDefault();
          onClick();
        }
      }}
      aria-label={`${label}: ${value} ${subtitle ? `(${subtitle})` : ''}`}
    >
      <div className="stat-card__header">
        <div className="stat-card__icon-wrapper" aria-hidden="true">
          <Icon size={20} />
        </div>
        <span className="stat-card__label">{label}</span>
      </div>
      <div className="stat-card__body">
        <span className="stat-card__value">{value}</span>
        {subtitle && <span className="stat-card__subtitle">{subtitle}</span>}
      </div>
    </div>
  );
}
