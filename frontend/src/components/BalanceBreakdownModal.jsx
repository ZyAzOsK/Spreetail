import { useEffect, useRef, useState } from 'react';
import { gsap } from 'gsap';
import { balancesApi } from '../services/api';

export default function BalanceBreakdownModal({ groupId, onClose }) {
  const modalRef = useRef(null);
  const [breakdown, setBreakdown] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    gsap.fromTo(
      modalRef.current,
      { scale: 0.95, opacity: 0 },
      { scale: 1, opacity: 1, duration: 0.25, ease: 'power3.out' }
    );
  }, []);

  useEffect(() => {
    balancesApi.breakdown(groupId)
      .then((res) => {
        setBreakdown(res.data.breakdown);
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, [groupId]);

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal" ref={modalRef} style={{ maxWidth: '600px', maxHeight: '80vh', display: 'flex', flexDirection: 'column' }}>
        <div className="modal-header">
          <span className="modal-title">Your Balance Breakdown</span>
          <button className="btn btn-ghost btn-icon" onClick={onClose}>✕</button>
        </div>

        <p className="text-sm text-muted mb-md">
          A trace of exactly which expenses make up your current balance.
        </p>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '32px' }}>
            <span className="spinner" />
          </div>
        ) : !breakdown || breakdown.length === 0 ? (
          <div className="empty-state" style={{ padding: '32px' }}>
            <p>No expenses affect your balance yet.</p>
          </div>
        ) : (
          <div style={{ overflowY: 'auto', flex: 1 }}>
            <table style={{ width: '100%', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border)', textAlign: 'left' }}>
                  <th style={{ padding: '8px' }}>Date</th>
                  <th style={{ padding: '8px' }}>Description</th>
                  <th style={{ padding: '8px' }}>Total</th>
                  <th style={{ padding: '8px' }}>Your Share</th>
                  <th style={{ padding: '8px', textAlign: 'right' }}>Net Effect</th>
                </tr>
              </thead>
              <tbody>
                {breakdown.map((item, i) => {
                  const net = parseFloat(item.net_effect);
                  const isPositive = net > 0;
                  return (
                    <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                      <td style={{ padding: '8px', color: 'var(--text-muted)' }}>{item.date}</td>
                      <td style={{ padding: '8px' }}>
                        <div style={{ fontWeight: 500 }}>{item.description}</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                          Paid by {item.paid_by}
                        </div>
                      </td>
                      <td style={{ padding: '8px' }}>
                        {item.currency === 'INR' ? '₹' : '$'}{parseFloat(item.total).toFixed(2)}
                      </td>
                      <td style={{ padding: '8px' }}>
                        ₹{parseFloat(item.your_share).toFixed(2)}
                      </td>
                      <td style={{ padding: '8px', textAlign: 'right', fontWeight: 600, color: isPositive ? 'var(--accent)' : 'var(--danger)' }}>
                        {isPositive ? '+' : ''}₹{net.toFixed(2)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
