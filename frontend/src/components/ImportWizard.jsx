import { useRef, useState } from 'react';
import { importApi } from '../services/api';

const SEVERITY_COLOR = {
  info:     'badge-muted',
  warning:  'badge-warning',
  error:    'badge-danger',
  critical: 'badge-danger',
};

const TYPE_LABEL = {
  duplicate:           'Duplicate',
  missing_field:       'Missing Field',
  format_error:        'Format',
  math_error:          'Math Error',
  name_mismatch:       'Name Mismatch',
  date_error:          'Date Error',
  negative_amount:     'Negative Amount',
  zero_amount:         'Zero Amount',
  membership_violation:'Membership',
  misclassification:   'Misclassified',
  conflicting_data:    'Conflict',
  rounding:            'Rounding',
  currency_missing:    'Currency Missing',
  other:               'Other',
};

// ─── Step indicator ───────────────────────────────────────────────
function StepBar({ step }) {
  const steps = ['Upload', 'Review', 'Confirm'];
  return (
    <div className="flex items-center gap-sm mb-xl" style={{ justifyContent: 'center' }}>
      {steps.map((label, i) => (
        <div key={i} className="flex items-center gap-sm">
          <div style={{
            width: 28, height: 28, borderRadius: '50%',
            background: i + 1 <= step ? 'var(--accent)' : 'var(--bg-elevated)',
            border: `2px solid ${i + 1 <= step ? 'var(--accent)' : 'var(--border)'}`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '0.75rem', fontWeight: 700,
            color: i + 1 <= step ? 'var(--text-on-accent)' : 'var(--text-muted)',
            transition: 'all 0.3s ease',
          }}>
            {i + 1}
          </div>
          <span style={{
            fontSize: '0.8rem', fontWeight: 600,
            color: i + 1 === step ? 'var(--text-primary)' : 'var(--text-muted)',
          }}>
            {label}
          </span>
          {i < steps.length - 1 && (
            <div style={{ width: 40, height: 1, background: i + 1 < step ? 'var(--accent)' : 'var(--border)' }} />
          )}
        </div>
      ))}
    </div>
  );
}

// ─── Step 1: Upload ───────────────────────────────────────────────
function UploadStep({ onUploaded, groupId, importApi }) {
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const inputRef = useRef(null);

  const handleFile = async (file) => {
    if (!file || !file.name.endsWith('.csv')) {
      setError('Please upload a .csv file.');
      return;
    }
    setLoading(true);
    setError('');
    const fd = new FormData();
    fd.append('file', file);
    try {
      const { data } = await importApi.upload(groupId, fd);
      onUploaded(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 520, margin: '0 auto' }}>
      <div
        id="csv-dropzone"
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          handleFile(e.dataTransfer.files[0]);
        }}
        style={{
          border: `2px dashed ${dragging ? 'var(--accent)' : 'var(--border)'}`,
          borderRadius: 'var(--radius-lg)',
          padding: '48px 32px',
          textAlign: 'center',
          cursor: 'pointer',
          transition: 'all 0.2s ease',
          background: dragging ? 'var(--bg-elevated)' : 'var(--bg-card)',
        }}
      >
        <div style={{ fontSize: '2.5rem', marginBottom: '16px', opacity: 0.6 }}>
          {loading ? '⏳' : '📄'}
        </div>
        <h3 style={{ marginBottom: '8px' }}>
          {loading ? 'Parsing CSV...' : 'Drop your CSV file here'}
        </h3>
        <p className="text-sm text-muted">
          {loading ? 'Detecting anomalies...' : 'or click to browse — only .csv files accepted'}
        </p>
        <input
          ref={inputRef}
          type="file"
          accept=".csv"
          style={{ display: 'none' }}
          onChange={(e) => handleFile(e.target.files[0])}
          id="csv-file-input"
        />
      </div>

      {error && <div className="auth-error mt-md">{error}</div>}

      <div className="card mt-lg" style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
        <p style={{ fontWeight: 600, marginBottom: '8px', color: 'var(--text-primary)' }}>
          Expected CSV columns:
        </p>
        <code style={{ color: 'var(--accent)' }}>
          date, description, paid_by, amount, currency, split_type, split_with, split_details, notes
        </code>
        <p style={{ marginTop: '8px' }}>
          The parser will detect 14+ types of data issues and flag them for your review.
        </p>
      </div>
    </div>
  );
}

