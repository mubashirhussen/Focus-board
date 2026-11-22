import React, { useState, useEffect } from 'react';
import { Globe, DollarSign, Clock, Calendar, Check, Save } from 'lucide-react';
import { useI18n } from '../../i18n/I18nContext';
import { regionalApi } from '../../services/regionalApi';
import './RegionalSettingsPage.css';

export default function RegionalSettingsPage() {
  const {
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
  } = useI18n();

  const [localesCatalog, setLocalesCatalog] = useState(null);
  const [savedNotice, setSavedNotice] = useState(false);

  useEffect(() => {
    regionalApi.getLocales().then(setLocalesCatalog).catch(() => {});
  }, []);

  const handleLanguageChange = (e) => {
    const val = e.target.value;
    setLanguage(val);
    triggerSaved();
  };

  const handleCurrencyChange = (e) => {
    const val = e.target.value;
    setCurrency(val);
    triggerSaved();
  };

  const handleTimezoneChange = (e) => {
    const val = e.target.value;
    setTimezone(val);
    triggerSaved();
  };

  const handleDateFormatChange = (e) => {
    const val = e.target.value;
    setDateFormat(val);
    triggerSaved();
  };

  const handleTimeFormatChange = (e) => {
    const val = e.target.value;
    setTimeFormat(val);
    triggerSaved();
  };

  const triggerSaved = () => {
    setSavedNotice(true);
    setTimeout(() => setSavedNotice(false), 2000);
  };

  const sampleDate = new Date();

  return (
    <div className="regional-page-container">
      <div className="regional-page-header">
        <h1>{t('regional.title')}</h1>
        <p className="regional-page-sub">{t('regional.subtitle')}</p>
      </div>

      {savedNotice && (
        <div className="saved-notification-toast">
          <Check size={16} />
          <span>{t('regional.saved')}</span>
        </div>
      )}

      <div className="regional-settings-grid">
        {/* Settings Controls Form */}
        <div className="regional-form-card">
          <div className="form-section-header">
            <Globe size={18} />
            <h3>Language & Layout Direction</h3>
          </div>

          <div className="regional-form-group">
            <label htmlFor="select-lang">{t('regional.language')}</label>
            <select id="select-lang" value={language} onChange={handleLanguageChange}>
              <option value="en">English (US / UK / Global)</option>
              <option value="hi">हिन्दी - Hindi (India)</option>
              <option value="te">తెలుగు - Telugu (India)</option>
              <option value="ar">العربية - Arabic (Middle East - RTL)</option>
            </select>
            <span className="field-hint">
              Direction: <strong>{direction.toUpperCase()}</strong> ({direction === 'rtl' ? 'Right to Left' : 'Left to Right'})
            </span>
          </div>

          <div className="form-section-header" style={{ marginTop: '1.5rem' }}>
            <DollarSign size={18} />
            <h3>{t('regional.currency')}</h3>
          </div>

          <div className="regional-form-group">
            <label htmlFor="select-curr">Currency</label>
            <select id="select-curr" value={currency} onChange={handleCurrencyChange}>
              <option value="USD">$ USD - United States Dollar</option>
              <option value="INR">₹ INR - Indian Rupee</option>
              <option value="EUR">€ EUR - Euro</option>
              <option value="GBP">£ GBP - British Pound</option>
              <option value="AED">د.إ AED - UAE Dirham</option>
              <option value="JPY">¥ JPY - Japanese Yen</option>
            </select>
          </div>

          <div className="form-section-header" style={{ marginTop: '1.5rem' }}>
            <Clock size={18} />
            <h3>Timezone & Clock Format</h3>
          </div>

          <div className="regional-form-group">
            <label htmlFor="select-tz">{t('regional.timezone')}</label>
            <select id="select-tz" value={timezone} onChange={handleTimezoneChange}>
              {localesCatalog?.timezones ? (
                localesCatalog.timezones.map((tz) => (
                  <option key={tz} value={tz}>
                    {tz}
                  </option>
                ))
              ) : (
                <>
                  <option value="Asia/Kolkata">Asia/Kolkata (IST +5:30)</option>
                  <option value="UTC">UTC (Coordinated Universal Time)</option>
                  <option value="America/New_York">America/New_York (EST/EDT)</option>
                  <option value="Europe/London">Europe/London (GMT/BST)</option>
                  <option value="Asia/Dubai">Asia/Dubai (GST +4:00)</option>
                </>
              )}
            </select>
          </div>

          <div className="regional-form-group">
            <label htmlFor="select-time-fmt">{t('regional.time_format')}</label>
            <select id="select-time-fmt" value={timeFormat} onChange={handleTimeFormatChange}>
              <option value="12h">12-hour AM/PM (e.g. 2:30 PM)</option>
              <option value="24h">24-hour Military (e.g. 14:30)</option>
            </select>
          </div>

          <div className="form-section-header" style={{ marginTop: '1.5rem' }}>
            <Calendar size={18} />
            <h3>Calendar & Date Representation</h3>
          </div>

          <div className="regional-form-group">
            <label htmlFor="select-date-fmt">{t('regional.date_format')}</label>
            <select id="select-date-fmt" value={dateFormat} onChange={handleDateFormatChange}>
              <option value="YYYY-MM-DD">YYYY-MM-DD (ISO 8601 standard)</option>
              <option value="DD/MM/YYYY">DD/MM/YYYY (UK / India / Europe)</option>
              <option value="MM/DD/YYYY">MM/DD/YYYY (US standard)</option>
            </select>
          </div>
        </div>

        {/* Live Preview Card */}
        <div className="regional-preview-card">
          <h3>Live Localization Preview</h3>
          <p className="preview-subtext">
            See how timestamps, prices, and text direction render across FocusBoard with your current preferences.
          </p>

          <div className="preview-spec-box">
            <div className="preview-item">
              <span className="spec-label">Formatted Price:</span>
              <span className="spec-value highlight">{formatCurrency(49.99)}</span>
            </div>

            <div className="preview-item">
              <span className="spec-label">Current Date:</span>
              <span className="spec-value">{formatDate(sampleDate)}</span>
            </div>

            <div className="preview-item">
              <span className="spec-label">Current Time ({timezone}):</span>
              <span className="spec-value">{formatTime(sampleDate)}</span>
            </div>

            <div className="preview-item">
              <span className="spec-label">Active Language:</span>
              <span className="spec-value">
                {language === 'hi'
                  ? 'हिन्दी (Hindi)'
                  : language === 'te'
                  ? 'తెలుగు (Telugu)'
                  : language === 'ar'
                  ? 'العربية (Arabic - RTL)'
                  : 'English (US)'}
              </span>
            </div>

            <div className="preview-item">
              <span className="spec-label">Layout Direction:</span>
              <span className="spec-value">{direction.toUpperCase()}</span>
            </div>
          </div>

          <div className="preview-sample-banner">
            <strong>Sample UI String:</strong>
            <p>"{t('dashboard.welcome')}"</p>
          </div>
        </div>
      </div>
    </div>
  );
}
