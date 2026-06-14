import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { groupsApi } from '../services/api';
import { useEffect, useRef, useState } from 'react';
import { gsap } from 'gsap';

// Simple SVG icons as components
const HomeIcon = () => (
  <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M3 9.75L12 3l9 6.75V21a.75.75 0 01-.75.75H15v-6H9v6H3.75A.75.75 0 013 21V9.75z" />
  </svg>
);

const GroupIcon = () => (
  <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M18 18.72a9.094 9.094 0 003.741-.479 3 3 0 00-4.682-2.72m.94 3.198l.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0112 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 016 18.719m12 0a5.971 5.971 0 00-.941-3.197m0 0A5.995 5.995 0 0012 12.75a5.995 5.995 0 00-5.058 2.772m0 0a3 3 0 00-4.681 2.72 8.986 8.986 0 003.74.477m.94-3.197a5.971 5.971 0 00-.94 3.197M15 6.75a3 3 0 11-6 0 3 3 0 016 0zm6 3a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0zm-13.5 0a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0z" />
  </svg>
);

const LogoutIcon = () => (
  <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15M12 9l-3 3m0 0l3 3m-3-3h12.75" />
  </svg>
);

const PlusIcon = () => (
  <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
  </svg>
);

export default function Sidebar() {
  const { user, logout } = useAuth();
  const { success, error } = useToast();
  const navigate = useNavigate();
  const sidebarRef = useRef(null);
  const [groups, setGroups] = useState([]);

  // GSAP entrance animation
  useEffect(() => {
    gsap.fromTo(
      sidebarRef.current,
      { x: -20, opacity: 0 },
      { x: 0, opacity: 1, duration: 0.5, ease: 'power3.out' }
    );
  }, []);

  // Load groups for sidebar list
  useEffect(() => {
    if (user) {
      groupsApi.list()
        .then(({ data }) => setGroups(data))
        .catch(() => {});
    }
  }, [user]);

  const handleLogout = async () => {
    await logout();
    success('Logged out');
    navigate('/login');
  };

  const initials = (name) => name
    ? name.split('').slice(0, 2).join('').toUpperCase()
    : '?';

  return (
    <aside className="sidebar" ref={sidebarRef}>
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">F</div>
        <span className="sidebar-logo-text">FairShare</span>
      </div>

      {/* Main nav */}
      <nav className="sidebar-nav">
        <span className="sidebar-section-label">Navigation</span>

        <NavLink
          to="/dashboard"
          className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
        >
          <HomeIcon />
          Dashboard
        </NavLink>

        <NavLink
          to="/groups"
          className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
        >
          <GroupIcon />
          All Groups
        </NavLink>
      </nav>

      {/* Group quick-access */}
      {groups.length > 0 && (
        <div className="sidebar-groups">
          <span className="sidebar-section-label">Your Groups</span>
          {groups.slice(0, 6).map((g) => (
            <div
              key={g.id}
              className="sidebar-group-item"
              onClick={() => navigate(`/groups/${g.id}`)}
            >
              <div className="sidebar-group-avatar">
                {initials(g.name)}
              </div>
              <span className="truncate">{g.name}</span>
            </div>
          ))}
        </div>
      )}

      {/* User footer */}
      <div className="sidebar-footer">
        <div className="sidebar-user" style={{ justifyContent: 'space-between' }}>
          <div className="flex items-center gap-sm">
            <div className="sidebar-avatar">
              {initials(user?.username || 'U')}
            </div>
            <span className="sidebar-username">{user?.username}</span>
          </div>
          <button
            className="btn btn-ghost btn-icon"
            onClick={handleLogout}
            title="Logout"
          >
            <LogoutIcon />
          </button>
        </div>
      </div>
    </aside>
  );
}
