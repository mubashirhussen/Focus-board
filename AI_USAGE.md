# FocusBoard — AI Usage & Transparency Log

This document provides transparent disclosure of AI assistance utilized during the development, testing, and full-stack expansion of **FocusBoard**, in accordance with Step 19 of the **MobileFirst Assignment Implementation Guide**.

---

## 1. Candidate Declaration

- **Candidate Name:** Sheik Mubashir Hussen
- **Project:** FocusBoard — Responsive Task Management Dashboard
- **Repository:** https://github.com/mubashirhussen/Focus-board

---

## 2. Tools Used

- **ChatGPT (GPT-4o)**
- **Antigravity AI (Google DeepMind)**
- **GitHub Copilot**
- **Claude 3.5 Sonnet**

---

## 3. Representative Prompts

The following prompts illustrate how AI assistance was leveraged during development:

1. **Prompt 1 (State Management & Data Flow):**
   > *"How do I design a centralized React custom hook and Context provider for FocusBoard that keeps task data in local state, derives dashboard statistics dynamically without division-by-zero errors, and synchronizes with browser localStorage on every mutation?"*

2. **Prompt 2 (Carousel Implementation):**
   > *"Write an accessible three-slide Focus Notes carousel in React with Lucide icons (ChevronLeft, ChevronRight), supporting circular boundary navigation, slide indicator dot selection, keyboard navigation with Arrow keys, and touch swipe gestures for mobile (390px)."*

3. **Prompt 3 (Composite Filtering & Search):**
   > *"How should I implement a composite filtering mechanism in React where case-insensitive title search, status tabs ('All', 'To do', 'In progress', 'Completed'), and priority dropdown ('Low', 'Medium', 'High') operate conjunctively (AND logic) on the same task dataset?"*

4. **Prompt 4 (Responsive Design & Figma Token Mapping):**
   > *"Extract CSS custom properties for FocusBoard adhering strictly to the 1440px desktop frame, 768px tablet reflow, and 390px mobile stacked card layout with WCAG AA compliant color contrast ratios."*

---

## 4. AI-Assisted Areas

- **CSS & Responsive Layouts:** Writing media queries for the 390px, 768px, and 1440px breakpoints; fine-tuning touch target sizes (min 44×44px) for mobile.
- **Component Decomposition:** Structuring reusable components (`StatCard.jsx`, `FocusNotes.jsx`, `TaskCard.jsx`, `TaskForm.jsx`, `SearchBar.jsx`, `FilterTabs.jsx`, `ConfirmDialog.jsx`).
- **Validation & Edge Cases:** Writing robust form validation logic for mandatory trimmed titles, whitespace rejection, and maximum character bounds.
- **Automated Verification:** Synthesizing automated test assertions (`npm test` and pytest) covering CRUD operations, composite filtering, and storage persistence.

---

## 5. Verified or Corrected Suggestion

### Carousel Boundary Navigation & State Wrapping
- **AI Suggestion:** The initial AI-generated carousel implementation used strict boundary clamping: disabling the "Previous" button when `currentIndex === 0` and disabling the "Next" button when `currentIndex === totalSlides - 1`.
- **Human Review & Correction:** During review against Step 7 of the MobileFirst Implementation Guide (*"Handle navigation boundaries consistently, preferably with circular navigation"*), the candidate identified that disabling buttons created a dead-end interaction for mobile touch users. The candidate modified the navigation handler to use modulo arithmetic:
  ```javascript
  // Corrected Circular Navigation Logic
  const handlePrev = () => {
    setCurrentIndex((prev) => (prev - 1 + totalSlides) % totalSlides);
  };

  const handleNext = () => {
    setCurrentIndex((prev) => (prev + 1) % totalSlides);
  };
  ```
  This ensures seamless circular looping across all three slides, keeps navigation buttons permanently interactive, and maintains synchronized indicator bars.

---

## 6. Human Engineering Decisions & Code Ownership

All architectural decisions, visual alignment with the Figma source of truth, accessibility standards, and code reviews were driven and verified by the candidate:
1. **Zero External Dependency Requirement:** Built on standard React hooks (`useState`, `useMemo`, `useCallback`, `useEffect`, `useRef`) without requiring external state management libraries (Redux/MobX) or backend infrastructure to operate.
2. **Data Safety Guarantee:** `useLocalStorage` validates existing stored data before loading and prevents sample data from overwriting user-created tasks on refresh.
3. **Accessibility Compliance:** Validated with semantic HTML5 (`<header>`, `<main>`, `<nav>`, `<section>`, `<dialog>`), visible keyboard focus rings, and screen-reader accessible ARIA labels.
