import { Routes, Route, Navigate } from 'react-router-dom';
import { RequireAuth, RedirectIfAuth } from './components/RouteGuards';
import LoginPage       from './pages/LoginPage';
import RegisterPage    from './pages/RegisterPage';
import DashboardPage   from './pages/DashboardPage';
import GroupsListPage  from './pages/GroupsListPage';
import GroupDetailPage from './pages/GroupDetailPage';

export default function App() {
  return (
    <Routes>
      {/* Auth routes — redirect away if already logged in */}
      <Route element={<RedirectIfAuth />}>
        <Route path="/login"    element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Route>

      {/* Protected routes — require login, render inside sidebar layout */}
      <Route element={<RequireAuth />}>
        <Route path="/dashboard"       element={<DashboardPage />} />
        <Route path="/groups"          element={<GroupsListPage />} />
        <Route path="/groups/:id"      element={<GroupDetailPage />} />
      </Route>

      {/* Default redirect */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
