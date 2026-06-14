import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { gsap } from 'gsap';
import { useAuth } from '../context/AuthContext';
import { groupsApi, balancesApi } from '../services/api';

function StatCard({ label, value, valueClass = '', icon }) {
  return (
    <div className="card stat-card">
      <div className="card-header">
        <span className="card-title">{label}</span>
        <span style={{ fontSize: '1.3rem' }}>{icon}</span>
      </div>
      <div className={`card-value ${valueClass}`}>{value}</div>
    </div>
  );
}

function GroupCard({ group, onClick }) {
  const activeMembers = group.memberships?.filter((m) => m.is_active) || [];
  const initials = (name) => name.slice(0, 2).toUpperCase();

  return (
    <div className="card card-interactive" onClick={onClick} id={`group-card-${group.id}`}>
      <div className="flex items-center justify-between mb-md">
        <div>
          <h3 style={{ fontSize: '1rem', marginBottom: '4px' }}>{group.name}</h3>
          {group.description && (
            <p className="text-sm text-muted truncate">{group.description}</p>
          )}
        </div>
        <div className="avatar-group">
          {activeMembers.slice(0, 4).map((m) => (
            <div className="avatar" key={m.id} title={m.user.username}>
              {initials(m.user.username)}
            </div>
          ))}
          {activeMembers.length > 4 && (
            <div className="avatar" style={{ background: 'var(--bg-elevated)', color: 'var(--text-muted)' }}>
              +{activeMembers.length - 4}
            </div>
          )}
        </div>
      </div>
      <div className="flex items-center gap-md">
        <span className="badge badge-muted">{activeMembers.length} members</span>
        <span className="text-xs text-muted">
          Created by {group.created_by?.username}
        </span>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const pageRef = useRef(null);
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [totalOwed, setTotalOwed] = useState(0);
  const [totalOwe, setTotalOwe] = useState(0);

  useEffect(() => {
    async function load() {
      try {
        const { data } = await groupsApi.list();
        setGroups(data);

        // Fetch balances for each group to compute dashboard totals
        let owed = 0, owe = 0;
        await Promise.allSettled(
          data.map(async (g) => {
            try {
              const { data: bal } = await balancesApi.get(g.id);
              const mine = bal.balances.find((b) => b.username === user?.username);
              if (mine) {
                owed += parseFloat(mine.owed_to_you || 0);
                owe  += parseFloat(mine.you_owe   || 0);
              }
            } catch {}
          })
        );
        setTotalOwed(owed);
        setTotalOwe(owe);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [user]);

  // GSAP stagger animation on cards
  useEffect(() => {
    if (!loading && pageRef.current) {
      gsap.fromTo(
        pageRef.current.querySelectorAll('.stat-card, .card-interactive'),
        { y: 24, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.5, stagger: 0.08, ease: 'power3.out', delay: 0.1 }
      );
    }
  }, [loading]);

  const net = totalOwed - totalOwe;

  return (
    <div className="page-container" ref={pageRef}>
      <div className="page-header">
        <h1>
          Welcome back,{' '}
          {user?.first_name || user?.username}
        </h1>
        <p className="text-muted mt-sm">
          Here is your current balance across all groups
        </p>
      </div>

      {/* Stats */}
      <div className="stat-grid">
        <StatCard
          label="You are owed"
          value={`+₹${totalOwed.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`}
          valueClass="positive"
          icon="↑"
        />
        <StatCard
          label="You owe"
          value={`-₹${totalOwe.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`}
          valueClass="negative"
          icon="↓"
        />
        <StatCard
          label="Net balance"
          value={`${net >= 0 ? '+' : ''}₹${Math.abs(net).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`}
          valueClass={net >= 0 ? 'positive' : 'negative'}
          icon="="
        />
        <StatCard
          label="Groups"
          value={groups.length}
          icon="G"
        />
      </div>

      {/* Groups grid */}
      <div className="flex items-center justify-between mb-md">
        <h2>Your Groups</h2>
        <button
          className="btn btn-primary btn-sm"
          id="new-group-btn"
          onClick={() => navigate('/groups/new')}
        >
          + New Group
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center" style={{ padding: '60px' }}>
          <span className="spinner spinner-lg" />
        </div>
      ) : groups.length === 0 ? (
        <div className="empty-state card">
          <div className="empty-state-icon">G</div>
          <h3>No groups yet</h3>
          <p>Create your first group to start tracking shared expenses with your flatmates.</p>
          <button
            className="btn btn-primary"
            onClick={() => navigate('/groups/new')}
          >
            Create Group
          </button>
        </div>
      ) : (
        <div className="grid-2">
          {groups.map((g) => (
            <GroupCard
              key={g.id}
              group={g}
              onClick={() => navigate(`/groups/${g.id}`)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
