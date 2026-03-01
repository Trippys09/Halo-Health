import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { api_client } from '../utils/api_client';
import { ShieldCheck, Lock } from 'lucide-react';
import './Auth.css';

const Register: React.FC = () => {
    const [fullName, setFullName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState(false);

    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!fullName || !email || !password) {
            setError('Please fill in all fields.');
            return;
        }
        if (password.length < 8) {
            setError('Password must be at least 8 characters.');
            return;
        }

        try {
            setLoading(true);
            setError('');
            await api_client.register(email, password, fullName);
            setSuccess(true);
            setTimeout(() => navigate('/login'), 2000);
        } catch (err: any) {
            setError(err.message || 'Registration failed.');
        } finally {
            setLoading(false);
        }
    };

    if (success) {
        return (
            <div className="auth-container">
                <div className="auth-card" style={{ textAlign: 'center' }}>
                    <h2 className="gradient-text">✅ Account Created!</h2>
                    <p style={{ marginTop: '1rem', color: 'var(--text-muted)' }}>Redirecting to login...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="auth-container">
            <div className="auth-card">
                <div className="auth-header">
                    <h1 className="gradient-text animate-fade-in" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                        <img src="/assets/logo.png" alt="HALO Health Logo" style={{ height: '40px' }} />
                        HALO Health
                    </h1>
                    <p className="animate-fade-in" style={{ animationDelay: '0.1s' }}>Join HALO Health today</p>
                </div>

                {error && <div className="auth-error animate-fade-in">{error}</div>}

                <form className="auth-form animate-fade-in" style={{ animationDelay: '0.2s' }} onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label htmlFor="fullName">Full Name</label>
                        <input
                            id="fullName"
                            type="text"
                            className="form-input"
                            placeholder="Jane Doe"
                            value={fullName}
                            onChange={(e) => setFullName(e.target.value)}
                        />
                    </div>

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
                            placeholder="Min 8 characters"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                        />
                    </div>

                    <button type="submit" className="auth-button" disabled={loading}>
                        {loading ? 'Creating account...' : 'Create Account'}
                    </button>
                </form>

                <div className="auth-link-text animate-fade-in" style={{ animationDelay: '0.3s' }}>
                    Already have an account? <Link to="/login">Sign in here</Link>
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

export default Register;
