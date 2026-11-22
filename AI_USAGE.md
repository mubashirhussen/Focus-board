# AI Usage Disclosure & Code Understanding

## 1. AI Tools Used
- **Antigravity AI Assistant** (powered by Google DeepMind Gemini models)

---

## 2. Representative Prompts
1. *"Act as a senior frontend engineer and product UI developer. Implement a complete, polished, responsive, functional frontend for FocusBoard, based on the provided Frontend Trainee Assignment PDF and the linked live Figma design references."*
2. *"Inspect the live Figma thumbnail and extract exact copy, active indicator styling, progress bars, and floating card treatments for Focus Notes slides 1, 2, and 3."*
3. *"Construct a robust React Context and custom useLocalStorage hook that avoids stale derived states and never overrides existing user tasks on page refresh."*

---

## 3. AI-Assisted Areas
- **Asset & Layout Extraction**: Parsing the Figma thumbnail and PDF specifications to extract exact card dimensions, color palettes (`#4F46E5`, `#6366F1`, `#ECFDF5`, `#FEF3C7`), typography scales, and slide copy.
- **Boilerplate & CSS System Architecture**: Generating modular, well-structured CSS design variables (`variables.css`, `typography.css`, `global.css`, `responsive.css`) with consistent 8pt-based spacing.
- **Form Validation & Keyboard Accessibility**: Writing ARIA attributes, modal focus trapping, Escape key handlers, and live input validation for the task creation and edit dialog.

---

## 4. Suggestions Verified, Corrected, or Rejected

### Suggestion: Storing Filtered Tasks & Statistics as Independent State Variables
- **Initial Idea**: An initial pattern suggested maintaining separate state variables: `const [stats, setStats] = useState(...)` and `const [filteredList, setFilteredList] = useState(...)`, updating them inside `useEffect` blocks whenever `tasks` changed.
- **Evaluation & Correction**: This was **rejected** because parallel states introduce synchronization delay, extra render cycles, and edge cases where counts disagree with the visible list.
- **Implemented Solution**: Computed `stats` and `filteredTasks` as pure derived values using `useMemo` directly from `tasks`, `searchQuery`, `statusFilter`, and `priorityFilter`. This ensures atomic, glitch-free updates across the dashboard whenever a task is added, edited, deleted, or toggled.

---

## 5. Code Understanding Summary
The application follows a unidirectional data flow:
1. `TaskProvider` owns the core array of tasks, persisted via `useLocalStorage`.
2. Any component can dispatch atomic actions (`addTask`, `updateTask`, `deleteTask`, `updateTaskStatus`).
3. Derived states (`stats`, `filteredTasks`) compute synchronously on every state transition, ensuring cards and rows remain in sync.
4. UI components are purely presentational or connected through clean custom hooks (`useTasks`), keeping JSX clean, accessible, and easily testable.
