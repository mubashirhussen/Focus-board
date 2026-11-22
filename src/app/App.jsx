import React, { useState } from 'react';
import { TaskProvider } from '../context/TaskContext';
import { Sidebar } from '../components/Sidebar/Sidebar';
import { Header } from '../components/Header/Header';
import { Dashboard } from '../pages/Dashboard/Dashboard';
import './App.css';

export function App() {
  const [activeTab, setActiveTab] = useState('overview');

  return (
    <TaskProvider>
      <div className="app-layout">
        {/* Navigation Sidebar (Desktop sticky / Mobile bottom) */}
        <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />

        {/* Main Content Area */}
        <div className="app-main-wrapper">
          <Header title="Overview" />
          <main className="app-main" id="main-content">
            <Dashboard activeTab={activeTab} />
          </main>
        </div>
      </div>
    </TaskProvider>
  );
}

export default App;