// ─── Anomaly badge ────────────────────────────────────────────────
function AnomalyBadge({ anomaly }) {
  return (
    <div style={{
      padding: '8px 12px',
      background: 'var(--bg-surface)',
      border: `1px solid var(--border)`,
      borderLeft: `3px solid ${
        anomaly.severity === 'error' || anomaly.severity === 'critical' ? 'var(--danger)' :
        anomaly.severity === 'warning' ? 'var(--warning)' : 'var(--text-muted)'
      }`,
      borderRadius: 'var(--radius-sm)',
      marginBottom: '6px',
    }}>
      <div className="flex items-center gap-sm" style={{ marginBottom: '4px' }}>
        <span className={`badge ${SEVERITY_COLOR[anomaly.severity]}`}>
          {anomaly.severity}
        </span>
        <span className="badge badge-muted">{TYPE_LABEL[anomaly.anomaly_type] || anomaly.anomaly_type}</span>
        {anomaly.auto_fixed && <span className="badge badge-success">auto-fixed</span>}
        {anomaly.field_name && <span className="text-xs text-muted">field: {anomaly.field_name}</span>}
      </div>
      <p className="text-sm" style={{ marginBottom: anomaly.suggested_action ? '4px' : 0 }}>
        {anomaly.description}
      </p>
      {anomaly.suggested_action && (
        <p className="text-xs text-muted">{anomaly.suggested_action}</p>
      )}
    </div>
  );
}

