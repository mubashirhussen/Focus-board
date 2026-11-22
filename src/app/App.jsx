import React, { useState, useEffect } from 'react';
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
import { Intelligence } from '../pages/Intelligence/Intelligence';
import { Enterprise } from '../pages/Enterprise/Enterprise';
import SupportPortal from '../pages/Support/SupportPortal';
import OnboardingModal from '../components/Onboarding/OnboardingModal';
import FeedbackModal from '../components/FeedbackModal/FeedbackModal';
import { growthApi } from '../services/growthApi';
import { MobileBottomNav } from '../components/Navigation/MobileBottomNav';
import { AuthModal } from '../components/auth/AuthModal';
import { CommandPalette } from '../components/CommandPalette/CommandPalette';
import { KeyboardShortcutsModal } from '../components/KeyboardShortcutsModal/KeyboardShortcutsModal';
import './App.css';

function AppContent() {
  const [activeTab, setActiveTab] = useState('overview');
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);
  const [isShortcutsModalOpen, setIsShortcutsModalOpen] = useState(false);
  const [isOnboardingOpen, setIsOnboardingOpen] = useState(false);
  const [isFeedbackModalOpen, setIsFeedbackModalOpen] = useState(false);
  const { openCreateModal, closeTaskModal, closeDeleteDialog } = useTasks();

  useEffect(() => {
    growthApi.getOnboarding().then((data) => {
      if (data && !data.is_completed && !data.dismissed) {
        setIsOnboardingOpen(true);
      }
    }).catch(() => {});
  }, []);

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
      case 'intelligence':
        return 'Product Intelligence & Behavioral Insights';
      case 'enterprise':
        return 'Enterprise Governance & Security RBAC';
      case 'support':
        return 'Customer Operations & Support';
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
      case 'intelligence':
        return <Intelligence />;
      case 'enterprise':
        return <Enterprise />;
      case 'support':
        return <SupportPortal />;
      default:
        return <Dashboard activeTab={activeTab} />;
    }
  };

  return (
    <div className="app-layout">
      {/* Navigation Sidebar (Desktop sticky / Tablet) */}
      <Sidebar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onOpenFeedback={() => setIsFeedbackModalOpen(true)}
      />

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

      {/* Product-Led Growth Onboarding Modal */}
      <OnboardingModal
        isOpen={isOnboardingOpen}
        onClose={() => setIsOnboardingOpen(false)}
      />

      {/* In-App Feedback & Bug Reporting Modal */}
      <FeedbackModal
        isOpen={isFeedbackModalOpen}
        onClose={() => setIsFeedbackModalOpen(false)}
      />

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
