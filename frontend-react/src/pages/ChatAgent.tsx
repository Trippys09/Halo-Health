import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import Markdown from 'markdown-to-jsx';
import {
    Send, Loader2, Paperclip, X, Plus, Share2,
    Clock, Mic, VolumeX, Volume2, StopCircle, FileText,
    Trash2, Edit2, Check
} from 'lucide-react';
import { api_client } from '../utils/api_client';
import { useAgentVoice } from '../hooks/useAgentVoice';
import ShareModal from '../components/ShareModal';
import { exportChatPDF } from '../utils/exportChatPDF';
import './ChatAgent.css';

/* ── Icons for agent avatars (no emojis) ──────────────────────────────── */
import {
    Eye, Stethoscope, HeartPulse, Bot, Apple, ShieldCheck, Brain, BarChart3
} from 'lucide-react';

interface Message {
    id?: number;
    role: 'user' | 'model' | 'assistant';
    content: string;
    image?: string;
    timestamp?: string;
}

interface SessionMeta {
    id: number;
    title: string;
    agent_type: string;
    created_at: string;
    updated_at?: string;
}

const agentInfo: Record<string, {
    name: string; role: string; color: string;
    Icon: React.FC<{ size?: number; strokeWidth?: number }>;
    systemPrompt: string;
}> = {
    'oculomics': { name: 'IRIS', role: 'Retina Engine', color: '#2563eb', Icon: Eye, systemPrompt: 'Hello! Upload a retinal scan or describe your ocular symptoms.' },
    'wellbeing': { name: 'SAGE', role: 'Wellbeing', color: '#10b981', Icon: HeartPulse, systemPrompt: "Hello, I'm SAGE. I'm here to listen and support you. How are you feeling today?" },
    'diagnostic': { name: 'PRISM', role: 'Diagnostic', color: '#0F52BA', Icon: Stethoscope, systemPrompt: 'Hello! Upload a medical scan or describe your diagnostic query.' },
    'virtual-doctor': { name: 'APOLLO', role: 'Virtual Doctor', color: '#ef4444', Icon: Bot, systemPrompt: "Hello! I'm APOLLO, your virtual doctor. Describe your symptoms and I'll provide a clinical assessment." },
    'dietary': { name: 'NORA', role: 'Dietary Advisor', color: '#f59e0b', Icon: Apple, systemPrompt: "Hi! I'm NORA. Tell me your dietary goals and I'll create a personalised meal plan." },
    'insurance': { name: 'COMPASS', role: 'Insurance Guide', color: '#3b82f6', Icon: ShieldCheck, systemPrompt: "Hello! I'm COMPASS. Ask me anything about health insurance plans, coverage, or eligibility." },
    'visualisation': { name: 'VISTA', role: 'Visualisation', color: '#8b5cf6', Icon: BarChart3, systemPrompt: 'Hello! I am VISTA. Describe the data or chart you need and I will generate it.' },
    'orchestrator': { name: 'HALO', role: 'Master Orchestrator', color: '#0F52BA', Icon: Brain, systemPrompt: "Hello! I'm HALO Orchestrator. Ask me anything health-related and I'll route it to the right specialist." },
};

const EXECUTION_STEPS = [
    'Analyzing context vectors...',
    'Querying clinical parameters...',
    'Routing to reasoning engine...',
    'Synthesizing response...',
    'Formatting output...',
];

const formatTs = (iso: string) => {
    if (!iso) return '';
    const d = new Date(iso);
    const now = new Date();
    const diff = (now.getTime() - d.getTime()) / 1000;
    if (diff < 60) return 'just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
};

