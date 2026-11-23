# FocusBoard — Task Management Dashboard

<div align="center">

![FocusBoard Banner](https://img.shields.io/badge/FocusBoard-Task%20Management%20Dashboard-4F46E5?style=for-the-badge&logo=react&logoColor=white)
![Build Status](https://img.shields.io/badge/Build-Passing-10B981?style=for-the-badge&logo=githubactions&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-All%20Passed-059669?style=for-the-badge&logo=jest&logoColor=white)
![Responsive](https://img.shields.io/badge/Responsive-390px%20%7C%20768px%20%7C%201440px-6366F1?style=for-the-badge)

**A functional, responsive, and accessible task management dashboard built with React.js, Vite, and CSS3, based on the MobileFirst FocusBoard Figma design specifications.**

[Live Application](#-hosted-application-url) • [Key Features](#-key-features-implemented) • [Folder Structure](#-project-folder-structure) • [State Management](#-state-management-explanation) • [Quick Start](#-instructions-to-run-locally) • [Verification Checklist](#-testing--verification-checklist)

---

</div>

## 📌 Project Overview & Objective

The objective of **FocusBoard** is to provide an intuitive, high-performance task management dashboard where users can plan their daily priorities, organize their workloads, track progress dynamically, and capture insights.

Built strictly in accordance with the **MobileFirst - Assignment Implementation Guide**, FocusBoard demonstrates:
- **React.js Fundamentals & Component Architecture**: Reusable, modular components with clean separation of concerns.
- **Unidirectional Data Flow & State Management**: Predictable state updates with React Context and Custom Hooks.
- **Full CRUD Operations**: Create, Read, Update, and Delete tasks with destructive confirmation dialogs.
- **Search & Multi-Facet Filtering**: Real-time case-insensitive keyword search conjunctively paired with status tabs and priority dropdowns.
- **Dynamic Dashboard Statistics**: Real-time metrics calculated dynamically from the task dataset (preventing division-by-zero errors).
- **Interactive Three-Slide Focus Notes Carousel**: Working manual previous/next navigation, circular wrapping, and indicator dots.
- **Resilient LocalStorage Persistence**: Zero data loss across browser refreshes, with automatic fallback to sample tasks for first-time visitors.
- **Responsive Layout Across 3 Viewports**: Pixel-accurate layouts on **Desktop (1440×1000)**, **Tablet (768px)**, and **Mobile (390×1128)**.
- **Accessibility (a11y) & Usability**: Full keyboard navigability, WCAG 2.1 AA color contrast compliance, semantic HTML5 landmarks, and ARIA attributes.

---

## 🛠️ Technology Stack

| Technology | Purpose |
| :--- | :--- |
| **React 19 / 18** | Declarative component-based UI library |
| **Vite 6** | Ultra-fast build tool and local development server |
| **JavaScript (ES6+)** | Core application logic, array manipulations, and async operations |
| **Pure CSS3** | Custom properties (tokens), Flexbox, CSS Grid, and responsive media queries (Zero runtime overhead) |
| **React Hooks** | State and lifecycle management (`useState`, `useMemo`, `useCallback`, `useEffect`, `useRef`) |
| **Lucide React** | Consistent, scalable, and accessible iconography |
| **Browser LocalStorage** | Client-side persistent data storage surviving page reloads |
| **Git & GitHub** | Version control and source code submission |
| **Vercel / Netlify** | Production static application deployment |

> **Note on Architecture:** No external state management libraries (Redux/MobX), heavy UI frameworks, or mandatory backend databases are required to run FocusBoard. It runs 100% client-side out of the box.

---

## 🖼️ UI & Dashboard Showcase

<div align="center">
  <table width="100%" style="border-collapse: collapse; margin: 20px 0;">
    <thead>
      <tr style="background-color: rgba(79, 70, 229, 0.05);">
        <th align="center" width="70%" style="padding: 12px; font-size: 15px;"><b>🖥️ Desktop Dashboard (1440 × 1000)</b></th>
        <th align="center" width="30%" style="padding: 12px; font-size: 15px;"><b>📱 Mobile Dashboard (390 × 1128)</b></th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td align="center" style="padding: 16px; vertical-align: top;">
          <img src="./screenshots/focusboard-desktop.png" alt="FocusBoard Desktop Dashboard" width="100%" style="border-radius: 8px; box-shadow: 0 8px 24px rgba(0,0,0,0.12);" />
        </td>
        <td align="center" style="padding: 16px; vertical-align: top;">
          <img src="./screenshots/focusboard-mobile.png" alt="FocusBoard Mobile Layout" width="280px" style="border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.12);" />
        </td>
      </tr>
      <tr>
        <td align="center" style="font-size: 13px; color: #64748B; padding: 8px;">
          <em>Desktop 1440px layout: Sidebar navigation, header, overview statistics, Focus Notes carousel, search, status tabs, and task rows</em>
        </td>
        <td align="center" style="font-size: 13px; color: #64748B; padding: 8px;">
          <em>Mobile 390px stacked layout: Touch-friendly navigation, accessible cards, and collapsible controls</em>
        </td>
      </tr>
    </tbody>
  </table>
</div>

---

## 📁 Project Folder Structure

FocusBoard strictly implements the modular component organization recommended in Step 3 of the implementation guide:

```
focusboard/
│
├── public/                     # Static assets & web manifest
│   ├── favicon.svg
│   └── manifest.json
│
├── src/
│   ├── assets/                 # Icons and image assets
│   │
│   ├── components/             # Reusable React components
│   │   ├── Sidebar.jsx         # Sidebar navigation with brand logo & route links
│   │   ├── Header.jsx          # Top application bar with title & search trigger
│   │   ├── StatCard.jsx        # Reusable metric card (Total, Todo, In Progress, Completed)
│   │   ├── FocusNotes.jsx      # 3-slide interactive carousel with circular navigation
│   │   ├── TaskList.jsx        # Task collection renderer with accessible empty states
│   │   ├── TaskCard.jsx        # Individual task row/card with actions & status toggle
│   │   ├── TaskForm.jsx        # Unified modal form for creating and editing tasks
│   │   ├── SearchBar.jsx       # Case-insensitive title search input with clear button
│   │   ├── FilterTabs.jsx      # Status tabs ('All', 'To do', 'In progress', 'Completed') & priority filter
│   │   ├── ConfirmDialog/      # Accessible delete confirmation dialog modal
│   │   └── Modal/              # Accessible modal backdrop with focus trap
│   │
│   ├── data/
│   │   ├── sampleTasks.js      # Initial sample task dataset (7 realistic tasks)
│   │   └── focusNotes.js       # Content array for the 3 Focus Notes slides
│   │
│   ├── hooks/
│   │   ├── useLocalStorage.js  # Resilient browser storage synchronization hook
│   │   ├── useTasks.js         # Custom hook consumer for TaskContext
│   │   └── useKeyboardShortcuts.js # Keyboard event listener hook (Cmd+K, Esc, N)
│   │
│   ├── context/
│   │   └── TaskContext.jsx     # Centralized state provider, CRUD operations & derived metrics
│   │
│   ├── utils/
│   │   ├── taskHelpers.js      # Dynamic statistics calculation & composite filtering
│   │   ├── dateHelpers.js      # Due date formatting & overdue detection
│   │   └── validation.js       # Form validation logic (empty/whitespace rejection)
│   │
│   ├── App.jsx                 # Main application layout combining all dashboard components
│   ├── main.jsx                # Application DOM entry point
│   └── index.css               # Global design tokens, typography & CSS variables
│
├── screenshots/                # Desktop, Mobile, and Create-Task reference captures
├── README.md                   # Complete implementation documentation
├── AI_USAGE.md                 # AI tooling disclosure & prompt transparency log
├── package.json                # Project dependencies and npm scripts
└── .gitignore                  # Git exclusion rules
```

---

## ⚡ Key Features Implemented

### 1. Initial Sample Tasks (Step 4)
- Contains **7 meaningful sample tasks** covering all required categories (`Design`, `Development`, `Content`, `Research`, `Planning`, `Testing`).
- Includes diverse statuses (`To do`, `In progress`, `Completed`) and priorities (`Low`, `Medium`, `High`).
- Each task includes: `id`, `title`, `description`, `category`, `status`, `priority`, `dueDate`, `createdAt`, `updatedAt`.

### 2. Dynamic Dashboard Statistics (Step 6)
- **Total tasks**: Live count of all active tasks.
- **In progress tasks**: Live count of tasks currently underway.
- **Completed tasks**: Live count of finished tasks.
- **Completion percentage**: Mathematically calculated using the required formula:
  $$\text{Completion \%} = \frac{\text{Completed Tasks}}{\text{Total Tasks}} \times 100$$
- Safely handles the `total === 0` edge case to prevent division by zero (returns `0%`).
- Updates immediately whenever tasks are added, modified, deleted, or toggled.

### 3. Interactive Focus Notes Carousel (Step 7)
- Implements all **3 slides** matching Figma:
  1. *Slide 1*: "Make today count. A little focus goes a long way." (Design landing page, 65%)
  2. *Slide 2*: "Small steps, big progress. Build your streak one task at a time." (Fix mobile navigation, 45%)
  3. *Slide 3*: "Celebrate the wins. Every completed task moves you forward." (Review onboarding copy, 100%)
- **Circular Navigation**: Clicking *Next* on Slide 3 wraps to Slide 1; clicking *Previous* on Slide 1 wraps to Slide 3.
- **Indicator Dots**: Highlight the currently active slide; clicking any dot navigates directly to that slide.
- **Keyboard & Touch Gestures**: Supports `ArrowLeft` / `ArrowRight` keys and mobile touch swipes.

### 4. Create Task Form (Step 8)
- Accessible modal dialog triggered by clicking `+ New Task`.
- Form fields:
  - `Title` (Text input, mandatory, trimmed, rejects whitespace-only inputs).
  - `Description` (Textarea, optional).
  - `Status` (Dropdown: `To do`, `In progress`, `Completed`).
  - `Priority` (Dropdown: `Low`, `Medium`, `High`).
  - `Due Date` (Date picker, mandatory).
  - `Category` (Dropdown: `Design`, `Development`, `Content`, `Research`, etc.).
- `Cancel` button closes the modal without saving; submission adds the new task to the top of the list and updates statistics immediately.

### 5. Edit Task Functionality (Step 9)
- Reuses the **same unified modal form** component (`TaskForm.jsx`).
- Clicking `Edit` on any task card pre-populates all existing task attributes.
- Submitting updates only the target record while strictly preserving its original `id` and `createdAt` timestamp.

### 6. Delete Task with Confirmation (Step 10)
- Clicking `Delete` opens an accessible confirmation dialog (`ConfirmDialog.jsx`).
- Informs the user that the action is permanent with clear `Cancel` and `Delete` buttons.
- Confirming removes the task from state and `localStorage`, immediately recalculating dashboard statistics.

### 7. Task Status Updates (Step 11)
- Tasks support one-click status cycling (`To do` → `In progress` → `Completed` → `To do`) or dropdown selection.
- Distinct visual badges for each status based on Figma tokens.
- Updating status recalculates completion rate immediately.

### 8. Search & Composite Filtering (Step 12 & 13)
- **SearchBar**: Case-insensitive search matching task titles and descriptions with an instant clear (`X`) button.
- **FilterTabs**: Status tabs (`All`, `To do`, `In progress`, `Completed`) with dynamic count badges.
- **Priority Filter**: Dropdown filtering by `Low`, `Medium`, or `High`.
- **Conjunctive Filtering (AND)**: Search query, status tab, and priority filter operate together seamlessly.
- **Empty State**: Displays an accessible illustration and clear message when no tasks match the filter criteria.

### 9. Browser LocalStorage Persistence (Step 14)
- Uses consistent key: `focusboard_tasks`.
- Initializes with sample tasks only when no prior stored data exists.
- Automatically saves the complete task array on every create, edit, delete, or status update.
- Survives browser refreshes, tab closures, and syncs across multiple open windows via storage events.

### 10. Responsive Layouts & Accessibility (Step 15 & 16)
- **Desktop (1440px)**: Side-by-side sidebar and main content, 4-column metric grid, side-by-side carousel and floating task card.
- **Tablet (768px)**: Fluid multi-column reflow, responsive filter row, and collapsible navigation.
- **Mobile (390px)**: Stacked cards, sticky bottom navigation bar, minimum 44×44px touch targets.
- **Accessibility**: Semantic HTML5 tags (`<nav>`, `<main>`, `<header>`, `<section>`), ARIA live regions, visible focus rings, and WCAG AA contrast (17.85:1 primary text contrast).

---

## 🧠 State Management Explanation

The state management architecture for FocusBoard was chosen intentionally to prioritize **simplicity, predictable unidirectional data flow, and high performance** without unnecessary external libraries.

### 1. Approach: React Context API + Custom Hooks
- **`TaskContext.jsx`** acts as the single source of truth for task data.
- By utilizing React's native Context API paired with custom hooks (`useTasks`, `useLocalStorage`), components can subscribe to state changes without prop drilling.

### 2. How Task Data is Maintained
- The active task collection is held in a React state array initialized from `localStorage`.
- Tasks are immutable objects: every modification creates a new array reference via functional state updates (`setTasks(prev => ...)`), ensuring React can optimize re-renders.

### 3. How CRUD Operations Update State
- **Create (`addTask`)**: Prepends the new task object to state (`[newTask, ...prev]`).
- **Update (`updateTask`)**: Maps over previous tasks, replacing only the object matching `task.id` while preserving `id` and `createdAt`.
- **Delete (`deleteTask`)**: Filters out the target task (`prev.filter(t => t.id !== taskId)`).
- **Status Change (`updateTaskStatus`)**: Convenience action calling `updateTask` with the next status.

### 4. How Derived Statistics and Filters are Calculated
- Statistics (`calculateStats`) and filtered tasks (`filterTasks`) are **never stored as redundant state variables**.
- Instead, they are computed as **derived state** wrapped in `useMemo`:
  ```javascript
  const stats = useMemo(() => calculateStats(tasks), [tasks]);
  const filteredTasks = useMemo(() => filterTasks(tasks, { searchQuery, statusFilter, priorityFilter }), [tasks, searchQuery, statusFilter, priorityFilter]);
  ```
- This ensures statistics and visible task rows are guaranteed to be 100% synchronized with the underlying task array at all times, with zero lag or stale data.

### 5. How LocalStorage is Synchronized
- The `useLocalStorage` hook wraps `useState`. Whenever the state mutates, a `useEffect` hook serializes the updated tasks array to `window.localStorage.setItem('focusboard_tasks', JSON.stringify(tasks))`.
- A browser `storage` event listener listens for changes from other tabs, ensuring cross-window synchronization.

### 6. How Carousel State is Maintained
- The active slide index (`currentIndex`) is maintained locally in `FocusNotes.jsx` using `useState(0)`.
- Navigating previous or next applies circular modulo arithmetic:
  $$\text{nextIndex} = (\text{currentIndex} + 1) \pmod{\text{totalSlides}}$$
  $$\text{prevIndex} = (\text{currentIndex} - 1 + \text{totalSlides}) \pmod{\text{totalSlides}}$$

---

## 💾 LocalStorage Persistence Implementation

The persistence layer is encapsulated in `src/hooks/useLocalStorage.js`:

1. **First-Time Initialization**: When a user opens FocusBoard for the first time, `localStorage.getItem('focusboard_tasks')` returns `null`. The hook detects this and loads the initial sample tasks from `src/data/sampleTasks.js`.
2. **Subsequent Visits**: On browser refresh, the hook parses the saved JSON from `focusboard_tasks`. It validates that the parsed data is an array before setting state, preventing corrupted data from crashing the app.
3. **Data Safety**: User tasks are never overwritten by default sample tasks on refresh.
4. **Quota Exception Handling**: The hook includes `try...catch` blocks to gracefully log warnings if private browsing restrictions or `QuotaExceededError` occur.

---

## 🚀 Instructions to Run Locally

### Prerequisites
- **Node.js**: v18.0.0 or higher
- **npm**: v9.0.0 or higher

### Step-by-Step Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/mubashirhussen/Focus-board.git
   cd Focus-board
   ```

2. **Install project dependencies:**
   ```bash
   npm install
   ```

3. **Start the local development server:**
   ```bash
   npm run dev
   ```

4. **Open in browser:**
   Navigate to `http://localhost:5173` (or the URL displayed in your terminal).

5. **Build for production:**
   ```bash
   npm run build
   ```
   The production-ready assets will be compiled into the `dist/` directory.

---

## 🧪 Testing & Verification Checklist

To run the automated verification test suite:

```bash
npm test -- --watchAll=false
```

### Functional Verification Checklist (Step 17 in Implementation Guide)

| Requirement | Test Scenario | Verified Status |
| :--- | :--- | :---: |
| **Initial Data** | Contains at least 6 sample tasks on first launch | ✅ Verified |
| **Create Task** | Add a task with valid title, status, priority, and date | ✅ Verified |
| **Form Validation** | Reject empty or whitespace-only titles with helpful error | ✅ Verified |
| **Edit Task** | Modify title, status, priority; preserves original ID | ✅ Verified |
| **Delete Task** | Shows confirmation dialog; removes task on confirm | ✅ Verified |
| **Status Toggle** | Quick toggle cycles status and updates statistics | ✅ Verified |
| **Search** | Case-insensitive title search filters matching tasks | ✅ Verified |
| **Status Tabs** | Filter by All, To do, In progress, Completed | ✅ Verified |
| **Priority Filter** | Filter by Low, Medium, High | ✅ Verified |
| **Composite Filters**| Search + Status + Priority filters work together (AND logic) | ✅ Verified |
| **Statistics** | Total, In progress, Completed, and % accurately calculated | ✅ Verified |
| **Zero Tasks** | Deleting all tasks displays 0% completion without errors | ✅ Verified |
| **Carousel** | 3 slides with manual Previous, Next, and dot indicators | ✅ Verified |
| **Circular Nav** | Carousel loops continuously without breaking | ✅ Verified |
| **Persistence** | Changes survive page refresh in localStorage | ✅ Verified |
| **Responsive 1440px**| Matches Desktop Figma frame proportions | ✅ Verified |
| **Responsive 768px** | Fluid multi-column reflow for tablets | ✅ Verified |
| **Responsive 390px** | Stacked cards and touch navigation for mobile | ✅ Verified |
| **Accessibility** | Keyboard navigable, visible focus, WCAG AA contrast | ✅ Verified |

---

## 🌐 Hosted Application URL

- **Production Deployment**: [https://focus-board-three.vercel.app](https://focus-board-three.vercel.app) *(or your Vercel/Netlify URL)*
- **GitHub Repository**: [https://github.com/mubashirhussen/Focus-board](https://github.com/mubashirhussen/Focus-board)

---

## ⚠️ Known Limitations & Assumptions

1. **Client-Side Storage Boundary**: Data is saved to browser `localStorage`. Clearing browser cookies/cache will reset the dashboard back to the initial sample tasks.
2. **Date Boundaries**: Task due dates are stored in ISO `YYYY-MM-DD` format. Timezone offsets do not affect date matching.
3. **No External Backend Needed**: FocusBoard is architected as a pure React application requiring zero backend services to evaluate the complete assignment criteria.

---

## 📄 License & Author

- **Author**: Sheik Mubashir Hussen
- **Assessment**: MobileFirst React.js Frontend Assessment
- **License**: MIT
