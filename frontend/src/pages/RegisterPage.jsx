import { useState, useRef, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { gsap } from 'gsap';

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    username: '', email: '', first_name: '', last_name: '',
    password: '', password_confirm: '',
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const cardRef = useRef(null);

  useEffect(() => {
    gsap.fromTo(
      cardRef.current,
      { y: 30, opacity: 0 },
      { y: 0, opacity: 1, duration: 0.6, ease: 'power3.out' }
    );
  }, []);

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    setErrors((prev) => ({ ...prev, [e.target.name]: '', general: '' }));
  };

  const validate = () => {
    const errs = {};
    if (!form.username.trim()) errs.username = 'Username is required.';
    if (!form.password) errs.password = 'Password is required.';
    if (form.password.length < 6) errs.password = 'Password must be at least 6 characters.';
    if (form.password !== form.password_confirm) errs.password_confirm = 'Passwords do not match.';
    return errs;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }

    setLoading(true);
    try {
      await register(form);
      navigate('/dashboard');
    } catch (err) {
      const data = err.response?.data || {};
      const mapped = {};
      Object.keys(data).forEach((key) => {
        mapped[key] = Array.isArray(data[key]) ? data[key][0] : data[key];
      });
      setErrors(mapped);
    } finally {
      setLoading(false);
    }
  };

  const field = (name, label, type = 'text', placeholder = '') => (
    <div className="form-group">
      <label className="form-label" htmlFor={`reg-${name}`}>{label}</label>
      <input
        id={`reg-${name}`}
        name={name}
        type={type}
        className={`form-input ${errors[name] ? 'error' : ''}`}
        placeholder={placeholder}
        value={form[name]}
        onChange={handleChange}
        autoComplete={type === 'password' ? 'new-password' : name}
      />
      {errors[name] && <span className="form-error">{errors[name]}</span>}
    </div>
  );

  return (
    <div className="auth-container">
      <div className="auth-card" ref={cardRef}>
        <div className="auth-logo">
          <div className="auth-logo-icon">F</div>
          <span className="auth-logo-name">FairShare</span>
        </div>

        <h1 className="auth-title">Create account</h1>
        <p className="auth-subtitle">Join your flatmates and track shared expenses</p>

        {errors.general && <div className="auth-error">{errors.general}</div>}

        <form onSubmit={handleSubmit} noValidate>
          <div className="grid-2">
            {field('first_name', 'First Name', 'text', 'Aisha')}
            {field('last_name',  'Last Name',  'text', 'Khan')}
          </div>
          {field('username', 'Username', 'text', 'aisha')}
          {field('email', 'Email (optional)', 'email', 'aisha@example.com')}
          {field('password', 'Password', 'password', 'Min 6 characters')}
          {field('password_confirm', 'Confirm Password', 'password', 'Repeat password')}

          <button
            type="submit"
            id="register-submit"
            className="btn btn-primary btn-full btn-lg"
            disabled={loading}
            style={{ marginTop: '8px' }}
          >
            {loading ? <><span className="spinner" /> Creating account...</> : 'Create Account'}
          </button>
        </form>

        <div className="auth-footer">
          Already have an account?{' '}
          <Link to="/login">Sign in</Link>
        </div>
      </div>
    </div>
  );
}
