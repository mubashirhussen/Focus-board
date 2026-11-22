import React, { useState } from 'react';
import { AuthProvider } from '../context/AuthContext';
import { TaskProvider } from '../context/TaskContext';
import { useTasks } from '../hooks/useTasks';
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';
import { Sidebar } from '../components/Sidebar/Sidebar';
import { Header } from '../components/Header/Header';
import { Dashboard } from '../pages/Dashboard/Dashboard';
import { Analytics } from '../pages/Analytics/Analytics';
import { AIAssistant } from '../pages/AIAssistant/AIAssistant';
import { TeamWorkspace } from '../pages/TeamWorkspace/TeamWorkspace';
import { CalendarView } from '../pages/Calendar/CalendarView';
import { Integrations } from '../pages/Integrations/Integrations';
import { Billing } from '../pages/Billing/Billing';
import { MobileBottomNav } from '../components/Navigation/MobileBottomNav';
import { AuthModal } from '../components/auth/AuthModal';
import { CommandPalette } from '../components/CommandPalette/CommandPalette';
import { KeyboardShortcutsModal } from '../components/KeyboardShortcutsModal/KeyboardShortcutsModal';
import './App.css';

function AppContent() {
  const [activeTab, setActiveTab] = useState('overview');
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);
  const [isShortcutsModalOpen, setIsShortcutsModalOpen] = useState(false);
  const { openCreateModal, closeTaskModal, closeDeleteDialog } = useTasks();

  // Global Keyboard Shortcuts handler
  useKeyboardShortcuts({
    onToggleCommandPalette: () => setIsCommandPaletteOpen((prev) => !prev),
    onOpenSearch: () => setIsCommandPaletteOpen(true),
    onNewTask: () => {
      setActiveTab('overview');
      openCreateModal?.();
    },
    onToggleShortcutsModal: () => setIsShortcutsModalOpen((prev) => !prev),
    onEscape: () => {
      setIsCommandPaletteOpen(false);
      setIsShortcutsModalOpen(false);
      closeTaskModal?.();
      closeDeleteDialog?.();
    },
  });

  const getPageTitle = (tab) => {
    switch (tab) {
      case 'ai':
        return 'AI Task Planning & Assistant';
      case 'team':
        return 'Team Workspace & Collaboration';
      case 'analytics':
        return 'Productivity Analytics';
      case 'calendar':
        return 'Calendar Schedule & Google Sync';
      case 'integrations':
        return 'Integrations Hub & Automations';
      case 'billing':
        return 'SaaS Plans & Usage Limits';
      case 'tasks':
        return 'Task Management';
      case 'settings':
        return 'Preferences & Settings';
      case 'overview':
      default:
        return 'Overview';
    }
  };

  const renderActiveContent = () => {
    switch (activeTab) {
      case 'ai':
        return <AIAssistant />;
      case 'team':
        return <TeamWorkspace />;
      case 'analytics':
        return <Analytics />;
      case 'calendar':
        return <CalendarView />;
      case 'integrations':
        return <Integrations />;
      case 'billing':
        return <Billing />;
      default:
        return <Dashboard activeTab={activeTab} />;
    }
  };

  return (
    <div className="app-layout">
      {/* Navigation Sidebar (Desktop sticky / Tablet) */}
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />

      {/* Main Content Area */}
      <div className="app-main-wrapper">
        <Header
          title={getPageTitle(activeTab)}
          onOpenCommandPalette={() => setIsCommandPaletteOpen(true)}
        />
        <main className="app-main" id="main-content">
          {renderActiveContent()}
        </main>
      </div>

      {/* Mobile Touch Navigation & Offline Status (Bottom bar on screens <= 768px) */}
      <MobileBottomNav activeTab={activeTab} onTabChange={setActiveTab} />

      {/* Authentication Modal */}
      <AuthModal />

      {/* Global Command Palette (Cmd/Ctrl + K) */}
      <CommandPalette
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
        onNavigate={(tab) => setActiveTab(tab)}
        onNewTask={() => {
          setActiveTab('overview');
          openCreateModal?.();
        }}
        onOpenShortcuts={() => setIsShortcutsModalOpen(true)}
      />

      {/* Keyboard Shortcuts Help Modal (?) */}
      <KeyboardShortcutsModal
        isOpen={isShortcutsModalOpen}
        onClose={() => setIsShortcutsModalOpen(false)}
      />
    </div>
  );
}

export function App() {
  return (
    <AuthProvider>
      <TaskProvider>
        <AppContent />
      </TaskProvider>
    </AuthProvider>
  );
}

export default App;
