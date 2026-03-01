import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
    HeartPulse, Stethoscope, ShieldCheck, Apple, Bot,
    ArrowRight, Eye, Info, BarChart3, Zap, GitBranch, Brain
} from 'lucide-react';
import './Dashboard.css';

const agentCards = [
    {
        id: 'orchestrator',
        name: 'HALO',
        role: 'Master Orchestrator',
        desc: 'Central intelligence hub. Routes your query to the right specialist via A2A. Handles any health domain automatically.',
        icon: <Brain size={30} />,
        color: '#0F52BA',
        badge: 'MASTER CHAT',
    },
    {
        id: 'oculomics',
        name: 'Oculomics AI',
        role: 'Predictive Retina Engine',
        desc: 'Analyses fundus photographs to detect Diabetic Retinopathy, Macular Edema, and systemic risks (Diabetes, Hypertension, CVD).',
        icon: <Eye size={30} />,
        color: '#2563eb',
        badge: 'VISION AI',
    },
    {
        id: 'diagnostic',
        name: 'PRISM',
        role: 'Diagnostic Assistant',
        desc: 'Multimodal scan analysis — X-rays, MRIs, CT, retinal images. Generates structured clinical reports. Hospital-grade PDF export.',
        icon: <Stethoscope size={30} />,
        color: '#0F52BA',
        badge: 'IMAGING',
    },
    {
        id: 'wellbeing',
        name: 'SAGE',
        role: 'Wellbeing Counsellor',
        desc: 'CBT-grounded mental wellness support. Addresses stress, anxiety, depression, and burnout. Crisis-aware with lifeline referral.',
        icon: <HeartPulse size={30} />,
        color: '#10b981',
        badge: 'WELLNESS',
    },
    {
        id: 'virtual-doctor',
        name: 'APOLLO',
        role: 'Virtual Doctor',
        desc: 'Clinical symptom consultation, OTC/Rx prescription suggestions, real-time emergency triage, nearest hospital & pharmacy search.',
        icon: <Bot size={30} />,
        color: '#ef4444',
        badge: 'MEDICAL',
    },
    {
        id: 'dietary',
        name: 'NORA',
        role: 'Dietary Expert',
        desc: 'Personalised meal plans with macro breakdowns. Immediate full plan on first message — no interrogation, sensible defaults.',
        icon: <Apple size={30} />,
        color: '#f59e0b',
        badge: 'NUTRITION',
    },
    {
        id: 'insurance',
        name: 'InsuCompass',
        role: 'Insurance Guide',
        desc: 'Navigates ACA Marketplace, Medicare Parts A-D, Medicaid, COBRA, and employer plans. Subsidy & eligibility guidance.',
        icon: <ShieldCheck size={30} />,
        color: '#3b82f6',
        badge: 'INSURANCE',
    },
];

const metrics = [
    { label: 'AI Models', value: '2', sub: 'Gemini 3.1 Pro · 3 flash', icon: <Zap size={20} /> },
    { label: 'Specialist Agents', value: '7', sub: 'APOLLO, PRISM, SAGE, NORA +', icon: <Bot size={20} /> },
    { label: 'Vector Memory', value: 'Per-User', sub: 'Isolated ChromaDB instances', icon: <Brain size={20} /> },
    { label: 'Architecture', value: 'A2A', sub: 'Agent-to-Agent protocol', icon: <GitBranch size={20} /> },
];

