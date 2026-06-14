import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { gsap } from 'gsap';
import { useToast } from '../context/ToastContext';
import { groupsApi } from '../services/api';

export default function GroupsListPage() {
  const navigate = useNavigate();
  const { success, error: toastError } = useToast();
  const pageRef = useRef(null);
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ name: '', description: '' });
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    groupsApi.list()
      .then(({ data }) => setGroups(data))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!loading && pageRef.current) {
      gsap.fromTo(
        pageRef.current.querySelectorAll('.card'),
        { y: 20, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.4, stagger: 0.07, ease: 'power3.out' }
      );
    }
  }, [loading]);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) return;
    setCreating(true);
    try {
      const { data } = await groupsApi.create(form);
      success('Group created!');
      navigate(`/groups/${data.id}`);
    } catch {
      toastError('Failed to create group.');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="page-container" ref={pageRef}>
      <div className="page-header flex items-center justify-between">
        <h1>All Groups</h1>
        <button
          className="btn btn-primary"
          id="create-group-btn"
          onClick={() => setShowCreate((v) => !v)}
        >
          {showCreate ? 'Cancel' : '+ New Group'}
        </button>
      </div>

      {showCreate && (
        <div className="card mb-lg">
          <h3 className="mb-md">Create a New Group</h3>
          <form onSubmit={handleCreate}>
            <div className="form-group">
              <label className="form-label" htmlFor="new-group-name">Group Name</label>
              <input
                id="new-group-name"
                className="form-input"
                placeholder="e.g. Flat 4B"
                value={form.name}
                onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
                autoFocus
              />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="new-group-desc">Description (optional)</label>
              <input
                id="new-group-desc"
                className="form-input"
                placeholder="Our flat group"
                value={form.description}
                onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))}
              />
            </div>
            <div className="flex gap-sm">
              <button type="submit" className="btn btn-primary" disabled={creating}>
                {creating ? <><span className="spinner" /> Creating...</> : 'Create Group'}
              </button>
              <button type="button" className="btn btn-secondary" onClick={() => setShowCreate(false)}>
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center" style={{ padding: '60px' }}>
          <span className="spinner spinner-lg" />
        </div>
      ) : groups.length === 0 ? (
        <div className="empty-state card">
          <div className="empty-state-icon">G</div>
          <h3>No groups yet</h3>
          <p>Create your first group to start splitting expenses.</p>
        </div>
      ) : (
        <div className="grid-2">
          {groups.map((g) => {
            const members = g.memberships?.filter((m) => m.is_active) || [];
            return (
              <div
                key={g.id}
                id={`group-list-${g.id}`}
                className="card card-interactive"
                onClick={() => navigate(`/groups/${g.id}`)}
              >
                <h3 style={{ marginBottom: '6px' }}>{g.name}</h3>
                {g.description && <p className="text-sm text-muted mb-md">{g.description}</p>}
                <div className="flex items-center gap-md">
                  <span className="badge badge-muted">{members.length} members</span>
                  <span className="text-xs text-muted">{g.expense_count || 0} expenses</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
