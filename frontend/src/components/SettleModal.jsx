import { useState, useRef, useEffect } from 'react';
import { gsap } from 'gsap';
import { useAuth } from '../context/AuthContext';
import { settlementsApi } from '../services/api';

export default function SettleModal({ group, members, onClose, onSaved }) {
  const { user } = useAuth();
  const modalRef = useRef(null);
  const [form, setForm] = useState({
    amount: '',
    currency: 'INR',
    settlement_date: new Date().toISOString().split('T')[0],
    paid_to_username: '',
    notes: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    gsap.fromTo(modalRef.current, { scale: 0.95, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.25, ease: 'power3.out' });
  }, []);

  const otherMembers = members.filter((m) => m.user.username !== user?.username);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.paid_to_username) { setError('Select who you paid.'); return; }
    if (!form.amount || isNaN(form.amount) || parseFloat(form.amount) <= 0) {
      setError('Enter a valid amount.'); return;
    }
    setLoading(true);
    try {
      await settlementsApi.create(group.id, {
        ...form,
        amount: parseFloat(form.amount),
      });
      onSaved();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to record settlement.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal" ref={modalRef} style={{ maxWidth: '400px' }}>
        <div className="modal-header">
          <span className="modal-title">Record Settlement</span>
          <button className="btn btn-ghost btn-icon" onClick={onClose}>✕</button>
        </div>

        <p className="text-sm text-muted mb-md">
          Record a payment you made to clear a debt.
        </p>

        {error && <div className="auth-error" style={{ marginBottom: '16px' }}>{error}</div>}

        <form onSubmit={handleSubmit} id="settle-form">
          <div className="form-group">
            <label className="form-label" htmlFor="settle-paid-to">I paid</label>
            <select
              id="settle-paid-to"
              className="form-select"
              value={form.paid_to_username}
              onChange={(e) => setForm((p) => ({ ...p, paid_to_username: e.target.value }))}
            >
              <option value="">-- Select person --</option>
              {otherMembers.map((m) => (
                <option key={m.id} value={m.user.username}>{m.user.username}</option>
              ))}
            </select>
          </div>

          <div className="grid-2">
            <div className="form-group">
              <label className="form-label" htmlFor="settle-amount">Amount</label>
              <input
                id="settle-amount"
                type="number"
                step="0.01"
                className="form-input"
                placeholder="0.00"
                value={form.amount}
                onChange={(e) => setForm((p) => ({ ...p, amount: e.target.value }))}
              />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="settle-currency">Currency</label>
              <select
                id="settle-currency"
                className="form-select"
                value={form.currency}
                onChange={(e) => setForm((p) => ({ ...p, currency: e.target.value }))}
              >
                <option value="INR">INR (₹)</option>
                <option value="USD">USD ($)</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="settle-date">Date</label>
            <input
              id="settle-date"
              type="date"
              className="form-input"
              value={form.settlement_date}
              onChange={(e) => setForm((p) => ({ ...p, settlement_date: e.target.value }))}
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="settle-notes">Notes (optional)</label>
            <input
              id="settle-notes"
              className="form-input"
              placeholder="Paid via UPI..."
              value={form.notes}
              onChange={(e) => setForm((p) => ({ ...p, notes: e.target.value }))}
            />
          </div>

          <div className="flex gap-sm">
            <button type="submit" id="settle-submit" className="btn btn-primary flex-1" disabled={loading}>
              {loading ? <><span className="spinner" /> Recording...</> : 'Record Payment'}
            </button>
            <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
          </div>
        </form>
      </div>
    </div>
  );
}
