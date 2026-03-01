import React, { useState, useEffect, useMemo } from 'react';
import { api_client } from '../utils/api_client';
import { Activity, Clock, MessageSquare, Bot, AlertCircle } from 'lucide-react';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    AreaChart, Area
} from 'recharts';
import './AuditDashboard.css';

interface AuditStats {
    sessions_by_agent: { agent: string; sessions: number }[];
    total_user_messages: number;
    total_agent_messages: number;
    avg_agent_response_chars: number;
    sessions_last_7_days: number;
    total_sessions: number;
}

interface AuditActivity {
    id: number;
    session_id: number;
    session_title: string;
    agent_type: string;
    role: string;
    content_preview: string;
    content_length: number;
    timestamp: string;
}

const AuditDashboard: React.FC = () => {
    const [stats, setStats] = useState<AuditStats | null>(null);
    const [activity, setActivity] = useState<AuditActivity[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [agentFilter, setAgentFilter] = useState<string>('all');

    const fetchAuditData = async () => {
        setLoading(true);
        setError(null);
        try {
            const [statsData, activityData] = await Promise.all([
                api_client.getAuditStats(),
                api_client.getAuditActivity(agentFilter, 100)
            ]);
            setStats(statsData);
            setActivity(activityData);
        } catch (err: any) {
            setError(err.message || 'Failed to fetch audit data');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchAuditData();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [agentFilter]);

    // Data Transformation for Recharts
    const chartData = useMemo(() => {
        if (!stats) return [];
        return stats.sessions_by_agent.map(item => ({
            name: item.agent.toUpperCase(),
            Sessions: item.sessions
        }));
    }, [stats]);

    const timelineData = useMemo(() => {
        if (!activity.length) return [];

        // Group activity by day
        const grouped: Record<string, { date: string, count: number }> = {};
        activity.forEach(msg => {
            if (!msg.timestamp) return;
            const day = new Date(msg.timestamp).toLocaleDateString();
            if (!grouped[day]) grouped[day] = { date: day, count: 0 };
            grouped[day].count++;
        });

        return Object.values(grouped).reverse();
    }, [activity]);

    if (loading && !stats) {
        return (
            <div className="audit-container flex-center">
                <div className="spinner"></div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="audit-container flex-center">
                <div className="error-message">
                    <AlertCircle size={24} />
                    <p>{error}</p>
                    <button onClick={fetchAuditData} className="btn-primary" style={{ marginTop: '1rem' }}>Retry</button>
                </div>
            </div>
        );
    }

    return (
        <div className="audit-container animate-fade-in">
            <header className="audit-header" style={{ marginBottom: '2rem' }}>
                <h1 style={{ background: 'linear-gradient(45deg, var(--primary), var(--info))', WebkitBackgroundClip: 'text', color: 'transparent', width: 'fit-content' }}>Platform Audit & Analytics</h1>
                <p>Monitor your system usage, visualised through rich analytics and automated metrics.</p>
            </header>

            {/* Top Level Metric Cards */}
            {stats && (
                <div className="stats-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1.5rem', marginBottom: '2rem' }}>
                    <div className="stat-card glass-panel" style={{ padding: '1.5rem', background: 'var(--bg-card)' }}>
                        <div className="stat-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', opacity: 0.8, marginBottom: '0.5rem' }}>
                            <Activity size={18} color="var(--primary)" /> <span>Total Sessions</span>
                        </div>
                        <div className="stat-value" style={{ fontSize: '2.5rem', color: 'var(--text-light)' }}>{stats.total_sessions}</div>
                    </div>
                    <div className="stat-card glass-panel" style={{ padding: '1.5rem', background: 'var(--bg-card)' }}>
                        <div className="stat-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', opacity: 0.8, marginBottom: '0.5rem' }}>
                            <Clock size={18} color="var(--info)" /> <span>Last 7 Days</span>
                        </div>
                        <div className="stat-value" style={{ fontSize: '2.5rem', color: 'var(--text-light)' }}>{stats.sessions_last_7_days}</div>
                    </div>
                    <div className="stat-card glass-panel" style={{ padding: '1.5rem', background: 'var(--bg-card)' }}>
                        <div className="stat-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', opacity: 0.8, marginBottom: '0.5rem' }}>
                            <MessageSquare size={18} color="var(--success)" /> <span>User Queries</span>
                        </div>
                        <div className="stat-value" style={{ fontSize: '2.5rem', color: 'var(--text-light)' }}>{stats.total_user_messages}</div>
                    </div>
                    <div className="stat-card glass-panel" style={{ padding: '1.5rem', background: 'var(--bg-card)' }}>
                        <div className="stat-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', opacity: 0.8, marginBottom: '0.5rem' }}>
                            <Bot size={18} color="var(--accent)" /> <span>AI Responses</span>
                        </div>
                        <div className="stat-value" style={{ fontSize: '2.5rem', color: 'var(--text-light)' }}>{stats.total_agent_messages}</div>
                    </div>
                </div>
            )}

            {/* Charts Section */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', marginBottom: '3rem' }}>
                <div className="glass-panel" style={{ padding: '1.5rem' }}>
                    <h3 style={{ marginBottom: '1.5rem', fontSize: '1.2rem', color: 'var(--text-light)' }}>Agent Engagement Distribution</h3>
                    <div style={{ width: '100%', height: 300 }}>
                        <ResponsiveContainer>
                            <BarChart data={chartData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                                <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={12} tickMargin={10} />
                                <YAxis stroke="var(--text-muted)" fontSize={12} />
                                <Tooltip
                                    contentStyle={{ background: 'var(--bg-dropdown)', border: '1px solid var(--border-color)', borderRadius: '8px' }}
                                    cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                                />
                                <Bar dataKey="Sessions" fill="var(--primary)" radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="glass-panel" style={{ padding: '1.5rem' }}>
                    <h3 style={{ marginBottom: '1.5rem', fontSize: '1.2rem', color: 'var(--text-light)' }}>Activity Volume</h3>
                    <div style={{ width: '100%', height: 300 }}>
                        <ResponsiveContainer>
                            <AreaChart data={timelineData}>
                                <defs>
                                    <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="var(--info)" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="var(--info)" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" vertical={false} />
                                <XAxis dataKey="date" stroke="var(--text-muted)" fontSize={12} tickMargin={10} />
                                <YAxis stroke="var(--text-muted)" fontSize={12} />
                                <Tooltip contentStyle={{ background: 'var(--bg-dropdown)', border: '1px solid var(--border-color)', borderRadius: '8px' }} />
                                <Area type="monotone" dataKey="count" stroke="var(--info)" fillOpacity={1} fill="url(#colorCount)" strokeWidth={3} />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            {/* Timeline List Section */}
            <h2 className="timeline-section-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-color)', paddingBottom: '1rem', marginBottom: '1.5rem' }}>
                Interaction Ledger
                <select
                    className="agent-filter"
                    value={agentFilter}
                    onChange={(e) => setAgentFilter(e.target.value)}
                    style={{ padding: '8px 16px', background: 'var(--bg-surface)', border: '1px solid var(--border-color)', color: 'var(--text)', borderRadius: '6px' }}
                >
                    <option value="all">All Agents</option>
                    <option value="diagnostic">Diagnostic (PRISM)</option>
                    <option value="wellbeing">Wellbeing (SAGE)</option>
                    <option value="virtual_doctor">Virtual Doctor (APOLLO)</option>
                    <option value="dietary">Dietary (NORA)</option>
                    <option value="insurance">Insurance (InsuCompass)</option>
                    <option value="visualisation">Visualisation (Nano Banana)</option>
                    <option value="orchestrator">Orchestrator (HALO)</option>
                </select>
            </h2>

            <div className="audit-timeline" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {activity.length === 0 ? (
                    <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                        No interaction history found for this view.
                    </div>
                ) : (
                    activity.map(item => (
                        <div key={item.id} className="timeline-item glass-panel" style={{ display: 'flex', padding: '1.5rem', gap: '1.5rem', alignItems: 'flex-start', background: 'var(--bg-card)' }}>
                            <div className="timeline-icon" style={{
                                background: item.role === 'user' ? 'var(--info)' : 'var(--accent)',
                                color: '#fff', padding: '10px', borderRadius: '50%', flexShrink: 0
                            }}>
                                {item.role === 'user' ? <MessageSquare size={20} /> : <Bot size={20} />}
                            </div>
                            <div className="timeline-content" style={{ flex: 1 }}>
                                <div className="timeline-meta" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                                    <strong style={{ fontSize: '1.1rem', color: 'var(--text-light)' }}>
                                        <span style={{ textTransform: 'uppercase', opacity: 0.8, letterSpacing: '1px', fontSize: '0.85rem' }}>{item.agent_type}</span> <span style={{ opacity: 0.5, margin: '0 8px' }}>•</span> {item.session_title}
                                    </strong>
                                    <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>{new Date(item.timestamp).toLocaleString()}</span>
                                </div>
                                <div className="timeline-text" style={{ background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: '8px', borderLeft: `3px solid ${item.role === 'user' ? 'var(--info)' : 'var(--accent)'}` }}>
                                    <span style={{
                                        display: 'inline-block', padding: '2px 8px', borderRadius: '4px', fontSize: '0.75rem',
                                        fontWeight: 'bold', textTransform: 'uppercase', marginBottom: '8px',
                                        background: item.role === 'user' ? 'rgba(56, 189, 248, 0.15)' : 'rgba(235, 78, 255, 0.15)',
                                        color: item.role === 'user' ? 'var(--info)' : 'var(--accent)'
                                    }}>
                                        {item.role}
                                    </span>
                                    <p style={{ margin: 0, color: 'var(--text)', lineHeight: 1.5 }}>
                                        {item.content_preview}
                                        {item.content_length > 200 ? <span style={{ color: 'var(--primary)', cursor: 'pointer' }}> ...read more</span> : ''}
                                    </p>
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default AuditDashboard;
