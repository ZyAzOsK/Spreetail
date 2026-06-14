import { useEffect, useRef, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { gsap } from 'gsap';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { groupsApi, expensesApi, balancesApi, settlementsApi } from '../services/api';
import ExpenseModal from '../components/ExpenseModal';
import AddMemberModal from '../components/AddMemberModal';
import SettleModal from '../components/SettleModal';

// ---- Sub-components ----

function BalanceSummary({ balances, simplified, currentUser, onSettle }) {
  return (
    <div className="card mb-lg">
      <div className="card-header">
        <h3>Balances</h3>
        <button className="btn btn-secondary btn-sm" id="settle-btn" onClick={onSettle}>
          Record Settlement
        </button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '16px' }}>
        {balances.map((b) => {
          const bal = parseFloat(b.balance);
          const isMe = b.username === currentUser;
          return (
            <div
              key={b.user_id}
              className="flex items-center justify-between"
              style={{ padding: '8px 0', borderBottom: '1px solid var(--border)' }}
            >
              <div className="flex items-center gap-sm">
                <div
                  style={{
                    width: 28, height: 28, borderRadius: '50%',
                    background: 'linear-gradient(135deg, var(--accent-dim), var(--accent))',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: '0.65rem', fontWeight: 700, color: 'var(--text-on-accent)',
                  }}
                >
                  {b.username.slice(0, 2).toUpperCase()}
                </div>
                <span className="text-sm" style={{ fontWeight: isMe ? 700 : 500 }}>
                  {b.username}{isMe && ' (you)'}
                </span>
              </div>
              <span className={`balance-chip ${bal > 0.01 ? 'positive' : bal < -0.01 ? 'negative' : 'neutral'}`}>
                {bal > 0.01 ? `+₹${parseFloat(b.owed_to_you).toFixed(0)} owed` :
                 bal < -0.01 ? `-₹${parseFloat(b.you_owe).toFixed(0)} owes` :
                 'Settled'}
              </span>
            </div>
          );
        })}
      </div>

      {simplified.length > 0 && (
        <>
          <p className="text-sm text-muted mb-md" style={{ marginTop: '8px' }}>
            Simplified transactions to settle:
          </p>
          {simplified.map((tx, i) => (
            <div key={i} className="debt-card">
              <div className="flex items-center gap-sm flex-1">
                <div className="sidebar-avatar" style={{ width: 28, height: 28, fontSize: '0.65rem' }}>
                  {tx.from_username.slice(0, 2).toUpperCase()}
                </div>
                <span className="text-sm">{tx.from_username}</span>
                <span className="debt-arrow">→</span>
                <div className="sidebar-avatar" style={{ width: 28, height: 28, fontSize: '0.65rem' }}>
                  {tx.to_username.slice(0, 2).toUpperCase()}
                </div>
                <span className="text-sm">{tx.to_username}</span>
              </div>
              <span className="badge badge-accent">₹{parseFloat(tx.amount).toFixed(0)}</span>
            </div>
          ))}
        </>
      )}
    </div>
  );
}

