import React, { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Navbar } from './Navbar';
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react';
import './Layout.css';

export const Layout: React.FC = () => {
    const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

    // Global Notification State
    const [notification, setNotification] = useState<{ message: string, type: 'success' | 'error' | 'info' } | null>(null);

    useEffect(() => {
        const handleNotification = (e: Event) => {
            const customEvent = e as CustomEvent<{ message: string, type: 'success' | 'error' | 'info' }>;
            setNotification(customEvent.detail);

            // Auto close after 4 seconds
            setTimeout(() => {
                setNotification(null);
            }, 4000);
        };

        window.addEventListener('SHOW_NOTIFICATION', handleNotification);
        return () => window.removeEventListener('SHOW_NOTIFICATION', handleNotification);
    }, []);

    return (
        <div className={`layout-container ${isSidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
            <Sidebar isCollapsed={isSidebarCollapsed} toggleSidebar={() => setIsSidebarCollapsed(!isSidebarCollapsed)} />
            <div className="main-stage">
                <Navbar />
                <main className="main-content">
                    <div className="page-wrapper">
                        <Outlet />
                    </div>
                </main>
            </div>

            {/* Global Toast Notification */}
            {notification && (
                <div className={`global-toast toast-${notification.type} animate-slide-up`}>
                    <div className="toast-icon">
                        {notification.type === 'success' && <CheckCircle2 size={20} />}
                        {notification.type === 'error' && <AlertCircle size={20} />}
                        {notification.type === 'info' && <Info size={20} />}
                    </div>
                    <div className="toast-message">{notification.message}</div>
                    <button className="toast-close" onClick={() => setNotification(null)}>
                        <X size={16} />
                    </button>
                </div>
            )}
        </div>
    );
};
