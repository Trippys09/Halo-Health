import React from 'react';
import { NavLink } from 'react-router-dom';
import {
    HeartPulse,
    Stethoscope,
    ShieldCheck,
    Apple,
    Bot,
    Activity,
    Eye,
    ChevronLeft,
    ChevronRight,
    LayoutDashboard,
    Info
} from 'lucide-react';
import './Layout.css';

interface SidebarProps {
    isCollapsed: boolean;
    toggleSidebar: () => void;
}

const agents = [
    { name: 'Dashboard', path: '/dashboard', icon: <LayoutDashboard size={20} /> },
    { name: 'About', path: '/about', icon: <Info size={20} /> },
    { name: 'Audit & Analytics', path: '/audit', icon: <Activity size={20} /> },
    { name: 'IRIS (Retinal)', path: '/chat/oculomics', icon: <Eye size={20} /> },
    { name: 'PRISM (Diagnostic)', path: '/chat/diagnostic', icon: <Stethoscope size={20} /> },
    { name: 'SAGE (Wellbeing)', path: '/chat/wellbeing', icon: <HeartPulse size={20} /> },
    { name: 'APOLLO (Virtual Dr)', path: '/chat/virtual-doctor', icon: <Bot size={20} /> },
    { name: 'NORA (Dietary)', path: '/chat/dietary', icon: <Apple size={20} /> },
    { name: 'COMPASS', path: '/chat/insurance', icon: <ShieldCheck size={20} /> },
    { name: 'HALO Orchestrator', path: '/chat/orchestrator', icon: <Bot size={20} /> },
];

export const Sidebar: React.FC<SidebarProps> = ({ isCollapsed, toggleSidebar }) => {
    return (
        <div className={`sidebar ${isCollapsed ? 'collapsed' : ''}`}>
            <div className="sidebar-header">
                {!isCollapsed && (
                    <div className="sidebar-logo">
                        <img src="/assets/logo.png" alt="HALO Health Logo" style={{ height: '32px', marginRight: '8px' }} />
                        HALO Health
                    </div>
                )}
                <button className="collapse-btn" onClick={toggleSidebar} title="Toggle Sidebar">
                    {isCollapsed ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
                </button>
            </div>

            <div className="sidebar-nav">
                {agents.map((agent) => (
                    <NavLink
                        key={agent.path}
                        to={agent.path}
                        className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                        title={isCollapsed ? agent.name : undefined}
                    >
                        <div className="nav-icon">{agent.icon}</div>
                        {!isCollapsed && <span className="nav-text">{agent.name}</span>}
                    </NavLink>
                ))}
            </div>

            {/* The User profile and logout are now in the Top Navbar, reducing clutter here */}
        </div>
    );
};
