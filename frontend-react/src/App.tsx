import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Layout } from './components/Layout';
import Login from './pages/Login';
import Register from './pages/Register';
import LandingPage from './pages/LandingPage';
import Dashboard from './pages/Dashboard';
import ChatAgent from './pages/ChatAgent';
import AuditDashboard from './pages/AuditDashboard';
import Settings from './pages/Settings';
import About from './pages/About';
import OculomicsDashboard from './pages/OculomicsDashboard';

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Protected Routes inside Layout */}
          <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/audit" element={<AuditDashboard />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/about" element={<About />} />

            {/* Special Dashboard for Oculomics */}
            <Route path="/chat/oculomics" element={<OculomicsDashboard />} />

            {/* Dynamic chat route for each agent */}
            <Route path="/chat/:agentId" element={<ChatAgent />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;
