/**
 * LoginPage — GeoLens IQ-inspired authentication with Sign In, Sign Up, and Google SSO.
 * Uses Firebase Authentication for all auth flows.
 */
import { useState } from 'react';
import {
  auth,
  googleProvider,
  signInWithPopup,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  updateProfile,
} from '../../firebase';
import './LoginPage.css';

export default function LoginPage({ onLogin }) {
  const [mode, setMode] = useState('signin'); // 'signin' | 'signup'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [username, setUsername] = useState('');
  const [fullName, setFullName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [rememberMe, setRememberMe] = useState(false);

  // ─── Google Sign-In ─────────────────────────────────────────
  const handleGoogleSignIn = async () => {
    setLoading(true);
    setError('');
    try {
      const result = await signInWithPopup(auth, googleProvider);
      const user = result.user;
      onLogin({
        uid: user.uid,
        name: user.displayName,
        email: user.email,
        picture: user.photoURL,
        provider: 'google',
      });
    } catch (err) {
      if (err.code === 'auth/popup-closed-by-user') return;
      setError(getFirebaseError(err.code));
    }
    setLoading(false);
  };

  // ─── Email Sign-In ──────────────────────────────────────────
  const handleEmailSignIn = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please fill in all fields');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const result = await signInWithEmailAndPassword(auth, email, password);
      const user = result.user;
      onLogin({
        uid: user.uid,
        name: user.displayName || email.split('@')[0],
        email: user.email,
        picture: user.photoURL,
        provider: 'email',
      });
    } catch (err) {
      setError(getFirebaseError(err.code));
    }
    setLoading(false);
  };

  // ─── Sign Up ────────────────────────────────────────────────
  const handleSignUp = async (e) => {
    e.preventDefault();
    if (!username || !email || !password || !confirmPassword) {
      setError('Please fill in all fields');
      return;
    }
    if (username.length < 3) {
      setError('Username must be at least 3 characters');
      return;
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const result = await createUserWithEmailAndPassword(auth, email, password);
      await updateProfile(result.user, {
        displayName: fullName || username,
      });
      onLogin({
        uid: result.user.uid,
        name: fullName || username,
        email: result.user.email,
        picture: null,
        username: username,
        provider: 'email',
      });
    } catch (err) {
      setError(getFirebaseError(err.code));
    }
    setLoading(false);
  };

  // ─── Demo Mode ──────────────────────────────────────────────
  const handleDemoLogin = () => {
    onLogin({
      uid: 'demo-user',
      name: 'Demo Operator',
      email: 'demo@geolens.iq',
      picture: null,
      isDemo: true,
    });
  };

  return (
    <div className="auth-page">
      {/* ─── Background ─── */}
      <div className="auth-bg">
        <div className="auth-grid" />
        <div className="auth-gradient" />
        {[...Array(15)].map((_, i) => (
          <div key={i} className="auth-particle" style={{
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
            animationDelay: `${Math.random() * 5}s`,
            animationDuration: `${3 + Math.random() * 4}s`,
          }} />
        ))}
      </div>

      <div className="auth-layout">
        {/* ─── Left Hero ─── */}
        <section className="auth-hero">
          <div className="auth-hero-content">
            <div className="auth-brand">
              <div className="auth-brand-icon">🌍</div>
              <span className="auth-brand-name">GeoSpatial IQ</span>
            </div>

            <h1 className="auth-headline">
              Precision Analytics for<br />
              <span className="auth-headline-accent">Global Site Readiness</span>
            </h1>

            <p className="auth-subtext">
              Harness high-resolution geospatial intelligence to evaluate
              territory potential, risk factors, and environmental constraints
              in real-time.
            </p>

            {/* Map Preview */}
            <div className="auth-map-preview">
              <div className="auth-map-glow" />
              <div className="auth-map-inner">
                <div className="auth-map-lines">
                  {[...Array(6)].map((_, i) => (
                    <div key={i} className="auth-map-line" style={{
                      top: `${15 + i * 15}%`,
                      left: `${10 + Math.random() * 20}%`,
                      width: `${40 + Math.random() * 40}%`,
                      transform: `rotate(${-15 + Math.random() * 30}deg)`,
                      animationDelay: `${i * 0.3}s`
                    }} />
                  ))}
                  {[...Array(8)].map((_, i) => (
                    <div key={`dot-${i}`} className="auth-map-dot" style={{
                      top: `${20 + Math.random() * 60}%`,
                      left: `${15 + Math.random() * 70}%`,
                      animationDelay: `${i * 0.4}s`,
                    }} />
                  ))}
                </div>
                <div className="auth-map-status">
                  <div className="auth-map-bar auth-map-bar-active" />
                  <div className="auth-map-bar" />
                  <span className="auth-map-label">SYSTEM STATUS: NOMINAL</span>
                </div>
              </div>
            </div>
          </div>

          {/* Coordinates */}
          <div className="auth-coords">
            <p>LAT: 23.0225° N</p>
            <p>LONG: 72.5714° E</p>
            <p>ALT: 12.4km</p>
          </div>
        </section>

        {/* ─── Right Auth Form ─── */}
        <main className="auth-form-section">
          <div className="auth-form-container">
            {/* Mobile branding */}
            <div className="auth-mobile-brand">
              <span className="auth-mobile-icon">🌍</span>
              <span className="auth-mobile-name">GeoSpatial IQ</span>
            </div>

            {/* Header */}
            <div className="auth-form-header">
              <h2>{mode === 'signin' ? 'Initialize Session' : 'Create Account'}</h2>
              <p>{mode === 'signin'
                ? 'Enter your credentials to access the intelligence suite.'
                : 'Register a new operator account.'
              }</p>
            </div>

            {/* Google Button */}
            <button className="auth-google-btn" onClick={handleGoogleSignIn} disabled={loading}>
              <svg className="auth-google-icon" viewBox="0 0 24 24">
                <path d="M12 5.04c1.9 0 3.61.65 4.95 1.93l3.71-3.71C18.41 1.39 15.39 0 12 0 7.31 0 3.26 2.69 1.25 6.63l4.24 3.29C6.5 7.07 9.04 5.04 12 5.04z" fill="#EA4335" />
                <path d="M23.49 12.27c0-.8-.07-1.56-.2-2.3H12v4.35h6.44c-.28 1.48-1.12 2.73-2.38 3.58l3.71 2.88c2.17-2 3.42-4.94 3.42-8.51z" fill="#4285F4" />
                <path d="M5.49 14.36c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09L1.25 6.63C.45 8.22 0 10.05 0 12s.45 3.78 1.25 5.37l4.24-3.01z" fill="#FBBC05" />
                <path d="M12 24c3.24 0 5.96-1.07 7.95-2.91l-3.71-2.88c-1.09.73-2.48 1.16-3.97 1.16-3 0-5.54-2.03-6.44-4.77L1.25 17.61C3.26 21.54 7.31 24 12 24z" fill="#34A853" />
              </svg>
              <span>Sign in with Google</span>
            </button>

            {/* Divider */}
            <div className="auth-divider">
              <span>{mode === 'signin' ? 'OR UTILIZE CREDENTIALS' : 'OR CREATE ACCOUNT'}</span>
            </div>

            {/* Error */}
            {error && (
              <div className="auth-error" onClick={() => setError('')}>
                ⚠ {error}
              </div>
            )}

            {/* ─── Sign In Form ─── */}
            {mode === 'signin' && (
              <form className="auth-form" onSubmit={handleEmailSignIn}>
                <div className="auth-field">
                  <label htmlFor="email">TERMINAL ID (EMAIL)</label>
                  <div className="auth-input-wrap">
                    <input
                      id="email"
                      type="email"
                      placeholder="operator@geolens.iq"
                      value={email}
                      onChange={e => setEmail(e.target.value)}
                      autoComplete="email"
                    />
                    <div className="auth-input-glow" />
                  </div>
                </div>

                <div className="auth-field">
                  <div className="auth-field-header">
                    <label htmlFor="password">ACCESS KEY</label>
                    <a href="#" className="auth-forgot">FORGOT CIPHER?</a>
                  </div>
                  <div className="auth-input-wrap">
                    <input
                      id="password"
                      type="password"
                      placeholder="••••••••••••"
                      value={password}
                      onChange={e => setPassword(e.target.value)}
                      autoComplete="current-password"
                    />
                    <div className="auth-input-glow" />
                  </div>
                </div>

                <div className="auth-remember">
                  <input
                    type="checkbox"
                    id="remember"
                    checked={rememberMe}
                    onChange={e => setRememberMe(e.target.checked)}
                  />
                  <label htmlFor="remember">Maintain secure session on this device</label>
                </div>

                <button className="auth-submit-btn" type="submit" disabled={loading}>
                  {loading ? 'Authenticating...' : 'Sign In'}
                </button>
              </form>
            )}

            {/* ─── Sign Up Form ─── */}
            {mode === 'signup' && (
              <form className="auth-form" onSubmit={handleSignUp}>
                <div className="auth-field">
                  <label htmlFor="username">OPERATOR CALLSIGN (USERNAME)</label>
                  <div className="auth-input-wrap">
                    <input
                      id="username"
                      type="text"
                      placeholder="geo_analyst_01"
                      value={username}
                      onChange={e => setUsername(e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, ''))}
                      autoComplete="username"
                    />
                    <div className="auth-input-glow" />
                  </div>
                </div>

                <div className="auth-field">
                  <label htmlFor="fullname">FULL NAME</label>
                  <div className="auth-input-wrap">
                    <input
                      id="fullname"
                      type="text"
                      placeholder="Your Full Name"
                      value={fullName}
                      onChange={e => setFullName(e.target.value)}
                      autoComplete="name"
                    />
                    <div className="auth-input-glow" />
                  </div>
                </div>

                <div className="auth-field">
                  <label htmlFor="signup-email">TERMINAL ID (EMAIL)</label>
                  <div className="auth-input-wrap">
                    <input
                      id="signup-email"
                      type="email"
                      placeholder="operator@geolens.iq"
                      value={email}
                      onChange={e => setEmail(e.target.value)}
                      autoComplete="email"
                    />
                    <div className="auth-input-glow" />
                  </div>
                </div>

                <div className="auth-row">
                  <div className="auth-field">
                    <label htmlFor="signup-password">ACCESS KEY</label>
                    <div className="auth-input-wrap">
                      <input
                        id="signup-password"
                        type="password"
                        placeholder="Min 6 chars"
                        value={password}
                        onChange={e => setPassword(e.target.value)}
                        autoComplete="new-password"
                      />
                      <div className="auth-input-glow" />
                    </div>
                  </div>

                  <div className="auth-field">
                    <label htmlFor="confirm-password">CONFIRM KEY</label>
                    <div className="auth-input-wrap">
                      <input
                        id="confirm-password"
                        type="password"
                        placeholder="Re-enter key"
                        value={confirmPassword}
                        onChange={e => setConfirmPassword(e.target.value)}
                        autoComplete="new-password"
                      />
                      <div className="auth-input-glow" />
                    </div>
                  </div>
                </div>

                <button className="auth-submit-btn" type="submit" disabled={loading}>
                  {loading ? 'Creating Account...' : 'Register Operator'}
                </button>
              </form>
            )}

            {/* Toggle Mode */}
            <div className="auth-toggle">
              {mode === 'signin' ? (
                <p>Don't have an account? <button onClick={() => { setMode('signup'); setError(''); }}>Sign Up</button></p>
              ) : (
                <p>Already registered? <button onClick={() => { setMode('signin'); setError(''); }}>Sign In</button></p>
              )}
            </div>

            {/* Demo shortcut */}
            <div className="auth-demo">
              <button onClick={handleDemoLogin}>🚀 Continue as Demo User</button>
            </div>

            {/* Footer */}
            <div className="auth-footer">
              <span>© 2026 GeoSpatial IQ</span>
              <div>
                <a href="#">Security</a>
                <a href="#">Privacy</a>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

// ─── Firebase Error Messages ──────────────────────────────────
function getFirebaseError(code) {
  const errors = {
    'auth/user-not-found': 'No account found with this email',
    'auth/wrong-password': 'Incorrect password',
    'auth/invalid-credential': 'Invalid email or password',
    'auth/email-already-in-use': 'This email is already registered',
    'auth/weak-password': 'Password must be at least 6 characters',
    'auth/invalid-email': 'Invalid email address',
    'auth/too-many-requests': 'Too many attempts. Please try again later',
    'auth/network-request-failed': 'Network error. Check your connection',
    'auth/popup-blocked': 'Popup was blocked. Allow popups and try again',
  };
  return errors[code] || `Authentication failed (${code})`;
}
