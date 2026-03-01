import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { User, Mail, Shield, Smartphone, Bell, Save } from 'lucide-react';
import './Settings.css';

const Settings: React.FC = () => {
    const { user } = useAuth();

    const [activeTab, setActiveTab] = useState('profile');

    const [formData, setFormData] = useState({
        fullName: user?.full_name || '',
        email: user?.email || '',
        currentPassword: '',
        newPassword: ''
    });

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSave = (e: React.FormEvent) => {
        e.preventDefault();
        // In a real application, this would dispatch an API call to update the profile
        alert("Profile updated successfully (Mock)");
    };

    return (
        <div className="settings-container animate-fade-in">
            <header className="settings-header">
                <h1>Profile & Preferences</h1>
                <p>Manage your HALO Health Enterprise account settings and security.</p>
            </header>

            <div className="settings-content">
                {/* Sidebar Navigation for Settings */}
                <div className="settings-nav">
                    <button className={`settings-tab ${activeTab === 'profile' ? 'active' : ''}`} onClick={() => setActiveTab('profile')}><User size={18} /> General Info</button>
                    <button className={`settings-tab ${activeTab === 'security' ? 'active' : ''}`} onClick={() => setActiveTab('security')}><Shield size={18} /> Security</button>
                    <button className={`settings-tab ${activeTab === 'notifications' ? 'active' : ''}`} onClick={() => setActiveTab('notifications')}><Bell size={18} /> Notifications</button>
                    <button className={`settings-tab ${activeTab === 'sessions' ? 'active' : ''}`} onClick={() => setActiveTab('sessions')}><Smartphone size={18} /> Sessions</button>
                </div>

                {/* Settings Form Area */}
                <div className="settings-form-container">
                    {activeTab === 'profile' && (
                        <form className="settings-form" onSubmit={handleSave}>
                            <div className="form-section animate-fade-in">
                                <h3>Personal Information</h3>
                                <div className="form-group">
                                    <label>Full Name</label>
                                    <div className="input-with-icon">
                                        <User size={18} className="input-icon" />
                                        <input
                                            type="text"
                                            name="fullName"
                                            value={formData.fullName}
                                            onChange={handleChange}
                                        />
                                    </div>
                                </div>
                                <div className="form-group">
                                    <label>Email Address</label>
                                    <div className="input-with-icon">
                                        <Mail size={18} className="input-icon" />
                                        <input
                                            type="email"
                                            name="email"
                                            value={formData.email}
                                            onChange={handleChange}
                                            disabled
                                            title="Email cannot be changed"
                                        />
                                    </div>
                                </div>
                            </div>
                            <div className="settings-footer">
                                <button type="button" className="btn-cancel">Cancel</button>
                                <button type="submit" className="btn-save">
                                    <Save size={18} /> Save Changes
                                </button>
                            </div>
                        </form>
                    )}

                    {activeTab === 'security' && (
                        <form className="settings-form animate-fade-in" onSubmit={handleSave}>
                            <div className="form-section">
                                <h3>Security Information</h3>
                                <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1rem' }}>Manage your passwords and two-factor authentication.</p>
                                <div className="form-group">
                                    <label>Current Password</label>
                                    <input
                                        type="password"
                                        name="currentPassword"
                                        value={formData.currentPassword}
                                        onChange={handleChange}
                                        placeholder="••••••••"
                                    />
                                </div>
                                <div className="form-group">
                                    <label>New Password</label>
                                    <input
                                        type="password"
                                        name="newPassword"
                                        value={formData.newPassword}
                                        onChange={handleChange}
                                        placeholder="••••••••"
                                    />
                                </div>
                            </div>
                            <div className="settings-footer">
                                <button type="submit" className="btn-save">
                                    Update Password
                                </button>
                            </div>
                        </form>
                    )}

                    {activeTab === 'notifications' && (
                        <div className="settings-form animate-fade-in">
                            <div className="form-section">
                                <h3>Notification Preferences</h3>
                                <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>Control what alerts and digests you receive from HALO Health.</p>

                                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                                        <input type="checkbox" defaultChecked /> Receive email alerts for Share events
                                    </label>
                                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                                        <input type="checkbox" defaultChecked /> Receive daily diagnostic digests
                                    </label>
                                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                                        <input type="checkbox" /> SMS alerts for Urgent Flagged Scans
                                    </label>
                                </div>
                            </div>
                        </div>
                    )}

                    {activeTab === 'sessions' && (
                        <div className="settings-form animate-fade-in">
                            <div className="form-section">
                                <h3>Active Sessions</h3>
                                <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>Review devices currently logged into your HALO Health Enterprise account.</p>

                                <div style={{ background: 'var(--bg-dark)', padding: '1rem', borderRadius: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                                    <div>
                                        <div style={{ fontWeight: 500, color: 'var(--text-main)' }}>Mac OS - Chrome (Current)</div>
                                        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Atlanta, GA • Active Now</div>
                                    </div>
                                    <span style={{ color: '#22c55e', fontSize: '0.8rem', fontWeight: 600 }}>CURRENT DEVICE</span>
                                </div>

                                <div style={{ background: 'var(--bg-dark)', padding: '1rem', borderRadius: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <div>
                                        <div style={{ fontWeight: 500, color: 'var(--text-main)' }}>iOS - Safari</div>
                                        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Atlanta, GA • Last active 2 hours ago</div>
                                    </div>
                                    <button style={{ background: 'transparent', border: 'none', color: 'var(--error)', cursor: 'pointer', fontSize: '0.9rem' }}>Revoke</button>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Settings;
