import React from 'react';
import {
    Mail, Users, MonitorSmartphone, BrainCircuit, Activity,
    Bot, Eye, Cpu, Database, Shield, Zap, GitBranch, Globe
} from 'lucide-react';
import './About.css';

const techStack = [
    { name: 'Frontend', tools: 'React 18, TypeScript, Vite, Vanilla CSS', icon: <MonitorSmartphone size={20} /> },
    { name: 'Backend', tools: 'FastAPI, Python 3.12, Pydantic v2, SQLAlchemy', icon: <Zap size={20} /> },
    { name: 'AI Core — Vision', tools: 'Gemini 3 flash (multimodal), Vision Transformers (ViT)', icon: <Cpu size={20} /> },
    { name: 'AI Core — Reasoning', tools: 'Gemini 3.1 Pro (reasoning & orchestration)', icon: <BrainCircuit size={20} /> },
    { name: 'Memory & Database', tools: 'ChromaDB (Vector DB), SQLite per-user isolation', icon: <Database size={20} /> },
    { name: 'Agent Orchestration', tools: 'A2A (Agent-to-Agent) Protocol, Tavily Web Search', icon: <GitBranch size={20} /> },
    { name: 'Security', tools: 'JWT Auth, bcrypt password hashing, per-user memory isolation', icon: <Shield size={20} /> },
    { name: 'External Services', tools: 'Tavily API, DuckDuckGo Search, gTTS, Web Speech API', icon: <Globe size={20} /> },
];

const offerings = [
    {
        name: 'Oculomics AI',
        desc: 'Predictive retina engine. Analyses mobile fundus images to detect Diabetic Retinopathy, Macular Edema, and systemic conditions (Hypertension, Cardiovascular risk).',
        icon: <Eye size={26} />,
        color: '#2563eb',
    },
    {
        name: 'PRISM',
        desc: 'Multimodal diagnostic assistant powered by Gemini 3 flash. Generates structured, clinician-ready reports from X-rays, MRIs, CT scans, and pathology slides. Exports hospital-grade PDF reports.',
        icon: <Activity size={26} />,
        color: '#0F52BA',
    },
    {
        name: 'SAGE',
        desc: 'Mental wellness counsellor leveraging CBT protocols. Provides grounding, breathing exercises, and behavioural activation strategies. Crisis-aware with 988 lifeline referral.',
        icon: <BrainCircuit size={26} />,
        color: '#10b981',
    },
    {
        name: 'APOLLO',
        desc: 'Virtual doctor for symptom consultation, prescription guidance (OTC & Rx class), first-aid protocols, and real-time nearest hospital/pharmacy search via AI-powered location lookup.',
        icon: <Bot size={26} />,
        color: '#ef4444',
    },
];

const modelInfo = [
    {
        model: 'Gemini 3.1 Pro',
        role: 'Primary Reasoning Engine',
        release: 'Latest',
        context: '1M tokens',
        use: 'APOLLO (Virtual Doctor), HALO Orchestrator — complex multi-step medical reasoning and A2A coordination.',
        badge: 'REASONING',
        color: '#0F52BA',
    },
    {
        model: 'Gemini 3 flash',
        role: 'Multimodal Vision Engine',
        release: 'Latest',
        context: '1M tokens',
        use: 'PRISM (Diagnostic), Oculomics AI, SAGE, NORA, InsuCompass — fast multimodal inference for imaging and text.',
        badge: 'VISION · SPEED',
        color: '#0284c7',
    },
];

interface TeamMember {
    name: string;
    firstName: string;
    initials: string;
    role: string;
    focus: string;
}

const teamMembers: TeamMember[] = [
    { name: 'Pavan Bobba', firstName: 'Pavan', initials: 'PB', role: 'Lead Developer', focus: 'Full-Stack & AI Integration' },
];

