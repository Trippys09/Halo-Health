import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Bell, Search, Settings, User, Info, Mic, MicOff } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { VoiceAssistant } from './VoiceAssistant';

export const Navbar: React.FC = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const [showProfileMenu, setShowProfileMenu] = useState(false);
    const [showVoiceAssistant, setShowVoiceAssistant] = useState(false);

    // Search Bar State
    const [searchQuery, setSearchQuery] = useState('');
    const [showSearchDropdown, setShowSearchDropdown] = useState(false);

    // List of searchable destinations
    const searchOptions = [
        { name: 'Dashboard', path: '/dashboard', type: 'Page' },
        { name: 'Audit & Analytics', path: '/audit', type: 'Page' },
        { name: 'Oculomics AI (Retinal)', path: '/chat/oculomics', type: 'Agent' },
        { name: 'PRISM Clinical AI', path: '/chat/diagnostic', type: 'Agent' },
        { name: 'SAGE Wellbeing', path: '/chat/wellbeing', type: 'Agent' },
        { name: 'APOLLO Virtual Doctor', path: '/chat/virtual-doctor', type: 'Agent' },
        { name: 'NORA Dietary', path: '/chat/dietary', type: 'Agent' },
        { name: 'InsuCompass', path: '/chat/insurance', type: 'Agent' },
        { name: 'Orchestrator', path: '/chat/orchestrator', type: 'Agent' },
        { name: 'Settings & Profile', path: '/settings', type: 'Settings' }
    ];

    const filteredSearch = searchOptions.filter(opt =>
        opt.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        opt.type.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    return (
        <>
            <header className="top-navbar">
                <div className="navbar-search" style={{ position: 'relative' }}>
                    <Search size={18} className="search-icon" />
                    <input
                        type="text"
                        placeholder="Search agents, sessions, or ask HALO..."
                        value={searchQuery}
                        onChange={(e) => {
                            setSearchQuery(e.target.value);
                            setShowSearchDropdown(true);
                        }}
                        onFocus={() => setShowSearchDropdown(true)}
                        onBlur={() => setTimeout(() => setShowSearchDropdown(false), 200)}
                    />

                    {showSearchDropdown && searchQuery && (
                        <div className="search-dropdown dropdown-menu">
                            {filteredSearch.length > 0 ? (
                                filteredSearch.map((opt, idx) => (
                                    <button
                                        key={idx}
                                        className="search-dropdown-item"
                                        onClick={() => {
                                            navigate(opt.path);
                                            setSearchQuery('');
                                            setShowSearchDropdown(false);
                                        }}
                                    >
                                        <div className="search-item-name">{opt.name}</div>
                                        <div className="search-item-type">{opt.type}</div>
                                    </button>
                                ))
                            ) : (
                                <div className="search-dropdown-empty">No results found for "{searchQuery}"</div>
                            )}
                        </div>
                    )}
                </div>

                <div className="navbar-actions">
                    {/* Voice Assistant Toggle */}
                    <button
                        className={`icon-btn voice-nav-btn ${showVoiceAssistant ? 'voice-active' : ''}`}
                        onClick={() => setShowVoiceAssistant(v => !v)}
                        title="Voice Navigator — say 'go to APOLLO' to navigate"
                        aria-label="Voice Navigator"
                    >
                        {showVoiceAssistant ? <MicOff size={20} /> : <Mic size={20} />}
                    </button>

                    <Link to="/about" className="icon-btn" title="About HALO Health">
                        <Info size={20} />
                    </Link>

                    <button className="icon-btn">
                        <Bell size={20} />
                        <span className="notification-dot"></span>
                    </button>

                    <div className="profile-dropdown-container">
                        <button
                            className="profile-btn"
                            onClick={() => setShowProfileMenu(!showProfileMenu)}
                        >
                            <div className="avatar-sm">
                                {user?.full_name ? user.full_name[0].toUpperCase() : 'U'}
                            </div>
                            <span className="profile-name">{user?.full_name?.split(' ')[0] || 'User'}</span>
                        </button>

                        {showProfileMenu && (
                            <div className="profile-menu">
                                <div className="menu-header">
                                    <strong>{user?.full_name || 'System User'}</strong>
                                    <span>{user?.email}</span>
                                </div>
                                <Link to="/settings" className="menu-item" onClick={() => setShowProfileMenu(false)}>
                                    <User size={16} /> My Profile
                                </Link>
                                <Link to="/settings" className="menu-item" onClick={() => setShowProfileMenu(false)}>
                                    <Settings size={16} /> Preferences
                                </Link>
                                <div className="menu-divider"></div>
                                <button className="menu-item text-danger" onClick={handleLogout}>
                                    Sign Out
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </header>

            {/* Voice Assistant Panel */}
            {showVoiceAssistant && (
                <VoiceAssistant onClose={() => setShowVoiceAssistant(false)} />
            )}
        </>
    );
};
