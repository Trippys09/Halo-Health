import React, { useState } from 'react';
import { X, Mail, MessageCircle, Send, Phone, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';
import { api_client } from '../utils/api_client';
import './ShareModal.css';

interface ShareModalProps {
    agentName: string;
    agentRole: string;
    chatText: string;
    onClose: () => void;
    onExportPDF?: () => void;
}

const COUNTRY_CODES = [
    { code: '+1', label: 'US/CA' },
    { code: '+44', label: 'UK' },
    { code: '+91', label: 'IN' },
    { code: '+61', label: 'AU' },
    { code: '+49', label: 'DE' },
    { code: '+33', label: 'FR' },
    { code: '+86', label: 'CN' },
    { code: '+81', label: 'JP' },
    { code: '+82', label: 'KR' },
    { code: '+971', label: 'UAE' },
    { code: '+966', label: 'SA' },
    { code: '+55', label: 'BR' },
    { code: '+52', label: 'MX' },
];

const ShareModal: React.FC<ShareModalProps> = ({ agentName, agentRole, chatText, onClose }) => {
    const [tab, setTab] = useState<'email' | 'whatsapp'>('email');

    // Email state
    const [toEmail, setToEmail] = useState('');
    const [subject, setSubject] = useState(`HALO Health ${agentName} Consultation — ${new Date().toLocaleDateString()}`);
    const [emailStatus, setEmailStatus] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle');
    const [emailError, setEmailError] = useState('');

    // WhatsApp state
    const [countryCode, setCountryCode] = useState('+1');
    const [phoneNumber, setPhoneNumber] = useState('');
    const [waStatus, setWaStatus] = useState<'idle' | 'unavailable' | 'sending' | 'sent' | 'error'>('idle');

    // PDF Attachment capability
    const canAttachPdf = agentName.includes('PRISM') || agentName.includes('Oculomics');
    const [attachPdf, setAttachPdf] = useState(canAttachPdf);

    // ── Email ────────────────────────────────────────────────────────────────
    const sendEmail = async () => {
        if (!toEmail.trim()) {
            setEmailError('Please enter a recipient email address.');
            return;
        }
        setEmailStatus('sending');
        setEmailError('');
        const body =
            `HALO Health AI Healthcare Platform\n` +
            `Agent: ${agentName} (${agentRole})\n` +
            `Date: ${new Date().toLocaleString()}\n\n` +
            `${'─'.repeat(50)}\n\n` +
            chatText +
            `\n\n${'─'.repeat(50)}\n` +
            `AI-generated content. Not a substitute for professional medical advice.`;
        try {
            await api_client.sendEmail({
                to: toEmail,
                subject,
                body,
                agent_name: agentName,
                include_pdf: attachPdf
            });
            setEmailStatus('sent');
            window.dispatchEvent(new CustomEvent('SHOW_NOTIFICATION', {
                detail: { message: `Secure Email sent successfully to ${toEmail}`, type: 'success' }
            }));
        } catch (err: any) {
            setEmailStatus('error');
            const errorMsg = err?.response?.data?.detail || err.message || 'Failed to send email.';
            setEmailError(errorMsg);
            window.dispatchEvent(new CustomEvent('SHOW_NOTIFICATION', {
                detail: { message: `Email failed: ${errorMsg}`, type: 'error' }
            }));
        }
    };

    // ── WhatsApp ──────────────────────────────────────────────────────────────
    const sendWhatsApp = async () => {
        const raw = phoneNumber.replace(/\D/g, '');
        if (!raw || raw.length < 7) {
            setWaStatus('unavailable');
            return;
        }
        const fullNumber = `${countryCode.replace('+', '')}${raw}`;
        const text = `*HALO Health ${agentName} Consultation*\n` +
            `_${new Date().toLocaleString()}_\n\n` +
            chatText.substring(0, 1500) +
            `\n\n_AI-generated. Not medical advice._`;

        try {
            setWaStatus('sending');
            await api_client.sendWhatsApp({
                phone_number: fullNumber,
                message: text,
                agent_name: agentName,
                include_pdf: attachPdf
            });
            setWaStatus('sent');
            window.dispatchEvent(new CustomEvent('SHOW_NOTIFICATION', {
                detail: { message: `WhatsApp message successfully sent to ${fullNumber}`, type: 'success' }
            }));
        } catch (err: any) {
            setWaStatus('error');
            window.dispatchEvent(new CustomEvent('SHOW_NOTIFICATION', {
                detail: { message: `Failed to send WhatsApp message`, type: 'error' }
            }));
        }
    };

    return (
        <div className="share-modal-overlay" role="dialog" aria-modal="true" aria-label="Share conversation">
            <div className="share-modal glass-panel animate-fade-in">
                {/* Header */}
                <div className="share-modal-header">
                    <div className="share-modal-title">
                        <Send size={18} />
                        <span>Share Conversation</span>
                    </div>
                    <button className="share-modal-close" onClick={onClose} aria-label="Close">
                        <X size={18} />
                    </button>
                </div>

                {/* Tabs */}
                <div className="share-tabs">
                    <button
                        className={`share-tab ${tab === 'email' ? 'active' : ''}`}
                        onClick={() => setTab('email')}
                    >
                        <Mail size={15} /> Email
                    </button>
                    <button
                        className={`share-tab ${tab === 'whatsapp' ? 'active' : ''}`}
                        onClick={() => setTab('whatsapp')}
                    >
                        <Phone size={15} /> WhatsApp
                    </button>
                </div>

                {/* Email Tab */}
                {tab === 'email' && (
                    <div className="share-content">
                        {emailStatus === 'sent' ? (
                            <div className="share-success">
                                <CheckCircle2 size={40} className="success-icon" />
                                <h3>Email Sent</h3>
                                <p>Conversation sent to <strong>{toEmail}</strong></p>
                                <button className="share-btn-secondary" onClick={() => setEmailStatus('idle')}>
                                    Send Another
                                </button>
                            </div>
                        ) : (
                            <>
                                <div className="form-field">
                                    <label>Recipient Email</label>
                                    <input
                                        type="email"
                                        className="share-input"
                                        placeholder="patient@example.com"
                                        value={toEmail}
                                        onChange={e => setToEmail(e.target.value)}
                                        autoFocus
                                    />
                                </div>
                                <div className="form-field">
                                    <label>Subject</label>
                                    <input
                                        type="text"
                                        className="share-input"
                                        value={subject}
                                        onChange={e => setSubject(e.target.value)}
                                    />
                                </div>
                                <div className="form-field">
                                    <label>Conversation Preview</label>
                                    <div className="share-preview">
                                        {chatText.substring(0, 300)}{chatText.length > 300 ? '...' : ''}
                                    </div>
                                </div>
                                {emailError && (
                                    <div className="share-error">
                                        <AlertCircle size={15} /> {emailError}
                                    </div>
                                )}
                                {canAttachPdf && (
                                    <div className="pdf-attach-toggle" style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem', color: '#334155' }}>
                                        <input
                                            type="checkbox"
                                            id="attachPdfEmail"
                                            checked={attachPdf}
                                            onChange={(e) => setAttachPdf(e.target.checked)}
                                            style={{ cursor: 'pointer', width: '16px', height: '16px', accentColor: 'var(--primary)' }}
                                        />
                                        <label htmlFor="attachPdfEmail" style={{ cursor: 'pointer' }}>Attach Full PDF Report</label>
                                    </div>
                                )}
                                <button
                                    className="share-btn-primary"
                                    onClick={sendEmail}
                                    disabled={emailStatus === 'sending'}
                                >
                                    {emailStatus === 'sending'
                                        ? <><Loader2 size={16} className="spin" /> Sending...</>
                                        : <><Send size={16} /> Send via Gmail</>
                                    }
                                </button>
                                <p className="share-hint">
                                    Emails are sent from the HALO Health platform Gmail account configured by your administrator.
                                </p>
                            </>
                        )}
                    </div>
                )}

                {/* WhatsApp Tab */}
                {tab === 'whatsapp' && (
                    <div className="share-content">
                        {waStatus === 'sent' ? (
                            <div className="share-success">
                                <CheckCircle2 size={40} className="success-icon" />
                                <h3>Message Sent</h3>
                                <p>WhatsApp message delivered to <strong>{countryCode} {phoneNumber}</strong></p>
                                <button className="share-btn-secondary" onClick={() => setWaStatus('idle')}>
                                    Send Another
                                </button>
                            </div>
                        ) : (
                            <>
                                {waStatus === 'unavailable' && (
                                    <div className="share-error wa-error">
                                        <AlertCircle size={15} />
                                        Please confirm the correct country code and phone number.
                                    </div>
                                )}
                                {waStatus === 'error' && (
                                    <div className="share-error wa-error">
                                        <AlertCircle size={15} />
                                        Failed to send WhatsApp message. Please try again.
                                    </div>
                                )}
                                <div className="form-field">
                                    <label>Phone Number</label>
                                    <div className="phone-input-row">
                                        <select
                                            className="country-select"
                                            value={countryCode}
                                            onChange={e => setCountryCode(e.target.value)}
                                        >
                                            {COUNTRY_CODES.map(c => (
                                                <option key={c.code} value={c.code}>
                                                    {c.code} {c.label}
                                                </option>
                                            ))}
                                        </select>
                                        <input
                                            type="tel"
                                            className="share-input phone-number-input"
                                            placeholder="(555) 123-4567"
                                            value={phoneNumber}
                                            onChange={e => {
                                                setPhoneNumber(e.target.value);
                                                setWaStatus('idle');
                                            }}
                                        />
                                    </div>
                                </div>
                                <div className="form-field">
                                    <label>Message Preview</label>
                                    <div className="share-preview">
                                        {chatText.substring(0, 300)}{chatText.length > 300 ? '...' : ''}
                                    </div>
                                </div>
                                {canAttachPdf && (
                                    <div className="pdf-attach-toggle" style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem', color: '#334155' }}>
                                        <input
                                            type="checkbox"
                                            id="attachPdfWa"
                                            checked={attachPdf}
                                            onChange={(e) => setAttachPdf(e.target.checked)}
                                            style={{ cursor: 'pointer', width: '16px', height: '16px', accentColor: '#25D366' }}
                                        />
                                        <label htmlFor="attachPdfWa" style={{ cursor: 'pointer' }}>Generate PDF Report Link</label>
                                    </div>
                                )}
                                <button
                                    className="share-btn-whatsapp"
                                    onClick={sendWhatsApp}
                                    disabled={waStatus === 'sending'}
                                >
                                    {waStatus === 'sending'
                                        ? <><Loader2 size={16} className="spin" /> Sending...</>
                                        : <><MessageCircle size={16} /> Send directly via WhatsApp</>}
                                </button>
                                <p className="share-hint">
                                    Delivers message directly via HALO Health infrastructure without opening your WhatsApp application.
                                </p>
                            </>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default ShareModal;
