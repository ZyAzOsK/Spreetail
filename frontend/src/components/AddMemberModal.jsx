import { useState, useRef, useEffect } from 'react';
import { gsap } from 'gsap';
import { groupsApi, authApi } from '../services/api';

export default function AddMemberModal({ group, onClose, onSaved }) {
  const modalRef = useRef(null);
  const [username, setUsername] = useState('');
  const [joinedAt, setJoinedAt] = useState(new Date().toISOString().split('T')[0]);
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    gsap.fromTo(modalRef.current, { scale: 0.95, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.25, ease: 'power3.out' });
  }, []);

  // Debounced user search
  useEffect(() => {
    if (username.length < 2) { setSearchResults([]); return; }
    const timer = setTimeout(async () => {
      setSearching(true);
      try {
        const { data } = await authApi.searchUsers(username);
        setSearchResults(data.results);
      } finally {
        setSearching(false);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [username]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username.trim()) { setError('Username is required.'); return; }
    if (!joinedAt) { setError('Join date is required.'); return; }
    setLoading(true);
    try {
      await groupsApi.addMember(group.id, { username, joined_at: joinedAt });
      onSaved();
    } catch (err) {
      const msg = err.response?.data?.detail || JSON.stringify(err.response?.data) || 'Failed to add member.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal" ref={modalRef} style={{ maxWidth: '400px' }}>
        <div className="modal-header">
          <span className="modal-title">Add Member</span>
          <button className="btn btn-ghost btn-icon" onClick={onClose}>✕</button>
        </div>

        {error && <div className="auth-error" style={{ marginBottom: '16px' }}>{error}</div>}

        <form onSubmit={handleSubmit} id="add-member-form">
          <div className="form-group" style={{ position: 'relative' }}>
            <label className="form-label" htmlFor="member-username">Search Username</label>
            <input
              id="member-username"
              className="form-input"
              placeholder="Type to search..."
              value={username}
              onChange={(e) => { setUsername(e.target.value); setError(''); }}
              autoFocus
              autoComplete="off"
            />
            {searchResults.length > 0 && (
              <div style={{
                position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 10,
                background: 'var(--bg-elevated)', border: '1px solid var(--border)',
                borderRadius: 'var(--radius-md)', overflow: 'hidden', marginTop: '4px',
              }}>
                {searchResults.map((u) => (
                  <div
                    key={u.id}
                    style={{ padding: '10px 14px', cursor: 'pointer', fontSize: '0.875rem' }}
                    onMouseDown={() => { setUsername(u.username); setSearchResults([]); }}
                    onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bg-card)'}
                    onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                  >
                    <span style={{ fontWeight: 600 }}>{u.username}</span>
                    {u.first_name && <span className="text-muted" style={{ marginLeft: '8px' }}>{u.first_name} {u.last_name}</span>}
                  </div>
                ))}
              </div>
            )}
            {searching && <span className="text-xs text-muted" style={{ marginTop: '4px' }}>Searching...</span>}
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="member-joined">Join Date</label>
            <input
              id="member-joined"
              type="date"
              className="form-input"
              value={joinedAt}
              onChange={(e) => setJoinedAt(e.target.value)}
            />
            <span className="text-xs text-muted" style={{ marginTop: '4px' }}>
              Used for balance calculations — expenses before this date won&apos;t affect them.
            </span>
          </div>

          <div className="flex gap-sm">
            <button type="submit" id="add-member-submit" className="btn btn-primary flex-1" disabled={loading}>
              {loading ? <><span className="spinner" /> Adding...</> : 'Add Member'}
            </button>
            <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
          </div>
        </form>
      </div>
    </div>
  );
}