const ChatAgent: React.FC = () => {
    const { agentId } = useParams<{ agentId: string }>();
    const [messages, setMessages] = useState<Message[]>([]);
    const [sessions, setSessions] = useState<SessionMeta[]>([]);
    const [activeSessionId, setActiveSessionId] = useState<number | null>(null);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [selectedImage, setSelectedImage] = useState<string | null>(null);
    const [executionLogIndex, setExecutionLogIndex] = useState(0);
    const [showShareModal, setShowShareModal] = useState(false);

    // Session Edit State
    const [editingSessionId, setEditingSessionId] = useState<number | null>(null);
    const [editTitle, setEditTitle] = useState('');

    // Voice
    const [voiceMode, setVoiceMode] = useState(false);
    const [isListening, setIsListening] = useState(false);
    const [isSpeaking, setIsSpeaking] = useState(false);
    const [voiceTranscript, setVoiceTranscript] = useState('');
    const recognitionRef = useRef<any>(null);
    const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
    const { speak, stop: stopSpeech, profile: voiceProfile } = useAgentVoice(agentId);

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const agent = agentId && agentInfo[agentId]
        ? agentInfo[agentId]
        : { name: 'Agent', role: 'Assistant', color: '#0F52BA', Icon: Bot, systemPrompt: 'Hello! How can I assist you?' };
    // Setup refs for preventing trailing responses bleeding across agents
    const activeAgentRef = useRef(agentId);
    useEffect(() => { activeAgentRef.current = agentId; }, [agentId]);

    const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    useEffect(() => { scrollToBottom(); }, [messages, loading]);

    // ── Execution log cycling ──────────────────────────────────────────────
    useEffect(() => {
        let interval: ReturnType<typeof setInterval>;
        if (loading) {
            setExecutionLogIndex(0);
            interval = setInterval(() => setExecutionLogIndex(i => (i + 1) % EXECUTION_STEPS.length), 1400);
        }
        return () => clearInterval(interval);
    }, [loading]);

    // ── Session management ─────────────────────────────────────────────────
    const fetchSessions = async () => {
        try {
            const all = await api_client.getSessions();
            if (agentId) {
                const norm = agentId.replace('-', '_');
                setSessions(all.filter((s: SessionMeta) => s.agent_type === norm).reverse());
            }
        } catch { /* silent */ }
    };

    const handleDeleteSession = async (e: React.MouseEvent, id: number) => {
        e.stopPropagation();
        if (!window.confirm("Are you sure you want to delete this session?")) return;
        try {
            await api_client.deleteSession(id);
            if (activeSessionId === id) startNewChat();
            fetchSessions();
        } catch (err) { alert("Failed to delete session"); }
    };

    const startRename = (e: React.MouseEvent, id: number, currentTitle: string) => {
        e.stopPropagation();
        setEditingSessionId(id);
        setEditTitle(currentTitle);
    };

    const saveRename = async (e: React.MouseEvent | React.KeyboardEvent, id: number) => {
        e.stopPropagation();
        if (!editTitle.trim()) { setEditingSessionId(null); return; }
        try {
            await api_client.renameSession(id, editTitle);
            setEditingSessionId(null);
            fetchSessions();
        } catch (err) { alert("Failed to rename session"); }
    };

    useEffect(() => { startNewChat(); fetchSessions(); }, [agentId]); // eslint-disable-line

    // ── Voice Assistant Event Listeners ────────────────────────────────────
    useEffect(() => {
        const handleVoiceToggle = (e: any) => {
            const { agentId: targetAgent, enable } = e.detail;
            // If no target agent specified, or if it matches the current route
            if (!targetAgent || targetAgent === agentId?.replace('-', '_')) {
                setVoiceMode(enable);
            }
        };

        const handleVoiceShareEmail = async (e: any) => {
            const email = e.detail.email;
            if (!email) return;

            const transcript = messages
                .filter(m => m.content && m.content !== agent.systemPrompt)
                .map(m => `[${m.role === 'user' ? 'You' : agent.name}]: ${m.content.replace(/\*\*/g, '').replace(/#{1,6}\s/g, '')}`)
                .join('\n\n');

            if (!transcript.trim()) {
                window.dispatchEvent(new CustomEvent('voice-assistant-speak', { detail: { text: 'The chat is currently empty.' } }));
                return;
            }

            try {
                await api_client.sendEmail({
                    to: email,
                    subject: `HALO Health Consultation: ${agent.name}`,
                    body: transcript
                });
                window.dispatchEvent(new CustomEvent('voice-assistant-speak', { detail: { text: `Chat transcript sent successfully to ${email}.` } }));
            } catch (err: any) {
                window.dispatchEvent(new CustomEvent('voice-assistant-speak', { detail: { text: "I'm sorry, I encountered an error and couldn't send the email." } }));
            }
        };

        window.addEventListener('voice-toggle-mode', handleVoiceToggle);
        window.addEventListener('voice-share-email', handleVoiceShareEmail);
        return () => {
            window.removeEventListener('voice-toggle-mode', handleVoiceToggle);
            window.removeEventListener('voice-share-email', handleVoiceShareEmail);
        };
    }, [agentId, messages, agent.name, agent.systemPrompt]);
    const startNewChat = () => {
        setActiveSessionId(null);
        setMessages([{ role: 'model', content: agent.systemPrompt, timestamp: new Date().toISOString() }]);
        setInput(''); setSelectedImage(null); setVoiceTranscript('');
    };

    const loadChat = async (sessionId: number) => {
        setActiveSessionId(sessionId);
        setLoading(true);
        try {
            const history = await api_client.getMessages(sessionId.toString());
            const formatted: Message[] = history.map((m: any) => ({
                id: m.id, role: m.role === 'assistant' ? 'model' : 'user',
                content: m.content, timestamp: m.created_at,
                image: m.image_data ? (m.image_data.startsWith('data:') ? m.image_data : `data:image/jpeg;base64,${m.image_data}`) : undefined
            }));
            setMessages(formatted.length ? formatted : [{ role: 'model', content: agent.systemPrompt, timestamp: new Date().toISOString() }]);
        } catch { /* silent */ } finally { setLoading(false); }
    };

    // ── Auto-resize textarea ───────────────────────────────────────────────
    const autoResize = (el: HTMLTextAreaElement) => {
        el.style.height = 'auto';
        el.style.height = Math.min(el.scrollHeight, 160) + 'px';
    };

    // ── Submit ─────────────────────────────────────────────────────────────
    const handleSubmit = async (text?: string) => {
        const userMessage = (text ?? input).trim();
        if ((!userMessage && !selectedImage) || !agentId || loading) return;
        const imagePayload = selectedImage;
        setInput(''); setSelectedImage(null); setVoiceTranscript('');
        if (textareaRef.current) { textareaRef.current.style.height = 'auto'; }

        const ts = new Date().toISOString();
        setMessages(prev => [...prev, { role: 'user', content: userMessage, image: imagePayload || undefined, timestamp: ts }]);
        setLoading(true);

        // Unlock TTS engine synchronously on user interaction (fixes async audio play on Safari/strict browsers)
        if (voiceMode) {
            window.speechSynthesis.speak(new SpeechSynthesisUtterance(''));
        }

        try {
            let sid = activeSessionId;
            if (!sid) {
                const sr = await api_client.startSession(agentId.replace('-', '_'));
                if (sr?.id) { sid = sr.id; setActiveSessionId(sid); fetchSessions(); }
            }
            const b64 = imagePayload ? imagePayload.split(',')[1] : undefined;
            const resp = await api_client.chatWithAgent(agentId, userMessage, sid || undefined, b64);
            if (!activeSessionId && resp.session_id) { setActiveSessionId(resp.session_id); fetchSessions(); }

            const reply = resp.reply || resp.response || 'No response received.';

            // Prevent bleeding if user navigated to a different agent while waiting
            if (activeAgentRef.current !== agentId) return;

            setMessages(prev => [...prev, { role: 'model', content: reply, timestamp: new Date().toISOString() }]);

            // Auto-speak if voice mode is on
            if (voiceMode) {
                setIsSpeaking(true);
                const utt = speak(reply);
                if (utt) {
                    utteranceRef.current = utt;
                    utt.onend = () => { setIsSpeaking(false); utteranceRef.current = null; };
                    utt.onerror = () => { setIsSpeaking(false); utteranceRef.current = null; };
                } else {
                    setIsSpeaking(false);
                }
            }
        } catch (err: any) {
            setMessages(prev => [...prev, {
                role: 'model', content: `**Error:** ${err.message || 'Request failed.'}`,
                timestamp: new Date().toISOString()
            }]);
        } finally { setLoading(false); }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit(); }
    };

    // ── Voice input ────────────────────────────────────────────────────────
    const startListening = () => {
        const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
        if (!SR) { alert('Voice input requires Chrome or Edge browser.'); return; }
        const rec = new SR();
        rec.lang = 'en-US';
        rec.interimResults = true;
        rec.continuous = false;
        rec.onstart = () => setIsListening(true);
        rec.onend = () => setIsListening(false);
        rec.onerror = () => setIsListening(false);
        rec.onresult = (event: any) => {
            const t = Array.from(event.results).map((r: any) => r[0].transcript).join('');
            setVoiceTranscript(t);
            if (event.results[event.results.length - 1].isFinal) {
                setVoiceTranscript('');
                handleSubmit(t);
            }
        };
        recognitionRef.current = rec;
        rec.start();
    };

    const stopListening = () => { recognitionRef.current?.stop(); setIsListening(false); };

    const toggleVoiceMode = () => {
        if (voiceMode) { stopListening(); stopSpeech(); }
        setVoiceMode(v => !v);
    };

    const stopSpeaking = () => {
        stopSpeech();
        if (utteranceRef.current) { utteranceRef.current.onend = null; utteranceRef.current = null; }
        setIsSpeaking(false);
    };

    // ── Chat transcript for sharing ────────────────────────────────────────
    const buildChatText = () => messages
        .filter(m => m.content && m.content !== agent.systemPrompt)
        .map(m => `[${m.role === 'user' ? 'You' : agent.name}]: ${m.content.replace(/\*\*/g, '').replace(/#{1,6}\s/g, '')}`)
        .join('\n\n');

    const handleExportPDF = () => {
        exportChatPDF({
            agentName: agent.name,
            agentRole: agent.role,
            messages,
        });
    };

    const AgentIcon = agent.Icon;

    return (
        <div className="chat-layout animate-fade-in">
            {/* ── Session Sidebar ──────────────────────────────────────── */}
            <aside className="chat-sidebar">
                <button className="chat-new-btn" onClick={startNewChat}>
                    <Plus size={16} />
                    <span>New Chat</span>
                </button>
                <p className="chat-sidebar-label">Recent Chats</p>
                <div className="chat-session-list">
                    {sessions.length === 0
                        ? <p className="chat-empty">No saved chats yet.</p>
                        : sessions.map(s => {
                            const title = s.title || `Chat · ${new Date(s.created_at).toLocaleDateString([], { month: 'short', day: 'numeric' })}`;
                            const isEditing = editingSessionId === s.id;
                            return (
                                <div key={s.id} className={`chat-session-item-wrapper ${activeSessionId === s.id ? 'active' : ''}`}>
                                    {isEditing ? (
                                        <div className="chat-session-edit">
                                            <input
                                                autoFocus
                                                value={editTitle}
                                                onChange={e => setEditTitle(e.target.value)}
                                                onKeyDown={e => e.key === 'Enter' && saveRename(e, s.id)}
                                            />
                                            <button onClick={(e) => saveRename(e, s.id)}><Check size={14} /></button>
                                        </div>
                                    ) : (
                                        <button
                                            className="chat-session-item"
                                            onClick={() => loadChat(s.id)}
                                            title={title}
                                        >
                                            <span className="session-title">{title}</span>
                                            <span className="session-ts">
                                                <Clock size={10} />
                                                {formatTs(s.updated_at || s.created_at)}
                                            </span>
                                            <div className="session-actions">
                                                <div onClick={(e) => startRename(e, s.id, title)}><Edit2 size={12} /></div>
                                                <div onClick={(e) => handleDeleteSession(e, s.id)}><Trash2 size={12} /></div>
                                            </div>
                                        </button>
                                    )}
                                </div>
                            );
                        })
                    }
                </div>
            </aside>

            {/* ── Main Chat ────────────────────────────────────────────── */}
            <div className="chat-main">
                {/* Header */}
                <header className="chat-header">
                    <div className="chat-header-agent">
                        <div className="chat-agent-icon" style={{ color: agent.color, background: `${agent.color}12` }}>
                            <AgentIcon size={20} strokeWidth={1.8} />
                        </div>
                        <div>
                            <span className="chat-agent-name">{agent.name}</span>
                            <span className="chat-agent-role">{agent.role}</span>
                        </div>
                        {voiceMode && (
                            <span className="voice-mode-badge" style={{ background: `${agent.color}15`, color: agent.color }}>
                                <Mic size={11} /> {voiceProfile.label} Voice
                            </span>
                        )}
                    </div>
                    <div className="chat-header-actions">
                        <button
                            className={`chat-action-btn ${voiceMode ? 'active' : ''}`}
                            onClick={toggleVoiceMode}
                            title={voiceMode ? 'Disable voice mode' : 'Enable voice mode'}
                            style={voiceMode ? { color: agent.color, background: `${agent.color}12` } : {}}
                        >
                            {voiceMode ? <Volume2 size={16} /> : <VolumeX size={16} />}
                            <span>{voiceMode ? 'Voice On' : 'Voice Off'}</span>
                        </button>
                        <button
                            className="chat-action-btn"
                            onClick={handleExportPDF}
                            title="Download Clinical Report as PDF"
                        >
                            <FileText size={16} />
                            <span>Export PDF</span>
                        </button>
                        <button
                            className="chat-action-btn"
                            onClick={() => setShowShareModal(true)}
                            title="Share conversation"
                        >
                            <Share2 size={16} />
                            <span>Share</span>
                        </button>
                    </div>
                </header>

                {/* Voice mode speaking indicator */}
                {isSpeaking && (
                    <div className="speaking-indicator" style={{ borderColor: agent.color }}>
                        <div className="speaking-bars">
                            {[...Array(5)].map((_, i) => (
                                <div key={i} className="speaking-bar" style={{ background: agent.color, animationDelay: `${i * 0.1}s` }} />
                            ))}
                        </div>
                        <span style={{ color: agent.color }}>{agent.name} is speaking</span>
                        <button className="speaking-stop" onClick={stopSpeaking} style={{ color: agent.color }}>
                            <StopCircle size={14} /> Stop
                        </button>
                    </div>
                )}

                {/* Messages */}
                <div className="chat-messages-area">
                    <div className="chat-messages-inner">
                        {messages.map((msg, index) => {
                            const isUser = msg.role === 'user';
                            return (
                                <div key={index} className={`chat-message ${isUser ? 'user-message' : 'agent-message'}`}>
                                    {!isUser && (
                                        <div className="msg-avatar agent-msg-avatar" style={{ background: `${agent.color}12`, color: agent.color }}>
                                            <AgentIcon size={16} strokeWidth={1.8} />
                                        </div>
                                    )}
                                    <div className="msg-body">
                                        {!isUser && (
                                            <div className="msg-sender-row">
                                                <span className="msg-sender">{agent.name}</span>
                                                {msg.timestamp && <span className="msg-time">{new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>}
                                            </div>
                                        )}
                                        {msg.image && (
                                            <div className="msg-image">
                                                <img src={msg.image} alt="Attached scan" />
                                            </div>
                                        )}
                                        {isUser ? (
                                            <div className="msg-bubble user-bubble">
                                                {msg.content}
                                                {msg.timestamp && <span className="bubble-time">{new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>}
                                            </div>
                                        ) : (
                                            <div className="msg-prose markdown-prose">
                                                <Markdown>{msg.content}</Markdown>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            );
                        })}

                        {/* Typing indicator */}
                        {loading && (
                            <div className="chat-message agent-message">
                                <div className="msg-avatar agent-msg-avatar" style={{ background: `${agent.color}12`, color: agent.color }}>
                                    <AgentIcon size={16} strokeWidth={1.8} />
                                </div>
                                <div className="msg-body">
                                    <div className="msg-sender-row">
                                        <span className="msg-sender">{agent.name}</span>
                                    </div>
                                    <div className="msg-typing">
                                        <div className="typing-dots">
                                            <span /><span /><span />
                                        </div>
                                        <span className="exec-step-text">{EXECUTION_STEPS[executionLogIndex]}</span>
                                    </div>
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>
                </div>

                {/* Input Area */}
                <div className="chat-input-area">
                    {/* Voice transcript preview */}
                    {voiceMode && isListening && voiceTranscript && (
                        <div className="voice-transcript-preview">
                            <Mic size={13} style={{ opacity: 0.6 }} />
                            <span>{voiceTranscript}</span>
                        </div>
                    )}

                    <div className="chat-input-box">
                        {selectedImage && (
                            <div className="attachment-tray">
                                <img src={selectedImage} alt="Attachment" />
                                <button className="remove-attachment" onClick={() => setSelectedImage(null)}>
                                    <X size={12} />
                                </button>
                            </div>
                        )}

                        <div className="chat-input-row">
                            {/* Attach */}
                            {!voiceMode && (
                                <>
                                    <button
                                        className="input-icon-btn"
                                        title="Attach file or image"
                                        onClick={() => fileInputRef.current?.click()}
                                    >
                                        <Paperclip size={18} strokeWidth={1.8} />
                                    </button>
                                    <input
                                        type="file"
                                        accept="image/jpeg,image/png,image/jpg"
                                        ref={fileInputRef}
                                        style={{ display: 'none' }}
                                        onChange={e => {
                                            const f = e.target.files?.[0];
                                            if (!f) return;
                                            const r = new FileReader();
                                            r.onload = ev => setSelectedImage(ev.target?.result as string);
                                            r.readAsDataURL(f);
                                            if (fileInputRef.current) fileInputRef.current.value = '';
                                        }}
                                    />
                                </>
                            )}

                            {/* Textarea or voice prompt */}
                            {voiceMode ? (
                                <div className="voice-mode-input">
                                    {isListening
                                        ? <span className="voice-listening-hint">Listening — speak now...</span>
                                        : <span className="voice-idle-hint">Press the mic to speak</span>
                                    }
                                </div>
                            ) : (
                                <textarea
                                    ref={textareaRef}
                                    className="chat-textarea"
                                    style={{
                                        resize: 'none',
                                        overflow: 'hidden',
                                        minHeight: '24px',
                                        maxHeight: '160px'
                                    }}
                                    placeholder={`Message ${agent.name} (or attach info)...`}
                                    disabled={loading || voiceMode}
                                    rows={1}
                                    onChange={e => { setInput(e.target.value); autoResize(e.target); }}
                                    onKeyDown={handleKeyDown}
                                />
                            )}

                            {/* Mic button (voice mode) */}
                            {voiceMode && (
                                <button
                                    className={`input-mic-btn ${isListening ? 'listening' : ''}`}
                                    onClick={isListening ? stopListening : startListening}
                                    title={isListening ? 'Stop listening' : 'Speak now'}
                                    style={isListening ? { background: '#ef4444', color: 'white', borderColor: '#ef4444' } : {}}
                                >
                                    {isListening ? <StopCircle size={24} color="white" /> : <Mic size={24} />}
                                </button>
                            )}

                            {/* Send button */}
                            {!voiceMode && (
                                <button
                                    className="input-send-btn"
                                    style={{ background: agent.color }}
                                    disabled={(!input.trim() && !selectedImage) || loading}
                                    onClick={() => handleSubmit()}
                                    title="Send message"
                                >
                                    {loading ? <Loader2 size={16} className="spin" /> : <Send size={16} />}
                                </button>
                            )}
                        </div>
                    </div>

                    <p className="chat-disclaimer">
                        AI-generated responses require clinical verification. Not for sole diagnostic use.
                        {voiceMode && <> · <strong style={{ color: agent.color }}>{voiceProfile.label}</strong> voice active.</>}
                    </p>
                </div>
            </div>

            {/* ── Share Modal ──────────────────────────────────────────── */}
            {showShareModal && (
                <ShareModal
                    agentName={agent.name}
                    agentRole={agent.role}
                    chatText={buildChatText()}
                    onClose={() => setShowShareModal(false)}
                    onExportPDF={handleExportPDF}
                />
            )}

        </div>
    );
};

export default ChatAgent;
