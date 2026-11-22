# FocusBoard — Task Management Dashboard

FocusBoard is a responsive, single-user task management dashboard developed for the **Frontend Trainee Assessment**. It is crafted with React, Vite, CSS3, and Lucide React icons, adhering strictly to the provided live Figma design references (`1440×1000` desktop, `390×1128` mobile, `760×822` task modal, and `1106×152` Focus Notes carousel slides).

---

## 1. Project Overview

FocusBoard is built to solve everyday task organization with clean visual hierarchy, low cognitive friction, and reliable client-side state persistence. It features:

- **Executive Overview Dashboard**: High-level dynamic statistics reflecting total task load, active work, completed tasks, and completion percentage.
- **Focus Notes Carousel**: A 3-slide visual inspiration banner matching the Figma design frames (`15:2`, `15:30`, and `15:58`), featuring interactive carousel slides with mini floating progress previews and keyboard accessibility.
- **Full Task Lifecycle Management (CRUD)**: Create, view, edit, update status, and safely delete tasks with confirmation dialogs.
- **Unified Search & Multi-Criteria Filtering**: Instant case-insensitive search by task title, description, or category combined with status pills (All, To do, In progress, Completed) and priority selectors (High, Medium, Low).
- **Zero-Latency Persistence**: Reliable `localStorage` data synchronization that preserves user modifications across page reloads without overwriting with sample data.
- **Responsive System**: Tailored layouts across standard desktop (`1440px`), tablet (`768px`), and mobile screens (`390px`) featuring a dedicated mobile bottom navigation bar and touch-friendly controls.

---

## 2. Tech Stack

- **Framework**: React 19 (Hooks, Context API, memoization)
- **Tooling & Bundler**: Vite 8
- **Styling**: Modular plain CSS3 with custom design tokens, CSS variables, and zero CSS framework bloat
- **Iconography**: Lucide React
- **Persistence**: Browser `localStorage` API with defensive fallback handling
- **Language**: JavaScript (ES2022+ / JSX)

---

## 3. Project Structure

```
focusboard/
├── public/
│   └── favicon.svg
├── src/
│   ├── app/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── appConfig.js
│   ├── assets/
│   │   ├── images/
│   │   └── icons/
│   ├── components/
│   │   ├── Sidebar/
│   │   │   ├── Sidebar.jsx
│   │   │   └── Sidebar.css
│   │   ├── Header/
│   │   │   ├── Header.jsx
│   │   │   └── Header.css
│   │   ├── StatCard/
│   │   │   ├── StatCard.jsx
│   │   │   └── StatCard.css
│   │   ├── FocusNotes/
│   │   │   ├── FocusNotes.jsx
│   │   │   └── FocusNotes.css
│   │   ├── TaskList/
│   │   │   ├── TaskList.jsx
│   │   │   └── TaskList.css
│   │   ├── TaskItem/
│   │   │   ├── TaskItem.jsx
│   │   │   └── TaskItem.css
│   │   ├── TaskFilters/
│   │   │   ├── TaskFilters.jsx
│   │   │   └── TaskFilters.css
│   │   ├── TaskForm/
│   │   │   ├── TaskForm.jsx
│   │   │   └── TaskForm.css
│   │   ├── Modal/
│   │   │   ├── Modal.jsx
│   │   │   └── Modal.css
│   │   ├── EmptyState/
│   │   │   ├── EmptyState.jsx
│   │   │   └── EmptyState.css
│   │   └── ConfirmDialog/
│   │       ├── ConfirmDialog.jsx
│   │       └── ConfirmDialog.css
│   ├── pages/
│   │   └── Dashboard/
│   │       ├── Dashboard.jsx
│   │       └── Dashboard.css
│   ├── context/
│   │   └── TaskContext.jsx
│   ├── hooks/
│   │   ├── useTasks.js
│   │   └── useLocalStorage.js
│   ├── data/
│   │   ├── initialTasks.js
│   │   └── focusNotes.js
│   ├── utils/
│   │   ├── taskHelpers.js
│   │   ├── dateHelpers.js
│   │   └── validation.js
│   ├── styles/
│   │   ├── variables.css
│   │   ├── global.css
│   │   ├── typography.css
│   │   └── responsive.css
│   ├── main.jsx
│   └── index.css
├── .env
├── .env.example
├── .gitignore
├── index.html
├── package.json
├── README.md
├── AI_USAGE.md
└── vite.config.js
```