const Dashboard: React.FC = () => {
    const { user } = useAuth();
    const firstName = user?.full_name?.split(' ')[0] || 'Clinician';

    return (
        <div className="dashboard-container animate-fade-in">
            {/* Hero Banner */}
            <section className="dashboard-hero">
                <div className="hero-text">
                    <h1>
                        Good morning, <span style={{ color: '#ffffff', fontWeight: '800' }}>{firstName}</span>
                    </h1>
                    <p>
                        HALO Health is ready. Select an agent below or use the Master Chat to let AI route your query automatically.
                    </p>
                </div>
                <div className="hero-graphic">
                    <div className="hero-pulse-ring" />
                    <span className="hero-icon">⚕️</span>
                </div>
            </section>

            {/* Platform Metrics */}
            <section className="metrics-row">
                {metrics.map(m => (
                    <div key={m.label} className="metric-card glass-panel">
                        <div className="metric-icon">{m.icon}</div>
                        <div>
                            <div className="metric-value">{m.value}</div>
                            <div className="metric-label">{m.label}</div>
                            <div className="metric-sub">{m.sub}</div>
                        </div>
                    </div>
                ))}
            </section>

            {/* Agent Grid */}
            <section>
                <div className="section-header">
                    <h2><BarChart3 size={22} /> Clinical AI Agents</h2>
                    <span className="section-sub">Click any agent to start a New Chat</span>
                </div>
                <div className="dashboard-grid">
                    {agentCards.map((agent, index) => (
                        <div
                            key={agent.id}
                            className="agent-card"
                            style={{ animationDelay: `${index * 0.05}s` }}
                        >
                            <div className="agent-card-top">
                                <div className="agent-icon" style={{ color: agent.color, backgroundColor: `${agent.color}12` }}>
                                    {agent.icon}
                                </div>
                                <span className="agent-badge" style={{ background: `${agent.color}15`, color: agent.color }}>
                                    {agent.badge}
                                </span>
                            </div>
                            <div className="agent-info">
                                <h3>{agent.name}</h3>
                                <span className="agent-role" style={{ color: agent.color }}>{agent.role}</span>
                                <p>{agent.desc}</p>
                            </div>
                            <Link to={`/chat/${agent.id}`} className="agent-link" style={{ borderColor: `${agent.color}30`, color: agent.color }}>
                                New Chat <ArrowRight size={15} />
                            </Link>
                        </div>
                    ))}
                </div>
            </section>

            {/* Oculomics Training Stats */}
            <section className="oculomics-stats-section">
                <div className="section-header">
                    <h2><Eye size={22} style={{ color: 'var(--primary)' }} /> Oculomics Predictive Modeling</h2>
                    <p className="section-sub">
                        We trained 10 distinct predictive tasks using PyTorch Foundational Models (ViT).
                        The Oculomics Agent uses these models autonomously to estimate demographics, systemic risks,
                        and ocular diseases directly from patient retinal scans. Below are the peak validation metrics from our training history.
                    </p>
                </div>
                <div className="stats-grid">
                    <div className="stat-card">
                        <h4>Diabetes</h4><span className="stat-value">97.03%</span><span className="stat-label">Accuracy</span>
                    </div>
                    <div className="stat-card">
                        <h4>Nephropathy</h4><span className="stat-value">96.21%</span><span className="stat-label">Accuracy</span>
                    </div>
                    <div className="stat-card">
                        <h4>Edema</h4><span className="stat-value">96.42%</span><span className="stat-label">Accuracy</span>
                    </div>
                    <div className="stat-card">
                        <h4>Neuropathy</h4><span className="stat-value">94.37%</span><span className="stat-label">Accuracy</span>
                    </div>
                    <div className="stat-card">
                        <h4>AMI</h4><span className="stat-value">93.35%</span><span className="stat-label">Accuracy</span>
                    </div>
                    <div className="stat-card">
                        <h4>Cardio Risk</h4><span className="stat-value">84.95%</span><span className="stat-label">Accuracy</span>
                    </div>
                    <div className="stat-card">
                        <h4>ICDR</h4><span className="stat-value">81.47%</span><span className="stat-label">Accuracy</span>
                    </div>
                    <div className="stat-card">
                        <h4>Gender</h4><span className="stat-value">72.47%</span><span className="stat-label">Accuracy</span>
                    </div>
                    <div className="stat-card">
                        <h4>Hypertension</h4><span className="stat-value">70.11%</span><span className="stat-label">Accuracy</span>
                    </div>
                    <div className="stat-card">
                        <h4>Age</h4><span className="stat-value">5.24</span><span className="stat-label">MAE (Years)</span>
                    </div>
                </div>
            </section>

            {/* About Platform */}
            <section className="about-strip">
                <div className="about-strip-text">
                    <h2><Info size={20} /> Why HALO Health?</h2>
                    <p>
                        HALO Health bridges the gap between advanced AI reasoning and everyday clinical workflows.
                        Powered by Gemini 3.1 Pro for complex reasoning and Gemini 3 flash for rapid multimodal analysis.
                    </p>
                    <ul className="about-list">
                        <li><strong>A2A Protocol:</strong> Agents consult each other for multi-domain queries.</li>
                        <li><strong>Isolated Memory:</strong> Each user has a private ChromaDB vector database.</li>
                        <li><strong>Audio Mode:</strong> Speak to any agent — voice input and response playback.</li>
                        <li><strong>Hospital-Grade PDFs:</strong> Export diagnostic reports with embedded scan images.</li>
                    </ul>
                </div>
                <Link to="/about" className="about-strip-btn">
                    View Full Platform Details <ArrowRight size={15} />
                </Link>
            </section>
        </div>
    );
};

export default Dashboard;
