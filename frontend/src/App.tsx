import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';

import './i18n';
import { useAuthStore } from '@/store/authStore';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Dashboard } from '@/pages/Dashboard';
import { Login } from '@/pages/Login';
import { BootstrapSetup } from '@/pages/BootstrapSetup';
import { ServerDetails } from '@/pages/ServerDetails';
import { CreateServer } from '@/pages/CreateServer';
import { UserManagement } from '@/pages/UserManagement';
import { RolesManagement } from '@/pages/RolesManagement';
import { Settings } from '@/pages/Settings';
import { loadSavedColorPreset } from '@/utils/colorPresets';
import { BackgroundAnimation } from '@/components/common/BackgroundAnimation';

const PrivateRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, user, requirePasswordChange } = useAuthStore();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (user?.role === 'bootstrap' && location.pathname !== '/setup-admin') {
    return <Navigate to="/setup-admin" replace />;
  }

  if (!requirePasswordChange && user?.role !== 'bootstrap' && location.pathname === '/setup-admin') {
    return <Navigate to="/" replace />;
  }

  if (requirePasswordChange && location.pathname !== '/setup-admin') {
    return <Navigate to="/setup-admin" replace />;
  }

  return <>{children}</>;
};

function App() {
  // Load saved color preset on app startup
  React.useEffect(() => {
    loadSavedColorPreset();
  }, []);

  return (
    <BrowserRouter>
      <BackgroundAnimation />
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/setup-admin"
          element={
            <PrivateRoute>
              <BootstrapSetup />
            </PrivateRoute>
          }
        />

        <Route
          path="/"
          element={
            <PrivateRoute>
              <DashboardLayout />
            </PrivateRoute>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="servers/new" element={<CreateServer />} />
          <Route path="servers/:id" element={<ServerDetails />} />
          <Route path="users" element={<UserManagement />} />
          <Route path="roles" element={<RolesManagement />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
