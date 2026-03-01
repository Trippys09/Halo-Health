/**
 * useAgentVoice — Per-agent TTS voice profiles
 *
 * Each agent has a distinct voice personality:
 *  - SAGE (wellbeing):    slow, warm, empathetic
 *  - PRISM (diagnostic):  clear, measured, clinical bold
 *  - APOLLO (doctor):     authoritative, steady
 *  - NORA (dietary):      bright, upbeat
 *  - InsuCompass:         calm, professional
 *  - Orchestrator:        neutral, confident
 *  - Oculomics:           precise, clinical
 */

export interface VoiceProfile {
    rate: number;      // 0.1 – 2.0
    pitch: number;     // 0.0 – 2.0
    volume: number;    // 0.0 – 1.0
    /** Optional preferred voice name fragments (matched against available voices) */
    preferredVoice?: string[];
    /** Label shown in UI */
    label: string;
}

// Ensure voices are loaded into the browser registry ASAP
if (typeof window !== 'undefined' && window.speechSynthesis) {
    window.speechSynthesis.getVoices();
    window.speechSynthesis.onvoiceschanged = () => {
        window.speechSynthesis.getVoices();
    };
}

const VOICE_PROFILES: Record<string, VoiceProfile> = {
    wellbeing: {
        rate: 0.82,
        pitch: 1.18,
        volume: 0.88,
        preferredVoice: ['Samantha', 'Karen', 'Victoria', 'Google UK English Female'],
        label: 'Empathetic',
    },
    diagnostic: {
        rate: 1.0,
        pitch: 0.88,
        volume: 0.95,
        preferredVoice: ['Microsoft David', 'Google UK English Male', 'Daniel'],
        label: 'Clinical',
    },
    oculomics: {
        rate: 0.95,
        pitch: 0.88,
        volume: 0.95,
        preferredVoice: ['Microsoft David', 'Google UK English Male', 'Daniel'],
        label: 'Precise',
    },
    'virtual-doctor': {
        rate: 0.92,
        pitch: 0.95,
        volume: 0.95,
        preferredVoice: ['Microsoft Mark', 'Google US English Male', 'Alex'],
        label: 'Authoritative',
    },
    dietary: {
        rate: 1.05,
        pitch: 1.1,
        volume: 0.9,
        preferredVoice: ['Samantha', 'Moira', 'Google US English Female'],
        label: 'Bright',
    },
    insurance: {
        rate: 0.95,
        pitch: 1.0,
        volume: 0.9,
        preferredVoice: ['Microsoft Zira', 'Google US English Female', 'Samantha'],
        label: 'Professional',
    },
    orchestrator: {
        rate: 1.0,
        pitch: 1.0,
        volume: 0.92,
        preferredVoice: ['Google US English Male', 'Alex', 'Microsoft David'],
        label: 'Confident',
    },
};

const DEFAULT_PROFILE: VoiceProfile = {
    rate: 1.0,
    pitch: 1.0,
    volume: 0.9,
    label: 'Neutral',
};

function pickVoice(prefs: string[] | undefined): SpeechSynthesisVoice | null {
    const voices = window.speechSynthesis.getVoices();
    if (!voices.length) return null;

    if (prefs) {
        for (const pref of prefs) {
            const match = voices.find(v => v.name.includes(pref));
            if (match) return match;
        }
    }
    // Fallback: any en-US or en-GB voice
    return voices.find(v => v.lang.startsWith('en')) || voices[0] || null;
}

export function useAgentVoice(agentId: string | undefined) {
    const profile = agentId
        ? (VOICE_PROFILES[agentId] ?? DEFAULT_PROFILE)
        : DEFAULT_PROFILE;

    /** Speak text using the agent's voice profile */
    const speak = (text: string) => {
        if (window.speechSynthesis.speaking) {
            window.speechSynthesis.cancel();
        }

        // Strip markdown for cleaner TTS
        const plain = text
            // Remove markdown tables entirely
            .replace(/\|.*\|/g, ' ')
            // Remove image links, normal links
            .replace(/!\[([^\]]*)\]\([^)]+\)/g, '$1')
            .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
            // Remove HTML tags
            .replace(/<[^>]+>/g, '')
            // Remove Headers
            .replace(/#{1,6}\s+/g, '')
            // Remove Bold and Italic
            .replace(/\*\*(.*?)\*\*/g, '$1')
            .replace(/\*(.*?)\*/g, '$1')
            // Remove Inline Code
            .replace(/`{1,3}[^`]*`{1,3}/g, '')
            // Convert list bullets to commas for natural pause
            .replace(/^\s*[-*+]\s+/gm, ', ')
            // Convert Double newlines to periods
            .replace(/\n{2,}/g, '. ')
            // Convert exact symbols with words
            .replace(/&/g, ' and ')
            .replace(/\n/g, ' ')
            .trim();

        if (!plain) return;

        const utterance = new SpeechSynthesisUtterance(plain);
        utterance.rate = profile.rate;
        utterance.pitch = profile.pitch;
        utterance.volume = profile.volume;

        const voices = window.speechSynthesis.getVoices();
        if (voices.length > 0) {
            const voice = pickVoice(profile.preferredVoice);
            if (voice) utterance.voice = voice;
        }

        setTimeout(() => {
            window.speechSynthesis.speak(utterance);
        }, 50);

        return utterance;
    };

    /** Stop current speech */
    const stop = () => window.speechSynthesis.cancel();

    return { profile, speak, stop };
}
