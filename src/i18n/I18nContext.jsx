import React, { createContext, useContext, useState, useEffect } from 'react';
import { translations } from './translations';
import { regionalApi } from '../services/regionalApi';

const I18nContext = createContext(null);

export function I18nProvider({ children }) {
  const [language, setLanguageState] = useState(() => localStorage.getItem('focusboard_lang') || 'en');
  const [timezone, setTimezoneState] = useState(() => localStorage.getItem('focusboard_tz') || 'Asia/Kolkata');
  const [currency, setCurrencyState] = useState(() => localStorage.getItem('focusboard_currency') || 'USD');
  const [dateFormat, setDateFormatState] = useState(() => localStorage.getItem('focusboard_date_fmt') || 'YYYY-MM-DD');
  const [timeFormat, setTimeFormatState] = useState(() => localStorage.getItem('focusboard_time_fmt') || '12h');
  const [direction, setDirectionState] = useState('ltr');

  // Load from backend if available
  useEffect(() => {
    regionalApi
      .getSettings()
      .then((data) => {
        if (data) {
          if (data.language) setLanguageState(data.language);
          if (data.timezone) setTimezoneState(data.timezone);
          if (data.currency) setCurrencyState(data.currency);
          if (data.date_format) setDateFormatState(data.date_format);
          if (data.time_format) setTimeFormatState(data.time_format);
          if (data.direction) setDirectionState(data.direction);
        }
      })
      .catch(() => {
        // Fallback to local storage / browser defaults
      });
  }, []);

  // Update HTML direction when language/direction changes
  useEffect(() => {
    const isRtl = language === 'ar' || direction === 'rtl';
    const newDir = isRtl ? 'rtl' : 'ltr';
    setDirectionState(newDir);
    document.documentElement.setAttribute('dir', newDir);
    document.documentElement.setAttribute('lang', language);
    localStorage.setItem('focusboard_lang', language);
  }, [language, direction]);

  const setLanguage = (lang) => {
    setLanguageState(lang);
    localStorage.setItem('focusboard_lang', lang);
    regionalApi.updateSettings({ language: lang }).catch(() => {});
  };

  const setTimezone = (tz) => {
    setTimezoneState(tz);
    localStorage.setItem('focusboard_tz', tz);
    regionalApi.updateSettings({ timezone: tz }).catch(() => {});
  };

  const setCurrency = (curr) => {
    setCurrencyState(curr);
    localStorage.setItem('focusboard_currency', curr);
    regionalApi.updateSettings({ currency: curr }).catch(() => {});
  };

  const setDateFormat = (fmt) => {
    setDateFormatState(fmt);
    localStorage.setItem('focusboard_date_fmt', fmt);
    regionalApi.updateSettings({ date_format: fmt }).catch(() => {});
  };

  const setTimeFormat = (fmt) => {
    setTimeFormatState(fmt);
    localStorage.setItem('focusboard_time_fmt', fmt);
    regionalApi.updateSettings({ time_format: fmt }).catch(() => {});
  };

  // Translation function: t(key, fallback)
  const t = (key, fallback = '') => {
    const dict = translations[language] || translations['en'];
    return dict[key] || translations['en']?.[key] || fallback || key;
  };

  // Locale-aware formatting functions
  const formatCurrency = (amount) => {
    try {
      const locale = language === 'hi' ? 'en-IN' : language === 'ar' ? 'ar-AE' : 'en-US';
      return new Intl.NumberFormat(locale, {
        style: 'currency',
        currency: currency,
        maximumFractionDigits: 2,
      }).format(amount);
    } catch (e) {
      return `${currency} ${amount}`;
    }
  };

  const formatDate = (dateInput) => {
    if (!dateInput) return '';
    try {
      const d = typeof dateInput === 'string' ? new Date(dateInput) : dateInput;
      if (isNaN(d.getTime())) return String(dateInput);

      if (dateFormat === 'DD/MM/YYYY') {
        const day = String(d.getDate()).padStart(2, '0');
        const month = String(d.getMonth() + 1).padStart(2, '0');
        return `${day}/${month}/${d.getFullYear()}`;
      } else if (dateFormat === 'MM/DD/YYYY') {
        const day = String(d.getDate()).padStart(2, '0');
        const month = String(d.getMonth() + 1).padStart(2, '0');
        return `${month}/${day}/${d.getFullYear()}`;
      } else {
        return d.toISOString().split('T')[0];
      }
    } catch (e) {
      return String(dateInput);
    }
  };

  const formatTime = (dateInput) => {
    if (!dateInput) return '';
    try {
      const d = typeof dateInput === 'string' ? new Date(dateInput) : dateInput;
      return new Intl.DateTimeFormat(language === 'ar' ? 'ar-AE' : 'en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: timeFormat === '12h',
        timeZone: timezone,
      }).format(d);
    } catch (e) {
      return '';
    }
  };

  const formatNumber = (num) => {
    try {
      const locale = language === 'hi' ? 'en-IN' : language === 'ar' ? 'ar-AE' : 'en-US';
      return new Intl.NumberFormat(locale).format(num);
    } catch (e) {
      return String(num);
    }
  };

  return (
    <I18nContext.Provider
      value={{
        t,
        language,
        setLanguage,
        timezone,
        setTimezone,
        currency,
        setCurrency,
        dateFormat,
        setDateFormat,
        timeFormat,
        setTimeFormat,
        direction,
        formatCurrency,
        formatDate,
        formatTime,
        formatNumber,
      }}
    >
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error('useI18n must be used within an I18nProvider');
  }
  return context;
}
