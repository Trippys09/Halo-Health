export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiClient {
    private getToken(): string | null {
        return localStorage.getItem('access_token');
    }

    private async fetchAPI(endpoint: string, options: RequestInit = {}) {
        const headers: Record<string, string> = {
            ...(options.headers as Record<string, string>),
        };

        if (!(options.body instanceof FormData)) {
            headers['Content-Type'] = 'application/json';
        }

        const token = this.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers,
        });

        if (response.status === 401) {
            // Auto-logout on 401
            localStorage.removeItem('access_token');
            // Dispatch custom event to let app know
            window.dispatchEvent(new Event('auth-unauthorized'));
        }

        if (!response.ok) {
            let errData;
            try {
                errData = await response.json();
            } catch {
                throw new Error(`HTTP ${response.status} - ${response.statusText}`);
            }
            throw new Error(errData?.detail || `HTTP ${response.status} - ${response.statusText}`);
        }

        return response.json();
    }

    // Auth Methods
    async login(email: string, password: string) {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ email, password }),
        });
        if (!response.ok) {
            let errData;
            try { errData = await response.json(); } catch { throw new Error("Login failed"); }
            throw new Error(errData?.detail || "Login failed");
        }
        return response.json();
    }

    async register(email: string, password: string, fullName: string) {
        return this.fetchAPI('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ email, password, full_name: fullName }),
        });
    }

    async getMe() {
        return this.fetchAPI('/auth/me', {
            method: 'GET',
        });
    }

    // Chat & Sessions
    async startSession(agentName: string) {
        return this.fetchAPI('/sessions', {
            method: 'POST',
            body: JSON.stringify({ agent_type: agentName }),
        });
    }

    async getSessions() {
        return this.fetchAPI('/sessions', {
            method: 'GET',
        });
    }

    async getMessages(sessionId: string) {
        return this.fetchAPI(`/sessions/${sessionId}/messages`, {
            method: 'GET',
        });
    }

    async deleteSession(sessionId: string | number) {
        return this.fetchAPI(`/sessions/${sessionId}`, {
            method: 'DELETE',
        });
    }

    async renameSession(sessionId: string | number, newTitle: string) {
        return this.fetchAPI(`/sessions/${sessionId}`, {
            method: 'PUT',
            body: JSON.stringify({ title: newTitle }),
        });
    }

    async chatWithAgent(agent: string, message: string, sessionId?: string | number, imageBase64?: string) {
        const body: any = { message };
        if (sessionId) {
            body.session_id = sessionId;
        }
        if (imageBase64) {
            body.image_base64 = imageBase64;
        }
        const agentPath = agent.replace(/-/g, "_"); // Globally replace hyphens just in case
        return this.fetchAPI(`/agents/${agentPath}/chat`, {
            method: 'POST',
            body: JSON.stringify(body),
        });
    }

    // Audit Methods
    async getAuditStats() {
        return this.fetchAPI('/audit/stats', {
            method: 'GET',
        });
    }

    async getAuditActivity(agentType: string = 'all', limit: number = 50) {
        return this.fetchAPI(`/audit/activity?agent_type=${agentType}&limit=${limit}`, {
            method: 'GET',
        });
    }

    async getAuditSystem() {
        return this.fetchAPI('/audit/system', {
            method: 'GET',
        });
    }

    // Share
    async sendEmail(payload: { to: string; subject: string; body: string; agent_name?: string; include_pdf?: boolean }) {
        return this.fetchAPI('/share/email', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
    }

    async sendWhatsApp(payload: { phone_number: string; message: string; agent_name?: string; include_pdf?: boolean }) {
        return this.fetchAPI('/share/whatsapp', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
    }
}

export const api_client = new ApiClient();
