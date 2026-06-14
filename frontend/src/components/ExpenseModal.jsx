import { useState, useRef, useEffect } from 'react';
import { gsap } from 'gsap';
import { useAuth } from '../context/AuthContext';
import { expensesApi } from '../services/api';

const SPLIT_TYPES = [
  { value: 'equal',      label: 'Equal',      hint: 'Divide equally among everyone' },
  { value: 'unequal',    label: 'Unequal',    hint: 'Specify exact amount per person' },
  { value: 'percentage', label: 'Percentage', hint: 'Specify % per person (auto-normalizes)' },
  { value: 'share',      label: 'Shares',     hint: 'Give relative shares (e.g. 2x for bigger portion)' },
];

export default function ExpenseModal({ group, members, onClose, onSaved }) {
  const { user } = useAuth();
  const modalRef = useRef(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [form, setForm] = useState({
    description: '',
    amount: '',
    currency: 'INR',
    split_type: 'equal',
    expense_date: new Date().toISOString().split('T')[0],
    notes: '',
    paid_by_username: user?.username || '',
  });

  // Per-person split detail values
  const [splitDetails, setSplitDetails] = useState({});
  // Which members are included in this split
  const memberUsernames = members.map((m) => m.user.username);
  const [selectedMembers, setSelectedMembers] = useState(memberUsernames);

  useEffect(() => {
    gsap.fromTo(
      modalRef.current,
      { scale: 0.95, opacity: 0 },
      { scale: 1, opacity: 1, duration: 0.25, ease: 'power3.out' }
    );
  }, []);

  const handleChange = (e) => {
    setForm((p) => ({ ...p, [e.target.name]: e.target.value }));
    if (error) setError('');
  };

  const toggleMember = (username) => {
    setSelectedMembers((prev) =>
      prev.includes(username) ? prev.filter((u) => u !== username) : [...prev, username]
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.description.trim()) { setError('Description is required.'); return; }
    if (!form.amount || isNaN(form.amount)) { setError('Valid amount is required.'); return; }
    if (selectedMembers.length === 0) { setError('Select at least one member.'); return; }

    const payload = {
      description: form.description,
      amount: parseFloat(form.amount),
      currency: form.currency,
      split_type: form.split_type,
      expense_date: form.expense_date,
      notes: form.notes,
      paid_by_username: form.paid_by_username,
      split_with: selectedMembers,
      split_details: form.split_type === 'equal' ? {} : splitDetails,
    };

    setLoading(true);
    try {
      await expensesApi.create(group.id, payload);
      onSaved();
    } catch (err) {
      const msg = err.response?.data?.detail || JSON.stringify(err.response?.data) || 'Failed to add expense.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const needsDetails = form.split_type !== 'equal';
  const splitHint = SPLIT_TYPES.find((t) => t.value === form.split_type)?.hint;
  const detailLabel = { unequal: 'Amount (₹)', percentage: 'Percentage (%)', share: 'Share count' }[form.split_type];

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal" ref={modalRef}>
        <div className="modal-header">
          <span className="modal-title">Add Expense</span>
          <button className="btn btn-ghost btn-icon" onClick={onClose}>✕</button>
        </div>

        {error && <div className="auth-error" style={{ marginBottom: '16px' }}>{error}</div>}

        <form onSubmit={handleSubmit} id="expense-form">
          <div className="form-group">
            <label className="form-label" htmlFor="exp-description">Description</label>
            <input id="exp-description" name="description" className="form-input"
              placeholder="e.g. Grocery run" value={form.description} onChange={handleChange} autoFocus />
          </div>

          <div className="grid-2">
            <div className="form-group">
              <label className="form-label" htmlFor="exp-amount">Amount</label>
              <input id="exp-amount" name="amount" type="number" step="0.01" className="form-input"
                placeholder="0.00" value={form.amount} onChange={handleChange} />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="exp-currency">Currency</label>
              <select id="exp-currency" name="currency" className="form-select" value={form.currency} onChange={handleChange}>
                <option value="INR">INR (₹)</option>
                <option value="USD">USD ($)</option>
              </select>
            </div>
          </div>

          <div className="grid-2">
            <div className="form-group">
              <label className="form-label" htmlFor="exp-date">Date</label>
              <input id="exp-date" name="expense_date" type="date" className="form-input"
                value={form.expense_date} onChange={handleChange} />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="exp-paid-by">Paid By</label>
              <select id="exp-paid-by" name="paid_by_username" className="form-select"
                value={form.paid_by_username} onChange={handleChange}>
                {members.map((m) => (
                  <option key={m.id} value={m.user.username}>{m.user.username}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="exp-split-type">Split Type</label>
            <select id="exp-split-type" name="split_type" className="form-select"
              value={form.split_type} onChange={handleChange}>
              {SPLIT_TYPES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
            <span className="text-xs text-muted" style={{ marginTop: '4px' }}>{splitHint}</span>
          </div>

          {/* Member selection + per-person details */}
          <div className="form-group">
            <label className="form-label">
              Split With {needsDetails ? `(enter ${detailLabel})` : ''}
            </label>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {members.map((m) => {
                const uname = m.user.username;
                const checked = selectedMembers.includes(uname);
                return (
                  <div key={m.id} className="flex items-center gap-md"
                    style={{ padding: '8px', borderRadius: 'var(--radius-md)',
                      background: checked ? 'var(--accent-glow-sm)' : 'var(--bg-input)',
                      border: `1px solid ${checked ? 'var(--border-active)' : 'var(--border)'}`,
                      cursor: 'pointer' }}
                    onClick={() => toggleMember(uname)}
                  >
                    <div style={{
                      width: 18, height: 18, borderRadius: '4px',
                      border: `2px solid ${checked ? 'var(--accent)' : 'var(--border)'}`,
                      background: checked ? 'var(--accent)' : 'transparent',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: '0.7rem', color: 'var(--text-on-accent)', flexShrink: 0,
                      transition: 'all 0.15s ease',
                    }}>
                      {checked && '✓'}
                    </div>
                    <span className="text-sm flex-1" style={{ fontWeight: 500 }}>{uname}</span>
                    {needsDetails && checked && (
                      <input
                        type="number"
                        step="0.01"
                        className="form-input"
                        style={{ width: '100px', padding: '4px 8px', fontSize: '0.85rem' }}
                        placeholder={detailLabel}
                        value={splitDetails[uname] || ''}
                        onChange={(e) => {
                          e.stopPropagation();
                          setSplitDetails((p) => ({ ...p, [uname]: e.target.value }));
                        }}
                        onClick={(e) => e.stopPropagation()}
                      />
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="exp-notes">Notes (optional)</label>
            <input id="exp-notes" name="notes" className="form-input"
              placeholder="Any extra info..." value={form.notes} onChange={handleChange} />
          </div>

          <div className="flex gap-sm" style={{ marginTop: '8px' }}>
            <button type="submit" id="expense-submit" className="btn btn-primary flex-1" disabled={loading}>
              {loading ? <><span className="spinner" /> Adding...</> : 'Add Expense'}
            </button>
            <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
          </div>
        </form>
      </div>
    </div>
  );
}