// ─── Step 2: Review ───────────────────────────────────────────────
function ReviewStep({ uploadResult, rowDecisions, setRowDecisions, onConfirm }) {
  const { rows = [], total_rows, needs_review, auto_ok, anomaly_count } = uploadResult;
  const [filter, setFilter] = useState('all'); // all | issues | clean | settlement
  const [expandedRow, setExpandedRow] = useState(null);

  const decisionFor = (rowNum) => rowDecisions[rowNum] || (
    rows.find(r => r.row_number === rowNum)?.is_settlement ? 'settlement' :
    rows.find(r => r.row_number === rowNum)?.is_valid ? 'import' : 'skip'
  );

  const setDecision = (rowNum, val) => {
    setRowDecisions(prev => ({ ...prev, [rowNum]: val }));
  };

  const filtered = rows.filter(r => {
    if (r.skip) return false;
    if (filter === 'issues') return r.needs_review;
    if (filter === 'clean') return !r.needs_review && r.is_valid;
    if (filter === 'settlement') return r.is_settlement;
    return true;
  });

  const pendingDecisions = rows.filter(r => !r.skip && r.needs_review && decisionFor(r.row_number) === 'skip').length;

  return (
    <div>
      {/* Summary stats */}
      <div className="stat-grid mb-lg">
        <div className="card"><div className="card-title">Total Rows</div><div className="card-value">{total_rows}</div></div>
        <div className="card"><div className="card-title">Ready to Import</div><div className="card-value" style={{color:'var(--accent)'}}>{auto_ok}</div></div>
        <div className="card"><div className="card-title">Need Review</div><div className="card-value" style={{color:'var(--warning)'}}>{needs_review}</div></div>
        <div className="card"><div className="card-title">Anomalies Found</div><div className="card-value" style={{color:'var(--danger)'}}>{anomaly_count}</div></div>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-sm mb-md" style={{ flexWrap: 'wrap' }}>
        {[
          ['all', `All (${rows.filter(r=>!r.skip).length})`],
          ['issues', `Issues (${rows.filter(r=>r.needs_review&&!r.skip).length})`],
          ['clean', `Clean (${rows.filter(r=>!r.needs_review&&r.is_valid&&!r.skip).length})`],
          ['settlement', `Settlements (${rows.filter(r=>r.is_settlement&&!r.skip).length})`],
        ].map(([val, label]) => (
          <button
            key={val}
            className={`btn btn-sm ${filter === val ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setFilter(val)}
          >
            {label}
          </button>
        ))}
        <button
          className="btn btn-secondary btn-sm"
          style={{ marginLeft: 'auto' }}
          onClick={() => {
            const decisions = {};
            rows.forEach(r => {
              if (!r.skip) {
                decisions[r.row_number] = r.is_settlement ? 'settlement' : r.is_valid ? 'import' : 'skip';
              }
            });
            setRowDecisions(decisions);
          }}
        >
          Auto-decide all
        </button>
      </div>

      {/* Rows table */}
      <div className="table-wrapper mb-lg">
        <table>
          <thead>
            <tr>
              <th style={{width: 48}}>Row</th>
              <th>Description</th>
              <th>Date</th>
              <th>Amount</th>
              <th>Paid By</th>
              <th>Status</th>
              <th>Decision</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(row => {
              const decision = decisionFor(row.row_number);
              const isExpanded = expandedRow === row.row_number;
              return [
                <tr
                  key={row.row_number}
                  id={`import-row-${row.row_number}`}
                  style={{ cursor: row.anomalies.length > 0 ? 'pointer' : 'default' }}
                  onClick={() => row.anomalies.length > 0 && setExpandedRow(isExpanded ? null : row.row_number)}
                >
                  <td className="font-mono text-xs" style={{color:'var(--text-muted)'}}>{row.row_number}</td>
                  <td>
                    <div style={{ fontWeight: 500 }}>{row.description || <span className="text-muted">—</span>}</div>
                    {row.is_settlement && <span className="badge badge-warning" style={{marginTop:2}}>settlement</span>}
                  </td>
                  <td className="text-sm text-muted">{row.date || row.date_raw || '—'}</td>
                  <td className="font-mono text-sm">
                    {row.amount ? `${row.currency === 'INR' ? '₹' : '$'}${parseFloat(row.amount).toLocaleString()}` : '—'}
                  </td>
                  <td className="text-sm">{row.paid_by_normalized || row.paid_by || '—'}</td>
                  <td>
                    {row.anomalies.length === 0 ? (
                      <span className="badge badge-success">Clean</span>
                    ) : (
                      <span className="badge badge-danger">{row.anomalies.length} issue{row.anomalies.length > 1 ? 's' : ''}</span>
                    )}
                  </td>
                  <td onClick={e => e.stopPropagation()}>
                    <select
                      className="form-select"
                      style={{ padding: '4px 8px', fontSize: '0.8rem', width: '120px' }}
                      value={decision}
                      onChange={e => setDecision(row.row_number, e.target.value)}
                      id={`decision-${row.row_number}`}
                    >
                      <option value="import">Import</option>
                      <option value="settlement">As Settlement</option>
                      <option value="skip">Skip</option>
                    </select>
                  </td>
                </tr>,
                isExpanded && (
                  <tr key={`${row.row_number}-expanded`} style={{ background: 'var(--bg-surface)' }}>
                    <td colSpan={7} style={{ padding: '12px 16px' }}>
                      <p className="text-xs text-muted mb-md" style={{ fontWeight: 600 }}>
                        ANOMALIES FOR ROW {row.row_number}
                      </p>
                      {row.anomalies.map((a, i) => <AnomalyBadge key={i} anomaly={a} />)}
                      {row.split_with?.length > 0 && (
                        <p className="text-xs text-muted mt-md">
                          Split with: {row.split_with.join(', ')}
                        </p>
                      )}
                      {row.notes && <p className="text-xs text-muted">Notes: {row.notes}</p>}
                    </td>
                  </tr>
                ),
              ];
            })}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between">
        <p className="text-sm text-muted">
          Click any row with issues to expand anomaly details. Set decision per row.
        </p>
        <button
          className="btn btn-primary"
          id="confirm-import-btn"
          onClick={onConfirm}
        >
          Confirm Decisions &amp; Import
        </button>
      </div>
    </div>
  );
}

// ─── Step 3: Confirm (result) ─────────────────────────────────────
function ResultStep({ result, onDone }) {
  if (!result) return null;
  const { created_expenses, created_settlements, skipped_rows, errors } = result;
  return (
    <div style={{ maxWidth: 480, margin: '0 auto', textAlign: 'center' }}>
      <div style={{ fontSize: '3rem', marginBottom: '16px' }}>
        {errors?.length === 0 ? '✓' : '!'}
      </div>
      <h2 style={{ marginBottom: '8px' }}>Import Complete</h2>
      <p className="text-muted mb-xl">Your CSV data has been imported.</p>

      <div className="stat-grid mb-lg" style={{ gridTemplateColumns: '1fr 1fr 1fr' }}>
        <div className="card"><div className="card-title">Expenses</div><div className="card-value positive">{created_expenses}</div></div>
        <div className="card"><div className="card-title">Settlements</div><div className="card-value positive">{created_settlements}</div></div>
        <div className="card"><div className="card-title">Skipped</div><div className="card-value">{skipped_rows}</div></div>
      </div>

      {errors?.length > 0 && (
        <div className="card mb-lg" style={{ textAlign: 'left' }}>
          <p className="text-sm" style={{ fontWeight: 600, color: 'var(--warning)', marginBottom: '8px' }}>
            {errors.length} row(s) had errors:
          </p>
          {errors.map((e, i) => (
            <p key={i} className="text-xs text-muted" style={{ marginBottom: '4px' }}>{e}</p>
          ))}
        </div>
      )}

      <button className="btn btn-primary btn-lg" id="import-done-btn" onClick={onDone}>
        Go to Group
      </button>
    </div>
  );
}

// ─── Main wizard ──────────────────────────────────────────────────
export default function ImportWizard({ group, onClose, onComplete }) {
  const [step, setStep] = useState(1);
  const [uploadResult, setUploadResult] = useState(null);
  const [rowDecisions, setRowDecisions] = useState({});
  const [finalizing, setFinalizing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const modalRef = useRef(null);

  const handleUploaded = (data) => {
    setUploadResult(data);
    setStep(2);
    // Pre-populate default decisions
    const defaults = {};
    data.rows.forEach(r => {
      if (!r.skip) {
        defaults[r.row_number] = r.is_settlement ? 'settlement' : r.is_valid ? 'import' : 'skip';
      }
    });
    setRowDecisions(defaults);
  };

  const handleFinalize = async () => {
    setFinalizing(true);
    setError('');
    try {
      const { data } = await importApi.finalize(
        group.id, uploadResult.report_id, rowDecisions
      );
      setResult(data);
      setStep(3);
    } catch (err) {
      setError(err.response?.data?.detail || 'Finalization failed.');
    } finally {
      setFinalizing(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div
        ref={modalRef}
        style={{
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-xl)',
          padding: '32px',
          width: '95%',
          maxWidth: step === 2 ? '960px' : '560px',
          maxHeight: '90vh',
          overflowY: 'auto',
          boxShadow: 'var(--shadow-lg)',
        }}
      >
        <div className="flex items-center justify-between mb-lg">
          <h2>Import CSV Expenses</h2>
          <button className="btn btn-ghost btn-icon" onClick={onClose}>✕</button>
        </div>

        <StepBar step={step} />

        {error && <div className="auth-error mb-md">{error}</div>}

        {step === 1 && (
          <UploadStep
            groupId={group.id}
            importApi={importApi}
            onUploaded={handleUploaded}
          />
        )}

        {step === 2 && uploadResult && (
          <ReviewStep
            uploadResult={uploadResult}
            rowDecisions={rowDecisions}
            setRowDecisions={setRowDecisions}
            onConfirm={handleFinalize}
          />
        )}

        {step === 3 && (
          <ResultStep
            result={result}
            onDone={() => { onClose(); onComplete(); }}
          />
        )}

        {step === 2 && finalizing && (
          <div style={{ textAlign: 'center', padding: '16px' }}>
            <span className="spinner spinner-lg" />
            <p className="text-muted mt-md">Importing rows...</p>
          </div>
        )}
      </div>
    </div>
  );
}
