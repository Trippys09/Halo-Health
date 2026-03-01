import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { api_client } from '../utils/api_client';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck, Lock } from 'lucide-react';
import './Auth.css';

const Login: React.FC = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const navigate = useNavigate();
    const { login } = useAuth();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!email || !password) {
            setError('Please enter both email and password.');
            return;
        }

        try {
            setLoading(true);
            setError('');

            const loginResp = await api_client.login(email, password);
            const token = loginResp.access_token;

            // Temporarily store to fetch me
            localStorage.setItem('access_token', token);
            const meResp = await api_client.getMe();

            login(token, meResp);
            navigate('/');
        } catch (err: any) {
            setError(err.message || 'Login failed.');
            localStorage.removeItem('access_token');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-container">
            <div className="auth-card">
                <div className="auth-header">
                    <h1 className="gradient-text animate-fade-in" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                        <img src="/assets/logo.png" alt="HALO Health Logo" style={{ height: '40px' }} />
                        HALO Health
                    </h1>
                    <p className="animate-fade-in" style={{ animationDelay: '0.1s' }}>Sign in to your personal health hub</p>
                </div>

                {error && <div className="auth-error animate-fade-in">{error}</div>}

                <form className="auth-form animate-fade-in" style={{ animationDelay: '0.2s' }} onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label htmlFor="email">Email</label>
                        <input
                            id="email"
                            type="email"
                            className="form-input"
                            placeholder="you@example.com"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="password">Password</label>
                        <input
                            id="password"
                            type="password"
                            className="form-input"
                            placeholder="••••••••"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                        />
                    </div>

                    <button type="submit" className="auth-button" disabled={loading}>
                        {loading ? 'Logging in...' : 'Login'}
                    </button>
                </form>

                <div className="auth-link-text animate-fade-in" style={{ animationDelay: '0.3s' }}>
                    New to HALO Health? <Link to="/register">Create Account</Link>
                </div>

                <div className="auth-security-notice animate-fade-in" style={{ animationDelay: '0.4s', marginTop: '2rem', paddingTop: '1.5rem', borderTop: '1px solid var(--border-color)', fontSize: '0.85rem', color: 'var(--text-muted)', textAlign: 'center', display: 'flex', flexDirection: 'column', gap: '0.5rem', alignItems: 'center' }}>
                    <div style={{ display: 'flex', gap: '1rem', color: 'var(--primary)' }}>
                        <ShieldCheck size={20} />
                        <Lock size={20} />
                    </div>
                    <p>Protected by end-to-end medical-grade encryption. Your data is private, secure, and fully HIPAA compliant.</p>
                </div>
            </div>
        </div>
    );
};

export default Login;
