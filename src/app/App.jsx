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
import AIAgentWorkspace from '../pages/AIAgents/AIAgentWorkspace';
import ExecutiveDashboard from '../pages/Executive/ExecutiveDashboard';
import DeveloperPortal from '../pages/Developer/DeveloperPortal';
import SecurityComplianceDashboard from '../pages/Security/SecurityComplianceDashboard';
import FinancialDashboard from '../pages/Finance/FinancialDashboard';
import TrustCenterPage from '../pages/Trust/TrustCenterPage';
import StrategicIntelligenceDashboard from '../pages/Strategy/StrategicIntelligenceDashboard';
import InnovationLabDashboard from '../pages/Innovation/InnovationLabDashboard';
import KnowledgeIntelligenceDashboard from '../pages/Knowledge/KnowledgeIntelligenceDashboard';
import AutomationDashboard from '../pages/Automation/AutomationDashboard';
import IntegrationPlatformDashboard from '../pages/Integrations/IntegrationPlatformDashboard';
import OperationsConsole from '../pages/Operations/OperationsConsole';
import DataIntelligenceDashboard from '../pages/DataIntelligence/DataIntelligenceDashboard';
import SecurityOperationsCenter from '../pages/SecurityOperations/SecurityOperationsCenter';
import ProductLifecycleWorkspace from '../pages/ProductLifecycle/ProductLifecycleWorkspace';
import PredictiveIntelligenceDashboard from '../pages/PredictiveIntelligence/PredictiveIntelligenceDashboard';
import LoginPage from '../pages/Auth/LoginPage';
import { I18nProvider, useI18n } from '../i18n/I18nContext';
import OnboardingModal from '../components/Onboarding/OnboardingModal';
import FeedbackModal from '../components/FeedbackModal/FeedbackModal';
import { growthApi } from '../services/growthApi';
import { MobileBottomNav } from '../components/Navigation/MobileBottomNav';
import { MobileDrawer } from '../components/Navigation/MobileDrawer';
import { AuthModal } from '../components/auth/AuthModal';
import { CommandPalette } from '../components/CommandPalette/CommandPalette';
import { KeyboardShortcutsModal } from '../components/KeyboardShortcutsModal/KeyboardShortcutsModal';
import './App.css';

