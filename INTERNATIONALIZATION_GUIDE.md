# FocusBoard Internationalization (i18n) & Localization Guide
## Phase 31 Multilingual Architecture, RTL Support & Regional Preferences

FocusBoard provides an enterprise-ready **Internationalization (i18n)** and **Localization (l10n)** system supporting global users with multi-language interfaces, Right-to-Left (RTL) layouts, and regional preference synchronization.

---

## 1. Supported Languages

| Language Code | Name | Native Script | Direction | Coverage |
| :--- | :--- | :--- | :--- | :--- |
| `en` | **English** | English | LTR | 100% (Default) |
| `hi` | **Hindi** | हिन्दी | LTR | Navigation, Dashboard, Tasks, Agents, Settings, Common |
| `te` | **Telugu** | తెలుగు | LTR | Navigation, Dashboard, Tasks, Agents, Settings, Common |
| `ar` | **Arabic** | العربية | **RTL** | Navigation, Dashboard, Tasks, Agents, Settings, Common |

---

## 2. Dynamic Language Switching & Direction Control

- **Client State (`I18nContext.jsx`)**:
  - `t(key, fallback)` function maps translation keys to active locale dictionaries.
  - Automatically updates `<html dir="rtl">` or `<html dir="ltr">` and `<html lang="...">` dynamically without requiring a page reload.
  - Direction changes automatically adjust CSS logical layout properties.
- **Persistence**:
  - Preference saved in `localStorage` for immediate offline and client boot.
  - Automatically synchronized to database via `PUT /api/v1/regional/settings`.

---

## 3. Translation Key Namespace Structure

Translation keys follow structured namespaces:
- `nav.*`: Sidebar and mobile navigation labels.
- `dashboard.*`: Dashboard titles, welcome banners, hero actions.
- `common.*`: Reusable actions (`save`, `cancel`, `delete`, `approve`, `reject`).
- `agents.*`: AI Agent titles, execution prompts, approval notices.
- `regional.*`: Language, timezone, currency, and date format settings.
