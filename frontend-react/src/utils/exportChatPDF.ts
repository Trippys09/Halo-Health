/**
 * exportChatPDF — Opens a dedicated print window with a professional
 * medical report layout. Works without any PDF library.
 */

interface ExportMessage {
    role: 'user' | 'model' | 'assistant';
    content: string;
    timestamp?: string;
    image?: string;
}

interface ExportOptions {
    agentName: string;
    agentRole: string;
    messages: ExportMessage[];
    patientNote?: string;
}

function escapeHtml(str: string): string {
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function markdownToHtml(md: string): string {
    // 1. Convert Markdown tables FIRST before newlines are destroyed
    const tableRegex = /((?:\|.+\|\n?)+)/g;
    let html = md.replace(tableRegex, (match: string) => {
        const rows = match.trim().split('\n');
        const [header, separator, ...body] = rows;
        if (!separator || !separator.includes('|-')) return match;

        // Helper to remove leading and trailing pipes
        const clean = (r: string) => r.replace(/^\||\|$/g, '').trim();

        const ths = clean(header).split('|').map((c: string) => `<th>${c.trim()}</th>`).join('');
        const trs = body.map((row: string) => {
            const tds = clean(row).split('|').map((c: string) => `<td>${c.trim()}</td>`).join('');
            return `<tr>${tds}</tr>`;
        }).join('');

        return `<table class="md-table"><thead><tr>${ths}</tr></thead><tbody>${trs}</tbody></table>`;
    });

    // 2. Process typography and whitespace
    html = html
        .replace(/\*\*\*(.*?)\*\*\*/g, '<strong><em>$1</em></strong>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/^### (.+)$/gm, '<h3>$1</h3>')
        .replace(/^## (.+)$/gm, '<h2>$1</h2>')
        .replace(/^# (.+)$/gm, '<h1>$1</h1>')
        .replace(/^[-*+] (.+)$/gm, '<li>$1</li>')
        .replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n---\n/g, '<hr>')
        .replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<br><img src="$2" alt="$1" style="max-width: 100%; border-radius: 4pt; margin: 8pt 0; max-height: 250pt; object-fit: contain; border: 1pt solid #cbd5e1;" /><br>')
        .replace(/\n/g, '<br>');

    return html;
}

export function exportChatPDF(opts: ExportOptions): void {
    const { agentName, agentRole, messages } = opts;
    const printDate = new Date().toLocaleString('en-US', {
        year: 'numeric', month: 'long', day: 'numeric',
        hour: '2-digit', minute: '2-digit'
    });
    const reportId = `MDRPT-${Date.now().toString(36).toUpperCase()}`;

    // Find key content
    const conversation = messages.filter(m => m.content);
    const agentResponses = conversation.filter(m => m.role !== 'user');
    const lastImageMsg = [...messages].reverse().find(m => m.image);

    // Build conversation rows
    const conversationRows = conversation
        .filter(m => m.role !== 'model' || conversation.indexOf(m) > 0)
        .map(m => {
            const isUser = m.role === 'user';
            const sender = isUser ? 'Patient' : agentName;
            const ts = m.timestamp ? new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';
            const content = isUser ? escapeHtml(m.content) : markdownToHtml(m.content);
            return `
            <tr class="${isUser ? 'row-user' : 'row-agent'}">
                <td class="cell-sender"><strong>${escapeHtml(sender)}</strong>${ts ? `<br><span class="ts">${ts}</span>` : ''}</td>
                <td class="cell-content">${content}</td>
            </tr>`;
        }).join('');

    const html = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>HALO Health Clinical Report — ${agentName}</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        @page { size: A4; margin: 20mm 18mm 22mm 18mm; }

        body {
            font-family: 'Times New Roman', Times, serif;
            font-size: 11pt;
            color: #1a1a1a;
            background: white;
        }

        /* ── Header ── */
        .report-header {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            border-bottom: 2.5pt solid #0F52BA;
            padding-bottom: 10pt;
            margin-bottom: 14pt;
        }
        .brand-block { }
        .brand-name {
            font-family: Arial, sans-serif;
            font-size: 20pt;
            font-weight: 700;
            color: #0F52BA;
            letter-spacing: -0.5pt;
        }
        .brand-tagline {
            font-size: 8.5pt;
            color: #64748b;
            font-style: italic;
            margin-top: 2pt;
        }
        .report-meta {
            text-align: right;
            font-family: Arial, sans-serif;
            font-size: 8.5pt;
            color: #475569;
            line-height: 1.6;
        }
        .report-id {
            font-weight: 700;
            color: #0F52BA;
            font-size: 9pt;
        }

        /* ── Report Title Bar ── */
        .report-title-bar {
            background: #f0f4ff;
            border: 1pt solid #d1d9f0;
            border-left: 4pt solid #0F52BA;
            padding: 8pt 12pt;
            margin-bottom: 14pt;
            font-family: Arial, sans-serif;
        }
        .report-title-bar h1 {
            font-size: 13pt;
            font-weight: 700;
            color: #0F52BA;
            margin-bottom: 2pt;
        }
        .report-title-bar .subtitle {
            font-size: 9pt;
            color: #64748b;
        }

        /* ── Info Grid ── */
        .info-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0;
            border: 1pt solid #cbd5e1;
            margin-bottom: 16pt;
            font-family: Arial, sans-serif;
            font-size: 9pt;
        }
        .info-cell {
            padding: 6pt 10pt;
            border-right: 1pt solid #cbd5e1;
            border-bottom: 1pt solid #cbd5e1;
        }
        .info-cell:nth-child(even) { border-right: none; }
        .info-cell:nth-last-child(-n+2) { border-bottom: none; }
        .info-label {
            font-size: 7.5pt;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            color: #64748b;
            display: block;
            margin-bottom: 2pt;
        }
        .info-value {
            font-size: 9.5pt;
            color: #0f172a;
            font-weight: 500;
        }

        /* ── Section Headers ── */
        .section-header {
            font-family: Arial, sans-serif;
            font-size: 9pt;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #0F52BA;
            border-bottom: 1pt solid #0F52BA;
            padding-bottom: 3pt;
            margin: 14pt 0 8pt;
        }

        /* ── Scan Image ── */
        .scan-section {
            margin-bottom: 14pt;
            text-align: center;
        }
        .scan-section img {
            max-width: 65%;
            max-height: 220pt;
            object-fit: contain;
            border: 1pt solid #cbd5e1;
            border-radius: 3pt;
        }
        .scan-caption {
            font-size: 8pt;
            color: #64748b;
            margin-top: 4pt;
            font-style: italic;
        }

        /* ── Consultation Table ── */
        .consult-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 10pt;
            margin-bottom: 16pt;
        }
        .consult-table thead tr {
            background: #0F52BA;
            color: white;
        }
        .consult-table th {
            padding: 6pt 10pt;
            text-align: left;
            font-family: Arial, sans-serif;
            font-size: 9pt;
            font-weight: 600;
        }
        .consult-table td {
            padding: 7pt 10pt;
            vertical-align: top;
            border-bottom: 0.5pt solid #e2e8f0;
        }
        .row-user { background: #f8fafc; }
        .row-agent { background: white; }
        .cell-sender {
            width: 100pt;
            font-family: Arial, sans-serif;
            font-size: 9pt;
            color: #334155;
        }
        .cell-sender .ts {
            font-size: 7.5pt;
            color: #94a3b8;
        }
        .cell-content { line-height: 1.65; }
        .cell-content h2, .cell-content h3 {
            font-family: Arial, sans-serif;
            font-size: 10pt;
            font-weight: 700;
            margin: 8pt 0 4pt;
            color: #0f172a;
        }
        .cell-content ul {
            padding-left: 16pt;
            margin: 4pt 0;
        }
        .cell-content li { margin-bottom: 2pt; }
        .cell-content strong { font-weight: 700; }
        .cell-content em { font-style: italic; }
        .cell-content code {
            background: #f1f5f9;
            padding: 1pt 4pt;
            border-radius: 2pt;
            font-family: 'Courier New', monospace;
            font-size: 9pt;
        }
        .cell-content hr {
            border: none;
            border-top: 0.5pt solid #e2e8f0;
            margin: 8pt 0;
        }
        .cell-content p {
            margin-bottom: 6pt;
        }

        /* ── Markdown Tables in Chat ── */
        .md-table {
            width: 100%;
            border-collapse: collapse;
            margin: 8pt 0;
            font-family: Arial, sans-serif;
            font-size: 8.5pt;
        }
        .md-table th {
            background: #f1f5f9;
            padding: 4pt 6pt;
            text-align: left;
            border: 1pt solid #cbd5e1;
            font-weight: 700;
        }
        .md-table td {
            padding: 4pt 6pt;
            border: 1pt solid #cbd5e1;
        }

        /* ── Disclaimer Box ── */
        .disclaimer-box {
            border: 1pt solid #fed7aa;
            background: #fff7ed;
            padding: 8pt 12pt;
            border-radius: 2pt;
            font-family: Arial, sans-serif;
            font-size: 8.5pt;
            color: #92400e;
            margin-bottom: 14pt;
            line-height: 1.5;
        }
        .disclaimer-box strong { font-weight: 700; }

        /* ── Footer ── */
        .report-footer {
            border-top: 1pt solid #cbd5e1;
            padding-top: 8pt;
            display: flex;
            justify-content: space-between;
            font-family: Arial, sans-serif;
            font-size: 7.5pt;
            color: #94a3b8;
        }
    </style>
</head>
<body>

    <!-- Header -->
    <div class="report-header">
        <div class="brand-block">
            <div class="brand-name">HALO Health</div>
            <div class="brand-tagline">Clinical Intelligence Platform — Georgia State University</div>
        </div>
        <div class="report-meta">
            <div class="report-id">${reportId}</div>
            <div>Date: ${printDate}</div>
            <div>Agent: ${escapeHtml(agentName)} (${escapeHtml(agentRole)})</div>
            <div>Status: Preliminary / For Review</div>
        </div>
    </div>

    <!-- Title Bar -->
    <div class="report-title-bar">
        <h1>${escapeHtml(agentName)} Clinical Consultation Report</h1>
        <div class="subtitle">Generated automatically from live consultation session · Not for sole diagnostic use</div>
    </div>

    <!-- Info Grid -->
    <div class="info-grid">
        <div class="info-cell"><span class="info-label">Report ID</span><span class="info-value">${reportId}</span></div>
        <div class="info-cell"><span class="info-label">Report Date</span><span class="info-value">${printDate}</span></div>
        <div class="info-cell"><span class="info-label">Agent System</span><span class="info-value">${escapeHtml(agentName)}</span></div>
        <div className="info-cell"><span class="info-label">Clinical Role</span><span class="info-value">${escapeHtml(agentRole)}</span></div>
        <div class="info-cell"><span class="info-label">AI Model</span><span class="info-value">Google Gemini 3 Family</span></div>
        <div class="info-cell"><span class="info-label">Total Exchanges</span><span class="info-value">${agentResponses.length} agent response${agentResponses.length !== 1 ? 's' : ''}</span></div>
    </div>

    ${lastImageMsg?.image ? `
    <!-- Medical Scan -->
    <div class="section-header">Submitted Medical Imaging</div>
    <div class="scan-section">
        <img src="${lastImageMsg.image}" alt="Medical scan" />
        <div class="scan-caption">Patient-submitted scan. Resolution and format as uploaded.</div>
    </div>
    ` : ''}

    <!-- Consultation Transcript -->
    <div class="section-header">Consultation Transcript</div>
    <table class="consult-table">
        <thead>
            <tr>
                <th style="width:100pt">Participant</th>
                <th>Exchange</th>
            </tr>
        </thead>
        <tbody>
            ${conversationRows}
        </tbody>
    </table>

    <!-- Disclaimer -->
    <div class="disclaimer-box">
        <strong>Important Notice:</strong> This report contains AI-generated clinical guidance from HALO Health.
        Content is preliminary and informational only. It does not constitute a formal medical diagnosis,
        prescription, or legal medical advice. All recommendations must be reviewed and verified by a licensed
        physician, pharmacist, or qualified healthcare professional before clinical use.
    </div>

    <!-- Footer -->
    <div class="report-footer">
        <span>HALO Health Clinical Intelligence Platform — Georgia State University</span>
        <span>${reportId} · ${printDate}</span>
    </div>

</body>
</html>`;

    const win = window.open('', '_blank', 'width=900,height=700,scrollbars=yes');
    if (!win) {
        alert('Please allow popups for this site to export the PDF report.');
        return;
    }
    win.document.write(html);
    win.document.close();
    // Give images time to load then trigger print
    setTimeout(() => {
        win.focus();
        win.print();
    }, 800);
}