---

## 4. Installation & Getting Started

### Prerequisites
- Node.js (version 18 or higher recommended; verified on Node v24)
- npm (version 9 or higher)

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd focusboard

# Install dependencies
npm install
```

### Running Locally (Development Mode)
```bash
npm run dev
```
The application will start at `http://localhost:3000` (or `http://localhost:5173` if running Vite directly) with Hot Module Replacement (HMR).

### Building for Production
```bash
npm run build
```
Generates optimized, minified production assets inside the `dist/` folder.

### Previewing Production Build
```bash
npm run preview
```

---

## 5. State Management Architecture

State is architected around the **Single Source of Truth** principle using React's built-in **Context API** (`TaskContext`) combined with custom hooks (`useTasks`, `useLocalStorage`).

### Why React Context + Custom Hooks?
- **Zero Third-Party Dependency**: Avoids the bundle overhead of Redux or heavy boilerplate for a single-user task dashboard.
- **Predictable Mutations**: All modifications (`addTask`, `updateTask`, `deleteTask`, `updateTaskStatus`) execute immutably using pure updater functions.
- **Derived State via `useMemo`**: Overview statistics (`total`, `todo`, `inProgress`, `completed`, `completionRate`) and `filteredTasks` are dynamically derived rather than stored in parallel state variables. This guarantees zero state synchronization bugs or stale counters.

---

## 6. Local Storage Persistence

Task data is stored under the storage key defined in `.env` (`focusboard_tasks_v1`).

1. **Initial Load**: The hook reads `localStorage`. If no stored records exist or the data is invalid, it safely bootstraps from `initialTasks.js`.
2. **Subsequent Visits & Refreshes**: If existing user tasks exist in `localStorage`, they are preserved and never overwritten by sample data.
3. **Resilience**: Handled within a defensive `try / catch` wrapper to guard against quota limitations, restricted iframe sandboxes, and corrupted JSON.
4. **Demo Reset**: A dedicated "Reset Demo Data" action in the sidebar allows testers to restore default tasks on demand.

---

## 7. Responsive Design System

The application adapts across three primary screen widths matching Figma specifications:

- **Desktop (1440px+)**: Left persistent navigation sidebar, top breadcrumb bar with user profile, high-density 3-card overview grid, wide Focus Notes carousel, and horizontal task rows.
- **Tablet (768px - 1024px)**: Responsive sidebar reflow, wrapped filter controls, and adapted card sizing without horizontal scrollbars.
- **Mobile (390px)**:
  - Top header with compact FocusBoard icon and user initials.
  - Floating circular quick-add button (`+`).
  - Vertically stacked overview cards.
  - Horizontally scrollable status pills.
  - Mobile bottom navigation bar fixed to the viewport with active states and badge indicators.
  - Fully touch-friendly interactive targets (44px minimum).

---

## 8. Deployment

This is a frontend-only Vite application with static output. It can be deployed to any static host:

### Deploying to Vercel
```bash
npm install -g vercel
vercel
```
Select default framework preset (`Vite`), build command (`npm run build`), and output directory (`dist`).

### Deploying to Netlify
```bash
npm install -g netlify-cli
netlify deploy --prod --dir=dist
```

---

## 9. Limitations

- **Single User Scope**: Designed strictly as a client-side, single-user dashboard; does not implement multi-tenant authentication or server-side databases.
- **Unlinked Navigation Items**: As designated in the assessment scope, navigation sections such as "Calendar" and "Settings" are visual UI placeholders, keeping focus on core task management and the Focus Notes carousel.
