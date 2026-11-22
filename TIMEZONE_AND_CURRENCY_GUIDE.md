# FocusBoard Timezone Management & Multi-Currency Architecture
## Phase 31 Regional Date/Time Formatting & Global Currency Telemetry

FocusBoard implements comprehensive regional preference controls allowing users across different timezones and financial regions to view accurate, localized dates, times, and currency symbols.

---

## 1. Timezone Management & UTC Storage Rules

- **Database Storage**:
  - All timestamps (`created_at`, `updated_at`, `scheduled_start`, `completed_at`) are strictly stored in **UTC** (`timezone.utc`).
  - Naive datetimes are avoided to prevent timezone skew.
- **Display Conversion**:
  - Timestamps are formatted client-side using `Intl.DateTimeFormat` configured with the user's selected IANA timezone (e.g. `Asia/Kolkata`, `America/New_York`, `Europe/London`).
- **Clock Format**:
  - Supports both **12-hour AM/PM** format (e.g., `2:30 PM`) and **24-hour military** format (e.g., `14:30`).

---

## 2. Date Representation Standards

Users can customize their preferred calendar date format in Regional Settings:
1. `YYYY-MM-DD`: ISO 8601 international standard (Default).
2. `DD/MM/YYYY`: United Kingdom, India, and European standard.
3. `MM/DD/YYYY`: United States standard.

---

## 3. Multi-Currency Display & Number Formatting

FocusBoard decouples billing currency from display currency preferences, using `Intl.NumberFormat` with ISO 4217 currency codes:

| Currency Code | Symbol | Currency Name | Example Output |
| :--- | :--- | :--- | :--- |
| `USD` | `$` | US Dollar | `$49.99` |
| `INR` | `₹` | Indian Rupee | `₹49.99` |
| `EUR` | `€` | Euro | `€49.99` |
| `GBP` | `£` | British Pound | `£49.99` |
| `AED` | `د.إ` | UAE Dirham | `49.99 د.إ` |
| `JPY` | `¥` | Japanese Yen | `¥50` |

---

## 4. REST APIs (`/api/v1/regional`)

- `GET /api/v1/regional/settings`: Returns current user regional configuration.
- `PUT /api/v1/regional/settings`: Updates language, timezone, date/time format, and currency.
- `GET /api/v1/regional/locales`: Returns supported platform languages, currencies, and timezones.