const About: React.FC = () => {
    return (
        <div className="about-container animate-fade-in">
            {/* Hero */}
            <header className="about-hero">
                <div className="about-hero-icon">⚕️</div>
                <h1>About <span className="gradient-text">HALO Health</span></h1>
                <p className="about-hero-sub">
                    Multimodal AI Healthcare Orchestration R&D Project — bridging clinical intelligence and everyday care.
                </p>
                <div className="about-badges">
                    <span className="about-badge">R&D Project</span>
                    <span className="about-badge">HIPAA-Aware Design</span>
                    <span className="about-badge">A2A Agent Protocol</span>
                    <span className="about-badge">Gemini 3 Powered</span>
                </div>
            </header>

            {/* Clinical Agents */}
            <section className="about-section">
                <div className="about-section-header">
                    <h2>Clinical AI Agents</h2>
                    <p>Each agent is a specialist — powered by state-of-the-art Gemini models and grounded with real-time search.</p>
                </div>
                <div className="offerings-grid">
                    {offerings.map(o => (
                        <div key={o.name} className="offering-card glass-panel">
                            <div className="offering-icon" style={{ background: `${o.color}15`, color: o.color }}>{o.icon}</div>
                            <h3>{o.name}</h3>
                            <p>{o.desc}</p>
                        </div>
                    ))}
                </div>
            </section>

            {/* AI Models & Datasets */}
            <section className="about-section bg-secondary">
                <div className="about-section-header">
                    <h2>AI Models & Benchmarks</h2>
                    <p>HALO Health runs on Google's latest Gemini 3 family. Our models are heavily benchmarked against leading open-source medical diagnostics datasets.</p>
                </div>

                <div className="benchmark-list" style={{ marginBottom: '2rem', textAlign: 'left', background: 'white', padding: '1.5rem', borderRadius: '8px', border: '1px solid #e1dfdd' }}>
                    <h3 style={{ marginBottom: '1rem', color: '#0F52BA' }}>Research Datasets</h3>
                    <ul style={{ lineHeight: '1.7' }}>
                        <li><strong>Oculomics Medical Reporting:</strong> Benchmarked against <a href="https://github.com/Jhhuangkay/DeepOpht-Medical-Report-Generation-for-Retinal-Images-via-Deep-Models-and-Visual-Explanation" target="_blank" rel="noreferrer">DeepEyeNet</a></li>
                        <li><strong>Retinal Imaging:</strong> Evaluated using the <a href="https://physionet.org/content/mbrset/1.0/" target="_blank" rel="noreferrer">mBRSET Dataset</a></li>
                        <li><strong>Radiology (Chest X-Rays):</strong> Benchmarked against <a href="https://physionet.org/content/mimic-cxr/2.1.0/" target="_blank" rel="noreferrer">MIMIC-CXR</a></li>
                        <li><strong>General Medical Imaging:</strong> Trained & validated against the <a href="https://github.com/razorx89/roco-dataset" target="_blank" rel="noreferrer">ROCO Dataset</a></li>
                    </ul>
                </div>

                <div className="model-cards">
                    {modelInfo.map(m => (
                        <div key={m.model} className="model-card glass-panel">
                            <div className="model-badge" style={{ background: `${m.color}20`, color: m.color }}>{m.badge}</div>
                            <h3 style={{ color: m.color }}>{m.model}</h3>
                            <p className="model-role">{m.role}</p>
                            <div className="model-meta">
                                <span>Released: {m.release}</span>
                                <span>Context: {m.context}</span>
                            </div>
                            <p className="model-use"><strong>Used by:</strong> {m.use}</p>
                        </div>
                    ))}
                </div>
            </section>

            {/* Tech Stack */}
            <section className="about-section">
                <div className="about-section-header">
                    <h2>Technology Stack</h2>
                    <p>Engineered for high-availability, security, and clinical-grade performance.</p>
                </div>
                <div className="tech-stack-list">
                    {techStack.map(stack => (
                        <div key={stack.name} className="tech-item glass-panel">
                            <div className="tech-icon">{stack.icon}</div>
                            <div>
                                <h4>{stack.name}</h4>
                                <p>{stack.tools}</p>
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            {/* Team */}
            <section className="about-section team-section">
                <div className="about-section-header">
                    <h2><Users size={22} style={{ display: 'inline', verticalAlign: 'text-bottom', marginRight: '8px' }} />Our Team</h2>
                    <p>Georgia State University · Computer Science Program</p>
                </div>
                <div className="team-grid">
                    {teamMembers.map(member => (
                        <div key={member.name} className="team-member glass-panel">
                            <div className="member-avatar">
                                <span className="member-initials">{member.initials}</span>
                                <img 
                                    src={`/assets/team/${member.firstName}.jpg`} 
                                    alt={member.name} 
                                    className="member-photo"
                                    onError={(e) => {
                                        // Hide the broken image icon and reveal initials underneath
                                        e.currentTarget.style.opacity = '0';
                                    }}
                                />
                            </div>
                            <h3>{member.name}</h3>
                            <p className="member-role" style={{ textTransform: 'none', color: '#64748b' }}>
                                <a href={`mailto:${member.email}`} style={{ color: 'inherit', textDecoration: 'none' }}>{member.email}</a>
                            </p>
                        </div>
                    ))}
                </div>
            </section>

            {/* Contact */}
            <section className="about-section contact-section">
                <h2>Get in Touch</h2>
                <p>Interested in integrating this R&D platform into your healthcare system?</p>
                <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', marginTop: '1.5rem' }}>
                    <a href="mailto:nshaik3@student.gsu.edu" className="btn-contact">
                        <Mail size={18} /> Contact Admin
                    </a>
                </div>
            </section>
        </div>
    );
};

export default About;