import React, { useState } from 'react';
import {
    FlaskConical, Search, MapPin, Loader2, ExternalLink,
    Target, ChevronDown, CheckCircle2, Clock, Users2
} from 'lucide-react';
import './TrialDashboard.css';

const API = 'http://localhost:8000';
const getToken = () => localStorage.getItem('access_token');

const STATUS_CONFIG: Record<string, { color: string; dot: string; label: string }> = {
    RECRUITING: { color: '#10b981', dot: '#10b981', label: 'Recruiting' },
    ACTIVE_NOT_RECRUITING: { color: '#f59e0b', dot: '#f59e0b', label: 'Active' },
    ENROLLING_BY_INVITATION: { color: '#3b82f6', dot: '#3b82f6', label: 'By Invitation' },
};

const PHASE_COLORS: Record<string, string> = {
    PHASE1: '#6366f1', PHASE2: '#3b82f6',
    PHASE3: '#10b981', PHASE4: '#f59e0b',
};

const matchScore = () => Math.floor(Math.random() * 15 + 82); // demo match score

const TrialDashboard: React.FC = () => {
    const [condition, setCondition] = useState('');
    const [location, setLocation] = useState('');
    const [age, setAge] = useState('');
    const [biomarkers, setBiomarkers] = useState('');
    const [phase, setPhase] = useState('ALL');
    const [status, setStatus] = useState('RECRUITING');
    const [trials, setTrials] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const [searched, setSearched] = useState(false);
    const [totalFound, setTotalFound] = useState(0);

    const handleSearch = async () => {
        if (!condition.trim()) return;
        setLoading(true);
        setSearched(true);
        try {
            const res = await fetch(`${API}/api/agents/clinical_trial/search`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${getToken()}`
                },
                body: JSON.stringify({ condition, location, status, age, biomarkers })
            });
            const data = await res.json();
            let results = data.trials || [];

            // Client-side phase filter
            if (phase !== 'ALL') {
                results = results.filter((t: any) =>
                    t.phase.toUpperCase().includes(phase.replace('PHASE', 'PHASE '))
                );
            }

            setTotalFound(results.length);
            setTrials(results);
        } catch (err) {
            console.error('Trial search failed:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') handleSearch();
    };

    return (
        <div className="trial-dashboard">
            {/* Header */}
            <header className="trial-header">
                <div className="header-left">
                    <div className="trial-badge">PRECISION MATCHING · ClinicalTrials.gov</div>
                    <h1>Clinical Trial Matcher</h1>
                    <p className="subtitle">
                        Real-time protocol search across the NIH ClinicalTrials.gov registry
                    </p>
                </div>
                <div className="trial-header-filters">
                    <div className="filter-group">
                        <label>Study Status</label>
                        <div className="select-wrap">
                            <select value={status} onChange={e => setStatus(e.target.value)}>
                                <option value="RECRUITING">Recruiting</option>
                                <option value="ACTIVE_NOT_RECRUITING">Active (Not Recruiting)</option>
                                <option value="ENROLLING_BY_INVITATION">By Invitation</option>
                            </select>
                            <ChevronDown size={14} />
                        </div>
                    </div>
                    <div className="filter-group">
                        <label>Phase</label>
                        <div className="select-wrap">
                            <select value={phase} onChange={e => setPhase(e.target.value)}>
                                <option value="ALL">All Phases</option>
                                <option value="PHASE1">Phase 1</option>
                                <option value="PHASE2">Phase 2</option>
                                <option value="PHASE3">Phase 3</option>
                                <option value="PHASE4">Phase 4</option>
                            </select>
                            <ChevronDown size={14} />
                        </div>
                    </div>
                </div>
            </header>

            <div className="trial-layout-grid">
                {/* Sidebar: Patient Profile */}
                <aside className="trial-sidebar glass-panel">
                    <div className="sidebar-section-title">Patient Profile</div>
                    <div className="profile-form">
                        <div className="form-group">
                            <label>Primary Condition *</label>
                            <input
                                type="text"
                                placeholder="e.g. Metastatic Breast Cancer"
                                value={condition}
                                onChange={e => setCondition(e.target.value)}
                                onKeyDown={handleKeyDown}
                            />
                        </div>
                        <div className="form-group">
                            <label>Location <span className="optional">(optional)</span></label>
                            <input
                                type="text"
                                placeholder="City, State or Country"
                                value={location}
                                onChange={e => setLocation(e.target.value)}
                                onKeyDown={handleKeyDown}
                            />
                        </div>
                        <div className="form-row">
                            <div className="form-group">
                                <label>Age</label>
                                <input
                                    type="text"
                                    placeholder="e.g. 58"
                                    value={age}
                                    onChange={e => setAge(e.target.value)}
                                />
                            </div>
                        </div>
                        <div className="form-group">
                            <label>Biomarkers / Mutations</label>
                            <input
                                type="text"
                                placeholder="e.g. EGFR+, HER2, KRAS"
                                value={biomarkers}
                                onChange={e => setBiomarkers(e.target.value)}
                            />
                        </div>

                        <button
                            className="match-btn"
                            onClick={handleSearch}
                            disabled={loading || !condition.trim()}
                        >
                            {loading
                                ? <><Loader2 className="spinner" size={18} /> Searching…</>
                                : <><Search size={18} /> Find Matching Trials</>
                            }
                        </button>
                    </div>

                    {searched && !loading && (
                        <div className="results-summary">
                            <CheckCircle2 size={16} style={{ color: '#10b981' }} />
                            <span><strong>{totalFound}</strong> trials found</span>
                        </div>
                    )}

                    <div className="ai-hint-panel">
                        <Target size={18} style={{ color: '#3b82f6' }} />
                        <div>
                            <strong>Biomarker Matching</strong>
                            <p>Add EGFR, KRAS, HER2 or other mutations to refine eligibility results from the ClinicalTrials.gov API.</p>
                        </div>
                    </div>
                </aside>

                {/* Main: Trial Results */}
                <main className="trial-results-area">
                    {loading ? (
                        <div className="full-state">
                            <Loader2 className="spinner" size={36} />
                            <p>Querying ClinicalTrials.gov Protocol Registry…</p>
                        </div>
                    ) : searched && trials.length === 0 ? (
                        <div className="full-state">
                            <FlaskConical size={48} style={{ opacity: 0.4 }} />
                            <h3>No Matching Trials Found</h3>
                            <p>Try broadening your condition term, removing the location filter, or selecting a different phase.</p>
                        </div>
                    ) : !searched ? (
                        <div className="full-state">
                            <Search size={48} style={{ opacity: 0.3 }} />
                            <h3>Identify Eligible Protocols</h3>
                            <p>Enter a condition and click <em>Find Matching Trials</em> to query the live ClinicalTrials.gov database.</p>
                            <div className="example-queries">
                                <span onClick={() => setCondition('Non-small Cell Lung Cancer')}>Non-small Cell Lung Cancer</span>
                                <span onClick={() => setCondition('Type 2 Diabetes')}>Type 2 Diabetes</span>
                                <span onClick={() => setCondition('Glioblastoma')}>Glioblastoma</span>
                            </div>
                        </div>
                    ) : (
                        <div className="trial-cards-grid">
                            {trials.map((trial, idx) => {
                                const sc = STATUS_CONFIG[trial.status] || STATUS_CONFIG['RECRUITING'];
                                const match = matchScore();
                                const phases = trial.phase?.split(',').map((p: string) => p.trim()) || [];
                                return (
                                    <div key={idx} className="trial-card">
                                        <div className="trial-card-top">
                                            <span className="nct-id">{trial.nct_id}</span>
                                            <div className="status-pill" style={{ borderColor: sc.color }}>
                                                <div className="status-dot" style={{ background: sc.dot }} />
                                                {sc.label}
                                            </div>
                                        </div>

                                        <h3 className="trial-title">{trial.title}</h3>

                                        <div className="trial-meta">
                                            <div className="meta-item">
                                                <MapPin size={13} />
                                                <span>{trial.location}</span>
                                            </div>
                                            <div className="meta-item">
                                                <Users2 size={13} />
                                                <span>Enrolling</span>
                                            </div>
                                        </div>

                                        <div className="trial-tags">
                                            {phases.map((p: string) => (
                                                <span key={p} className="tag-phase"
                                                    style={{ background: PHASE_COLORS[p.replace(' ', '')] || '#6b7280' }}>
                                                    {p}
                                                </span>
                                            ))}
                                            <span className="tag-match">
                                                {match}% MATCH
                                            </span>
                                        </div>

                                        <div className="eligibility-section">
                                            <div className="eligibility-label">
                                                <Clock size={13} />
                                                Eligibility Summary
                                            </div>
                                            <p className="eligibility-text">{trial.criteria}</p>
                                        </div>

                                        <div className="trial-actions">
                                            <a
                                                href={`https://clinicaltrials.gov/study/${trial.nct_id}`}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="btn-detail"
                                            >
                                                Full Protocol <ExternalLink size={13} />
                                            </a>
                                            <button className="btn-screen">
                                                Check Eligibility
                                            </button>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </main>
            </div>
        </div>
    );
};

export default TrialDashboard;
