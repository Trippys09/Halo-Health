import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Mic, MicOff, Volume2, X } from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './VoiceAssistant.css';

const AGENT_ROUTES: Record<string, string> = {
    'dashboard': '/dashboard',
    'home': '/dashboard',
    'about': '/about',
    'audit': '/audit',
    'analytics': '/audit',
    'settings': '/settings',
    'oculomics': '/chat/oculomics',
    'retinal': '/chat/oculomics',
    'iris': '/chat/oculomics',
    'prism': '/chat/diagnostic',
    'diagnostic': '/chat/diagnostic',
    'sage': '/chat/wellbeing',
    'wellbeing': '/chat/wellbeing',
    'counsellor': '/chat/wellbeing',
    'apollo': '/chat/virtual-doctor',
    'virtual doctor': '/chat/virtual-doctor',
    'doctor': '/chat/virtual-doctor',
    'nora': '/chat/dietary',
    'dietary': '/chat/dietary',
    'nutrition': '/chat/dietary',
    'insucompass': '/chat/insurance',
    'insurance': '/chat/insurance',
    'compass': '/chat/insurance',
    'orchestrator': '/chat/orchestrator',
    'aura': '/chat/orchestrator',
    'vista': '/chat/visualisation',
    'data': '/chat/visualisation',
    'visualisation': '/chat/visualisation',
    'profile': '/settings',
};

const AGENT_NAME_MAP: Record<string, string> = {
    'oculomics': 'oculomics',
    'iris': 'oculomics',
    'prism': 'diagnostic',
    'diagnostic': 'diagnostic',
    'sage': 'wellbeing',
    'wellbeing': 'wellbeing',
    'apollo': 'virtual-doctor',
    'doctor': 'virtual-doctor',
    'nora': 'dietary',
    'dietary': 'dietary',
    'insucompass': 'insurance',
    'insurance': 'insurance',
    'compass': 'insurance',
    'aura': 'orchestrator',
    'orchestrator': 'orchestrator',
    'vista': 'visualisation',
    'visualisation': 'visualisation',
};

type VAState = 'IDLE' | 'AWAITING_EMAIL' | 'CONFIRMING_EMAIL';

interface VoiceAssistantProps {
    onClose?: () => void;
}

