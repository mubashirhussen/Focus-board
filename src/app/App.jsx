import React, { useState } from 'react';
import { AuthProvider } from '../context/AuthContext';
import { TaskProvider } from '../context/TaskContext';
import { Sidebar } from '../components/Sidebar/Sidebar';
import { Header } from '../components/Header/Header';
import { Dashboard } from '../pages/Dashboard/Dashboard';
import { Analytics } from '../pages/Analytics/Analytics';
import { AuthModal } from '../components/auth/AuthModal';
import './App.css';

export function App() {
  const [activeTab, setActiveTab] = useState('overview');

  const getPageTitle = (tab) => {
    switch (tab) {
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
              {activeTab === 'analytics' ? (
                <Analytics />
              ) : (
                <Dashboard activeTab={activeTab} />
              )}
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
