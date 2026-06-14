import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Sidebar from './Sidebar';

// Protects routes that require login
export function RequireAuth() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="page-loader">
        <span className="spinner spinner-lg" />
        <span className="page-loader-text">Loading FairShare...</span>
      </div>
    );
  }

  if (!user) return <Navigate to="/login" replace />;

  return (
    <div className="app-shell">
      <Sidebar />
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}

// Redirects logged-in users away from auth pages
export function RedirectIfAuth() {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (user) return <Navigate to="/dashboard" replace />;
  return <Outlet />;
}