export const VoiceAssistant: React.FC<VoiceAssistantProps> = ({ onClose }) => {
    const navigate = useNavigate();
    const location = useLocation();
    const { logout } = useAuth();

    const [isListening, setIsListening] = useState(false);
    const [transcript, setTranscript] = useState('');
    const [response, setResponse] = useState('Say "open IRIS", "go to profile", or "log out".');
    const [isVisible, setIsVisible] = useState(true);

    // Conversation State Machine
    const [convState, setConvState] = useState<VAState>('IDLE');
    const [pendingEmail, setPendingEmail] = useState('');

    const recognitionRef = useRef<any>(null);
    const synthRef = useRef<SpeechSynthesisUtterance | null>(null);

    // Forward declare startListening
    const startListeningRef = useRef<(silent?: boolean) => void>(() => { });

    const speak = useCallback((text: string, autoListenAfter = false) => {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 0.95;
        utterance.pitch = 1.05;
        utterance.volume = 0.9;

        const voices = window.speechSynthesis.getVoices();
        const pref = voices.find(v => v.name.includes('Google') || v.name.includes('Microsoft') || v.lang === 'en-US');
        if (pref) utterance.voice = pref;

        if (autoListenAfter) {
            utterance.onend = () => { startListeningRef.current(true); };
        }

        synthRef.current = utterance;
        window.speechSynthesis.speak(utterance);
    }, []);

    const emitToChat = (eventName: string, detail: any) => {
        window.dispatchEvent(new CustomEvent(eventName, { detail }));
    };

    // External speaker event (ChatAgent can ask VoiceAssistant to speak)
    useEffect(() => {
        const handleSpeak = (e: any) => {
            if (e.detail?.text) {
                setResponse(e.detail.text);
                speak(e.detail.text);
            }
        };
        window.addEventListener('voice-assistant-speak', handleSpeak);
        return () => window.removeEventListener('voice-assistant-speak', handleSpeak);
    }, [speak]);

    const formatEmail = (spoken: string) => {
        return spoken.toLowerCase()
            .replace(/\s+at\s+/g, '@')
            .replace(/\s+dot\s+/g, '.')
            .replace(/\s+/g, '');
    };

    const processCommand = useCallback((text: string) => {
        const lower = text.toLowerCase().trim();

        // ── STATE: AWAITING_EMAIL ──────────────────────────────────────
        if (convState === 'AWAITING_EMAIL') {
            const email = formatEmail(text);
            if (email.includes('@') && email.includes('.')) {
                setPendingEmail(email);
                setConvState('CONFIRMING_EMAIL');
                const msg = "Did you mean " + email + "? Say yes or no.";
                setResponse(msg);
                speak(msg, true);
            } else {
                const msg = "I didn't catch a valid email. Please say the email address again, like john at example dot com. Or say cancel.";
                setResponse(msg);
                speak(msg, true);
            }
            return;
        }

        // ── STATE: CONFIRMING_EMAIL ────────────────────────────────────
        if (convState === 'CONFIRMING_EMAIL') {
            if (lower.includes('yes') || lower.includes('correct') || lower.includes('right') || lower.includes('yep')) {
                setConvState('IDLE');
                if (!location.pathname.includes('/chat/')) {
                    const msg = "You are not in an active chat. Please open a chat first.";
                    setResponse(msg); speak(msg);
                    return;
                }
                const msg = "Sending chat to " + pendingEmail + " now...";
                setResponse(msg); speak(msg);
                emitToChat('voice-share-email', { email: pendingEmail });
                setPendingEmail('');
            } else if (lower.includes('no') || lower.includes('incorrect') || lower.includes('wrong')) {
                setConvState('AWAITING_EMAIL');
                const msg = "Okay, let's try again. What is the email address?";
                setResponse(msg); speak(msg, true);
            } else if (lower.includes('cancel')) {
                setConvState('IDLE');
                setResponse('Email sharing cancelled.'); speak('Email sharing cancelled.');
            } else {
                const msg = "Please just say yes or no, or cancel.";
                setResponse(msg); speak(msg, true);
            }
            return;
        }

        // ── STATE: IDLE ───────────────────────────────────────────────

        // 1. Cancel / Stop
        if (lower.match(/^(stop|cancel|nevermind|ignore)$/)) {
            setResponse('Okay.');
            return;
        }

        // 2. Share to Email
        if (lower.match(/(?:share|send) (?:chat|this |conversation )?(?:to )?email/i)) {
            if (!location.pathname.includes('/chat/')) {
                const msg = "You are not in a chat. Please navigate to an agent first to share a conversation.";
                setResponse(msg); speak(msg);
                return;
            }
            setConvState('AWAITING_EMAIL');
            const msg = "Sure. What email address should I send this conversation to?";
            setResponse(msg); speak(msg, true);
            return;
        }

        // 3. Enable / Disable Voice Mode
        const voiceTogggleMatch = lower.match(/(enable|disable|turn on|turn off) voice(?: for (.+))?/i);
        if (voiceTogggleMatch) {
            const action = voiceTogggleMatch[1].includes('enable') || voiceTogggleMatch[1].includes('on');
            const targetAgent = voiceTogggleMatch[2]?.trim();

            if (targetAgent) {
                // Find agent and route if needed
                const agentKey = Object.keys(AGENT_NAME_MAP).find(k => targetAgent.includes(k));
                if (agentKey) {
                    const mappedCode = AGENT_NAME_MAP[agentKey];
                    const route = AGENT_ROUTES[agentKey];

                    if (location.pathname !== route) {
                        navigate(route!);
                        setTimeout(() => {
                            emitToChat('voice-toggle-mode', { agentId: mappedCode, enable: action });
                        }, 500);
                    } else {
                        emitToChat('voice-toggle-mode', { agentId: mappedCode, enable: action });
                    }
                    const msg = "Voice mode " + (action ? 'enabled' : 'disabled') + " for " + agentKey + ".";
                    setResponse(msg); speak(msg);
                    return;
                }
            }

            // If no target agent specified, apply to current
            if (location.pathname.includes('/chat/')) {
                emitToChat('voice-toggle-mode', { enable: action });
                const msg = "Voice mode " + (action ? 'enabled' : 'disabled') + " for this chat.";
                setResponse(msg); speak(msg);
            } else {
                const msg = "Which agent do you want to enable voice for? For example, say Enable voice for SAGE.";
                setResponse(msg); speak(msg);
            }
            return;
        }

        // 4. Navigation
        const navMatch = lower.match(/(?:go to|open|navigate to|show|take me to)\s+(.+)/i);
        if (navMatch) {
            const target = navMatch[1].trim();

            if (target === 'logout' || target === 'log out' || target === 'sign out') {
                const msg = "Logging out. Goodbye!";
                setResponse(msg); speak(msg);
                setTimeout(() => logout(), 1500);
                return;
            }

            const route = AGENT_ROUTES[target];
            if (route) {
                navigate(route);
                const msg = "Navigating to " + target + ".";
                setResponse(msg); speak(msg);
                return;
            }
            const fuzzy = Object.entries(AGENT_ROUTES).find(([key]) => target.includes(key));
            if (fuzzy) {
                navigate(fuzzy[1]);
                const msg = "Navigating to " + fuzzy[0] + ".";
                setResponse(msg); speak(msg);
                return;
            }
        }

        // 5. Help
        if (lower.match(/(what can you do|help|commands)/i)) {
            const msg = 'Available commands: "Open IRIS", "Go to Profile", "Share to email", "Log out".';
            setResponse(msg); speak(msg);
            return;
        }

        // Fallback Ambiguity (Audio to Audio)
        const msg = "I didn't quite catch that. Could you repeat? You can say 'Open IRIS' or 'Go to profile'.";
        setResponse(msg);
        speak(msg, true); // auto listen after repeating

    }, [convState, pendingEmail, location.pathname, navigate, speak, logout]);

    const startListening = useCallback((silentStart = false) => {
        const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
        if (!SpeechRecognition) {
            setResponse('Voice recognition is not supported in this browser. Please use Chrome or Edge.');
            return;
        }

        // Stop current speech output if user interrupts
        window.speechSynthesis.cancel();

        try {
            recognitionRef.current?.stop();
        } catch (e) { }

        const recognition = new SpeechRecognition();
        recognition.lang = 'en-US';
        recognition.interimResults = true;
        recognition.continuous = false;
        recognition.maxAlternatives = 1;

        recognition.onstart = () => setIsListening(true);
        recognition.onend = () => setIsListening(false);
        recognition.onerror = () => {
            setIsListening(false);
            if (!silentStart) {
                setResponse('Could not hear you. Please try again.');
            }
        };
        recognition.onresult = (event: any) => {
            const t = Array.from(event.results)
                .map((r: any) => r[0].transcript)
                .join('');
            setTranscript(t);
            if (event.results[0].isFinal) {
                processCommand(t);
            }
        };

        recognitionRef.current = recognition;
        recognition.start();
    }, [processCommand]);

    useEffect(() => {
        startListeningRef.current = startListening;
    }, [startListening]);

    const stopListening = useCallback(() => {
        try { recognitionRef.current?.stop(); } catch (e) { }
        setIsListening(false);
    }, []);

    const handleClose = () => {
        stopListening();
        window.speechSynthesis.cancel();
        setIsVisible(false);
        onClose?.();
    };

    useEffect(() => {
        speak('HALO Voice Assistant ready. Please go ahead.');
        return () => {
            try { recognitionRef.current?.stop(); } catch (e) { }
            window.speechSynthesis.cancel();
        };
    }, []); // eslint-disable-line

    if (!isVisible) return null;

    return (
        <div className="voice-assistant-panel glass-panel animate-fade-in" role="dialog" aria-label="Voice Assistant">
            <div className="va-header">
                <div className="va-title">
                    <Volume2 size={18} />
                    <span>HALO Voice Navigator</span>
                </div>
                <button className="va-close" onClick={handleClose} aria-label="Close voice assistant">
                    <X size={16} />
                </button>
            </div>

            <div className="va-waveform">
                {[...Array(12)].map((_, i) => (
                    <div
                        key={i}
                        className={"va-bar " + (isListening ? 'active' : '')}
                        style={{ animationDelay: i * 0.08 + 's' }}
                    />
                ))}
            </div>

            <div className="va-transcript">
                {transcript || (isListening ? 'Listening...' : 'Press the mic to speak')}
            </div>

            <div className="va-response">{response}</div>

            <button
                className={"va-mic-btn " + (isListening ? 'listening' : '')}
                onClick={isListening ? stopListening : () => startListening(false)}
                aria-label={isListening ? 'Stop listening' : 'Start listening'}
            >
                {isListening ? <MicOff size={24} /> : <Mic size={24} />}
            </button>

            <div className="va-hint">
                Commands: <em>"Open IRIS"</em> · <em>"Go to Profile"</em> · <em>"Log out"</em>
            </div>
        </div>
    );
};

export default VoiceAssistant;