function AppContent() {
  const [activeTab, setActiveTab] = useState(() => {
    if (typeof window !== 'undefined') {
      const path = window.location.pathname.toLowerCase();
      const hash = window.location.hash.toLowerCase();
      if (
        path === '/login' ||
        path === '/signin' ||
        path === '/signup' ||
        hash === '#login' ||
        hash === '#signin' ||
        hash === '#signup'
      ) {
        return 'login';
      }
    }
    return 'tasks';
  });
  const [isMobileDrawerOpen, setIsMobileDrawerOpen] = useState(false);
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
      setActiveTab('tasks');
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
      case 'agents':
        return 'AI Autonomous Agents & Orchestration';
      case 'team':
        return 'Team Workspace & Collaboration';
      case 'analytics':
        return 'Productivity Analytics';
      case 'calendar':
        return 'Calendar Schedule & Google Sync';
      case 'automation':
        return 'Automation Intelligence & Workflow Orchestrator';
      case 'integrations':
        return 'Integrations Ecosystem & Developer Platform';
      case 'operations':
        return 'Platform Observability & Operations Console';
      case 'data-intelligence':
        return 'Data Intelligence, BI & Enterprise Insights';
      case 'soc':
        return 'Security Operations Center (SOC) & Zero-Trust Intelligence';
      case 'product-lifecycle':
        return 'Product Lifecycle Intelligence & Discovery Platform';
      case 'billing':
        return 'SaaS Plans & Usage Limits';
      case 'predictive-intelligence':
        return 'Predictive Project Intelligence & Health Analytics';
      case 'intelligence':
        return 'Product Intelligence & Behavioral Insights';
      case 'enterprise':
        return 'Enterprise Governance & Security RBAC';
      case 'executive':
        return 'Executive Business Intelligence & Portfolio Analytics';
      case 'developer':
        return 'Developer Platform, Public API & Webhooks';
      case 'compliance':
        return 'Enterprise Security, Compliance & GRC';
      case 'finance':
        return 'SaaS Financial Intelligence, FinOps & Profitability';
      case 'strategy':
        return 'SaaS Platform Strategic Intelligence & Decision Engine';
      case 'innovation':
        return 'Innovation Lab, R&D & Prototyping Pipeline';
      case 'knowledge':
        return 'Organizational Knowledge Intelligence & Graph Hub';
      case 'trust':
        return 'FocusBoard Enterprise Trust Center';
      case 'support':
        return 'Customer Operations & Support';
      case 'settings':
        return 'Preferences & Settings';
      case 'tasks':
      default:
        return 'Task Management';
    }
  };

  const renderActiveContent = () => {
    switch (activeTab) {
      case 'ai':
        return <AIAssistant />;
      case 'agents':
        return <AIAgentWorkspace />;
      case 'team':
        return <TeamWorkspace />;
      case 'analytics':
        return <Analytics />;
      case 'calendar':
        return <CalendarView />;
      case 'automation':
        return <AutomationDashboard />;
      case 'integrations':
        return <IntegrationPlatformDashboard />;
      case 'operations':
        return <OperationsConsole />;
      case 'data-intelligence':
        return <DataIntelligenceDashboard />;
      case 'soc':
        return <SecurityOperationsCenter />;
      case 'product-lifecycle':
        return <ProductLifecycleWorkspace />;
      case 'billing':
        return <Billing />;
      case 'predictive-intelligence':
        return <PredictiveIntelligenceDashboard />;
      case 'intelligence':
        return <Intelligence />;
      case 'enterprise':
        return <Enterprise />;
      case 'executive':
        return <ExecutiveDashboard />;
      case 'developer':
        return <DeveloperPortal />;
      case 'compliance':
        return <SecurityComplianceDashboard />;
      case 'finance':
        return <FinancialDashboard />;
      case 'strategy':
        return <StrategicIntelligenceDashboard />;
      case 'innovation':
        return <InnovationLabDashboard />;
      case 'knowledge':
        return <KnowledgeIntelligenceDashboard />;
      case 'trust':
        return <TrustCenterPage />;
      case 'support':
        return <SupportPortal />;
      default:
        return <Dashboard activeTab={activeTab} />;
    }
  };

  if (activeTab === 'login') {
    return (
      <LoginPage
        onNavigateToDashboard={() => {
          setActiveTab('tasks');
          if (typeof window !== 'undefined' && window.history.pushState) {
            window.history.pushState({}, '', '/');
          }
        }}
      />
    );
  }

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
          onOpenMobileDrawer={() => setIsMobileDrawerOpen(true)}
          onNavigate={(tab) => setActiveTab(tab)}
        />
        <main className="app-main" id="main-content">
          {renderActiveContent()}
        </main>
      </div>

      {/* Mobile Touch Navigation & Offline Status (Bottom bar on screens <= 768px) */}
      <MobileBottomNav
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onOpenMobileDrawer={() => setIsMobileDrawerOpen(true)}
        onNewTask={() => {
          setActiveTab('tasks');
          openCreateModal?.();
        }}
      />

      {/* Comprehensive Mobile Navigation Drawer with 100% Feature Parity */}
      <MobileDrawer
        isOpen={isMobileDrawerOpen}
        onClose={() => setIsMobileDrawerOpen(false)}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onOpenSearch={() => setIsCommandPaletteOpen(true)}
        onOpenFeedback={() => setIsFeedbackModalOpen(true)}
      />

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
          setActiveTab('tasks');
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
    <I18nProvider>
      <AuthProvider>
        <TaskProvider>
          <AppContent />
        </TaskProvider>
      </AuthProvider>
    </I18nProvider>
  );
}

export default App;
