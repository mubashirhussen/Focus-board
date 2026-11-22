import React, { useState } from 'react';
import { AuthProvider } from '../context/AuthContext';
import { TaskProvider } from '../context/TaskContext';
import { Sidebar } from '../components/Sidebar/Sidebar';
import { Header } from '../components/Header/Header';
import { Dashboard } from '../pages/Dashboard/Dashboard';
import { Analytics } from '../pages/Analytics/Analytics';
import { AIAssistant } from '../pages/AIAssistant/AIAssistant';
import { TeamWorkspace } from '../pages/TeamWorkspace/TeamWorkspace';
import { AuthModal } from '../components/auth/AuthModal';
import './App.css';

export function App() {
  const [activeTab, setActiveTab] = useState('overview');

  const getPageTitle = (tab) => {
    switch (tab) {
      case 'ai':
        return 'AI Task Planning & Assistant';
      case 'team':
        return 'Team Workspace & Collaboration';
      case 'analytics':
        return 'Productivity Analytics';
      case 'tasks':
        return 'Task Management';
      case 'calendar':
        return 'Calendar Schedule';
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
      default:
        return <Dashboard activeTab={activeTab} />;
    }
  };

  return (
    <AuthProvider>
      <TaskProvider>
        <div className="app-layout">
          {/* Navigation Sidebar (Desktop sticky / Mobile bottom) */}
          <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />

          {/* Main Content Area */}
          <div className="app-main-wrapper">
            <Header title={getPageTitle(activeTab)} />
            <main className="app-main" id="main-content">
              {renderActiveContent()}
            </main>
          </div>

          {/* Authentication Modal */}
          <AuthModal />
        </div>
      </TaskProvider>
    </AuthProvider>
  );
}

export default App;