function ExpenseRow({ expense, onDelete }) {
  const paid = expense.paid_by?.username;
  return (
    <tr id={`expense-row-${expense.id}`}>
      <td>
        <div style={{ fontWeight: 500 }}>{expense.description}</div>
        {expense.notes && (
          <div className="text-xs text-muted" style={{ marginTop: '2px' }}>{expense.notes}</div>
        )}
      </td>
      <td className="text-sm text-muted">{expense.expense_date}</td>
      <td>
        <span className="font-mono">
          {expense.currency === 'INR' ? '₹' : '$'}
          {parseFloat(expense.amount).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </span>
      </td>
      <td className="text-sm">{paid}</td>
      <td>
        <span className="badge badge-muted">{expense.split_type}</span>
      </td>
      <td>
        <button
          className="btn btn-danger btn-sm"
          onClick={() => onDelete(expense.id)}
          id={`delete-expense-${expense.id}`}
        >
          Delete
        </button>
      </td>
    </tr>
  );
}

// ---- Main Page ----

export default function GroupDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { success, error: toastError } = useToast();
  const pageRef = useRef(null);

  const [group, setGroup] = useState(null);
  const [expenses, setExpenses] = useState([]);
  const [balances, setBalances] = useState([]);
  const [simplified, setSimplified] = useState([]);
  const [loading, setLoading] = useState(true);

  const [showExpenseModal, setShowExpenseModal] = useState(false);
  const [showAddMemberModal, setShowAddMemberModal] = useState(false);
  const [showSettleModal, setShowSettleModal] = useState(false);

  const groupId = parseInt(id);

  // Guard: if id is not a valid number, redirect to groups list
  useEffect(() => {
    if (isNaN(groupId)) navigate('/groups', { replace: true });
  }, [groupId, navigate]);

  async function loadAll() {
    try {
      const [gRes, eRes, bRes] = await Promise.all([
        groupsApi.get(groupId),
        expensesApi.list(groupId),
        balancesApi.get(groupId),
      ]);
      setGroup(gRes.data);
      setExpenses(eRes.data);
      setBalances(bRes.data.balances);
      setSimplified(bRes.data.simplified_transactions);
    } catch (err) {
      if (err.response?.status === 403) navigate('/dashboard');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadAll(); }, [groupId]);

  useEffect(() => {
    if (!loading && pageRef.current) {
      gsap.fromTo(
        pageRef.current.querySelectorAll('.card'),
        { y: 20, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.4, stagger: 0.07, ease: 'power3.out' }
      );
    }
  }, [loading]);

  const handleDeleteExpense = async (expenseId) => {
    if (!confirm('Delete this expense?')) return;
    try {
      await expensesApi.delete(groupId, expenseId);
      success('Expense deleted');
      loadAll();
    } catch {
      toastError('Failed to delete expense');
    }
  };

  const activeMembers = group?.memberships?.filter((m) => m.is_active) || [];

  if (loading) {
    return (
      <div className="page-loader">
        <span className="spinner spinner-lg" />
        <span className="page-loader-text">Loading group...</span>
      </div>
    );
  }

  if (!group) return null;

  return (
    <div className="page-container" ref={pageRef}>
      {/* Page header */}
      <div className="page-header flex items-center justify-between">
        <div>
          <button className="btn btn-ghost btn-sm mb-md" onClick={() => navigate('/dashboard')}>
            ← Back
          </button>
          <h1>{group.name}</h1>
          {group.description && <p className="text-muted mt-sm">{group.description}</p>}
        </div>
        <div className="flex gap-sm">
          <button
            className="btn btn-secondary btn-sm"
            id="add-member-btn"
            onClick={() => setShowAddMemberModal(true)}
          >
            + Member
          </button>
          <button
            className="btn btn-primary btn-sm"
            id="add-expense-btn"
            onClick={() => setShowExpenseModal(true)}
          >
            + Expense
          </button>
        </div>
      </div>

      {/* Members strip */}
      <div className="card mb-lg">
        <div className="card-header">
          <h3>Members ({activeMembers.length})</h3>
        </div>
        <div className="flex gap-md" style={{ flexWrap: 'wrap' }}>
          {activeMembers.map((m) => (
            <div key={m.id} className="flex items-center gap-sm">
              <div className="sidebar-avatar" style={{ width: 32, height: 32, fontSize: '0.75rem' }}>
                {m.user.username.slice(0, 2).toUpperCase()}
              </div>
              <div>
                <div className="text-sm" style={{ fontWeight: 600 }}>{m.user.username}</div>
                <div className="text-xs text-muted">Joined {m.joined_at}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Balance Summary */}
      <BalanceSummary
        balances={balances}
        simplified={simplified}
        currentUser={user?.username}
        onSettle={() => setShowSettleModal(true)}
      />

      {/* Expenses Table */}
      <div className="card">
        <div className="card-header">
          <h3>Expenses ({expenses.length})</h3>
        </div>

        {expenses.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">$</div>
            <h3>No expenses yet</h3>
            <p>Add your first expense to start tracking.</p>
          </div>
        ) : (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Description</th>
                  <th>Date</th>
                  <th>Amount</th>
                  <th>Paid By</th>
                  <th>Split</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {expenses.map((e) => (
                  <ExpenseRow key={e.id} expense={e} onDelete={handleDeleteExpense} />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modals */}
      {showExpenseModal && (
        <ExpenseModal
          group={group}
          members={activeMembers}
          onClose={() => setShowExpenseModal(false)}
          onSaved={() => { setShowExpenseModal(false); loadAll(); success('Expense added'); }}
        />
      )}
      {showAddMemberModal && (
        <AddMemberModal
          group={group}
          onClose={() => setShowAddMemberModal(false)}
          onSaved={() => { setShowAddMemberModal(false); loadAll(); success('Member added'); }}
        />
      )}
      {showSettleModal && (
        <SettleModal
          group={group}
          members={activeMembers}
          onClose={() => setShowSettleModal(false)}
          onSaved={() => { setShowSettleModal(false); loadAll(); success('Settlement recorded'); }}
        />
      )}
    </div>
  );
}
