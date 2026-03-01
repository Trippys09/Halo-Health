import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Bot, Activity, Eye, HeartPulse, Stethoscope, Database } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import './LandingPage.css';

const LandingPage: React.FC = () => {
    const { user } = useAuth();

    return (
        <div className="landing-page-wrapper">
            {/* Top Navigation */}
            <nav className="landing-nav">
                <div className="nav-container">
                    <div className="landing-logo">
                        <img src="/assets/logo.png" alt="HALO Health Logo" style={{ height: '32px', marginRight: '8px', verticalAlign: 'middle' }} />
                        HALO Health <span className="logo-light">Enterprise</span>
                    </div>
                    <div className="landing-nav-links">
                        <a href="#features">Capabilities</a>
                        <a href="#oculomics">Oculomics</a>
                        <a href="#security">Security</a>
                    </div>
                    <div className="landing-auth">
                        {user ? (
                            <Link to="/dashboard" className="btn-primary">Go to Dashboard</Link>
                        ) : (
                            <>
                                <Link to="/login" className="btn-login">Sign In</Link>
                                <Link to="/register" className="btn-primary">Request Access</Link>
                            </>
                        )}
                    </div>
                </div>
            </nav>

            <div className="landing-container animate-fade-in">
                {/* Hero Section */}
                <header className="landing-hero">
                    <div className="hero-badges">
                        <span className="hero-badge">NON-INVASIVE DIAGNOSTICS</span>
                        <span className="hero-badge">GEMINI 3 POWERED</span>
                    </div>
                    <h1>The Eye is a Systemic <br /><span className="gradient-text">Window.</span></h1>
                    <p className="landing-hero-sub">
                        "Oculomics" offers a transformative paradigm for non-invasive systemic health monitoring.
                        HALO Health leverages advanced Vision Transformers (ViT) and multi-task setups so clinical priors no longer overshadow noisy visual signals.
                    </p>
                    <div className="hero-cta">
                        <Link to={user ? "/dashboard" : "/register"} className="btn-primary large">
                            Access Oculomics Engine <ArrowRight size={18} />
                        </Link>
                    </div>
                </header>

                {/* Features / Capabilities */}
                <section id="features" className="landing-section">
                    <div className="section-header">
                        <h2>End-to-End Orchestration</h2>
                        <p>A cohesive medical intelligence ecosystem linking multimodal diagnostic modules with an advanced agent protocol.</p>
                    </div>
                    <div className="features-grid">
                        <div className="feature-card glass-panel">
                            <div className="feature-icon" style={{ background: '#0F52BA15', color: '#0F52BA' }}>
                                <Bot size={26} />
                            </div>
                            <h3>7 Specialized Agents</h3>
                            <p>From Dietary to Diagnostics, route complex medical queries to specialized LLMs capable of multimodal reasoning.</p>
                        </div>
                        <div className="feature-card glass-panel">
                            <div className="feature-icon" style={{ background: '#0284c715', color: '#0284c7' }}>
                                <Activity size={26} />
                            </div>
                            <h3>SynthVision Generation</h3>
                            <p>Automatically generate visual insights and medical imagery projections rather than standard data telemetry calls.</p>
                        </div>
                        <div className="feature-card glass-panel">
                            <div className="feature-icon" style={{ background: '#10b98115', color: '#10b981' }}>
                                <Database size={26} />
                            </div>
                            <h3>Isolated Vector Memory</h3>
                            <p>Every session is stored locally with ChromaDB tracking, entirely decoupled from external telemetry servers.</p>
                        </div>
                    </div>
                </section>

                {/* Oculomics Spotlight (Redesigned for Full Width) */}
                <section id="oculomics" className="landing-section bg-secondary oculomics-section">
                    <div className="section-header">
                        <h2>Introducing <span style={{ color: '#0F52BA' }}>Oculomics AI</span></h2>
                        <p style={{ fontSize: '1.1rem', color: '#0f172a', fontWeight: 500, marginBottom: '0.5rem' }}>
                            Your smartphone is now a predictive diagnostic tool.
                        </p>
                        <p>
                            Our flagship reasoning engine accepts mobile phone retinal scans to instantly predict systemic, neurological, and ocular health markers with unprecedented accuracy.
                        </p>
                    </div>

                    <div className="oculomics-grid">
                        <div className="oculomics-item glass-panel">
                            <div className="feature-icon" style={{ background: '#2563eb15', color: '#2563eb' }}><Eye size={24} /></div>
                            <div>
                                <strong>Ocular Diseases</strong>
                                <p>Early detection of Diabetic Retinopathy and Macular Edema.</p>
                            </div>
                        </div>
                        <div className="oculomics-item glass-panel">
                            <div className="feature-icon" style={{ background: '#ef444415', color: '#ef4444' }}><HeartPulse size={24} /></div>
                            <div>
                                <strong>Systemic Risks</strong>
                                <p>Identifies markers for Diabetes, Hypertension, and Cardiovascular conditions.</p>
                            </div>
                        </div>
                        <div className="oculomics-item glass-panel">
                            <div className="feature-icon" style={{ background: '#8b5cf615', color: '#8b5cf6' }}><Stethoscope size={24} /></div>
                            <div>
                                <strong>Neurological & Nephrological</strong>
                                <p>Early-stage risk pattern detection mapped directly from fundus scans.</p>
                            </div>
                        </div>
                    </div>
                </section>

                {/* Footer */}
                <footer className="landing-footer">
                    <div className="footer-brand">
                        <div className="footer-logo">
                            <img src="/assets/logo.png" alt="HALO Health Logo" style={{ height: '24px', marginRight: '8px', verticalAlign: 'middle' }} />
                            HALO Health Enterprise
                        </div>
                        <p>© 2026 HALO Health Healthcare Systems. HIPAA-Aware Design.</p>
                    </div>
                    <div className="footer-links">
                        <a href="#">Privacy Policy</a>
                        <a href="#">Terms of Service</a>
                        <a href="mailto:nshaik3@student.gsu.edu">Contact Admin</a>
                    </div>
                </footer>
            </div>
        </div>
    );
};

export default LandingPage;