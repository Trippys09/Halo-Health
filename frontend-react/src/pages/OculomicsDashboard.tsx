import React, { useState, useEffect } from 'react';
import Markdown from 'markdown-to-jsx';
import {
    Eye, Upload, Loader2, FileText, Activity,
    CheckCircle2, AlertCircle, Share2, Download, X, Trash2
} from 'lucide-react';
import { api_client, API_BASE_URL } from '../utils/api_client';
import ShareModal from '../components/ShareModal';
import { exportChatPDF } from '../utils/exportChatPDF';
import './OculomicsDashboard.css';

const OculomicsDashboard: React.FC = () => {
    const [loading, setLoading] = useState(false);
    const [outcomes, setOutcomes] = useState<Record<string, any>>({});
    const [report, setReport] = useState<string>('');
    const [selectedImage, setSelectedImage] = useState<string | null>(null);
    const [sessionId, setSessionId] = useState<number | null>(null);
    const [showShareModal, setShowShareModal] = useState(false);
    const [selectedMapUrl, setSelectedMapUrl] = useState<string | null>(null);
    const [selectedMapTask, setSelectedMapTask] = useState<string>('');
    const [pendingImageBase64, setPendingImageBase64] = useState<string | null>(null);
    const [sessionReady, setSessionReady] = useState(false);

    useEffect(() => {
        const setup = async () => {
            try {
                const sessions = await api_client.getSessions();
                const ocuSessions = sessions.filter((s: any) => s.agent_type === 'oculomics');

                if (ocuSessions.length > 0) {
                    const latest = ocuSessions[0];
                    setSessionId(latest.id);
                    const messages = await api_client.getMessages(latest.id);

                    if (messages.length > 0) {
                        // 1. Restore Clinical Report
                        const lastAssistant = [...messages].reverse().find(m => m.role === 'assistant');
                        if (lastAssistant) {
                            setReport(lastAssistant.content);
                        }

                        // 2. Restore Patient Scan (Image)
                        const lastUserWithImage = [...messages].reverse().find(m => m.role === 'user' && m.image_data);
                        if (lastUserWithImage && lastUserWithImage.image_data) {
                            const imgData = lastUserWithImage.image_data;
                            setSelectedImage(imgData.startsWith('data:') ? imgData : `data:image/jpeg;base64,${imgData}`);
                        }

                        // 3. Restore Predictive Outcomes (from local storage cache)
                        const cachedOutcomes = localStorage.getItem(`oculomics_outcomes_${latest.id}`);
                        if (cachedOutcomes) {
                            try {
                                setOutcomes(JSON.parse(cachedOutcomes));
                            } catch (e) {
                                console.error("Failed to parse cached outcomes");
                            }
                        }
                    }
                } else {
                    const newSess = await api_client.startSession('oculomics');
                    setSessionId(newSess.session_id);
                }
                setSessionReady(true);
            } catch (err) {
                console.error("Failed to setup Oculomics session:", err);
            }
        };
        setup();
    }, []);

    // Process pending image once session is ready
    useEffect(() => {
        if (sessionReady && sessionId && pendingImageBase64) {
            runAnalysis(pendingImageBase64);
            setPendingImageBase64(null);
        }
    }, [sessionReady, sessionId, pendingImageBase64]);

    const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = async () => {
            const result = reader.result as string;
            const base64 = result.split(',')[1];
            setSelectedImage(result);

            // If session is ready, analyze immediately; otherwise queue it
            if (sessionReady && sessionId) {
                runAnalysis(base64);
            } else {
                setPendingImageBase64(base64);
                setLoading(true); // Show loading state while waiting for session
            }
        };
        reader.readAsDataURL(file);
    };

    const handleReset = async () => {
        setLoading(true);
        setSelectedImage(null);
        setReport('');
        setOutcomes({});
        setPendingImageBase64(null);
        try {
            const newSess = await api_client.startSession('oculomics');
            setSessionId(newSess.session_id);
        } catch (err) {
            console.error("Failed to reset session:", err);
            window.dispatchEvent(new CustomEvent('SHOW_NOTIFICATION', {
                detail: { message: `Failed to open new patient session.`, type: 'error' }
            }));
        } finally {
            setLoading(false);
        }
    };

    const runAnalysis = async (imageBase64: string) => {
        if (!sessionId) return;
        setLoading(true);
        setOutcomes({});
        setReport('');

        try {
            const data = await api_client.chatWithAgent('oculomics', "Analyze this retinal scan for all biomarkers.", sessionId, imageBase64);
            setReport(data.reply);

            if (data.outcomes) {
                setOutcomes(data.outcomes);
                // Cache outcomes so they persist on page reload/navigation
                localStorage.setItem(`oculomics_outcomes_${sessionId}`, JSON.stringify(data.outcomes));
            }
        } catch (err) {
            console.error("Analysis failed:", err);
        } finally {
            setLoading(false);
        }
    };

    // Formats the context for the PDF Export (Includes the image file)
    const handleExportContext = () => {
        let fullReport = report;
        const gradcamTasks = Object.entries(outcomes).filter(([_, v]) => (v as any)?.gradcam_heatmap_url);
        if (gradcamTasks.length > 0) {
            fullReport += "\n\n### GradCAM++ Attention Maps\n\n";
            gradcamTasks.forEach(([task, data]: [string, any]) => {
                fullReport += `**${task}**\n![${task} GradCAM](${API_BASE_URL}${data.gradcam_heatmap_url})\n\n`;
            });
        }

        return [
            { role: 'user' as const, content: 'Analyze this retinal scan for all biomarkers.', image: selectedImage || undefined },
            { role: 'assistant' as const, content: fullReport }
        ];
    };

    const handleDownloadPdf = () => {
        if (!report) return;
        exportChatPDF({
            agentName: 'Oculomics AI',
            agentRole: 'Retina Engine',
            messages: handleExportContext()
        });
    };

    // Formats the text for the Share Modal email body
    const buildChatText = () => {
        if (!report) return "";
        let text = `[You]: Analyze this retinal scan for all biomarkers.\n\n`;
        text += `[Oculomics AI]: ${report.replace(/\*\*/g, '').replace(/#{1,6}\s/g, '')}`;
        return text;
    };

    return (
        <div className="oculomics-dashboard animate-fade-in">
            <header className="ocu-header">
                <div className="ocu-title">
                    <div className="ocu-icon"><Eye size={24} /></div>
                    <div>
                        <h1>Oculomics Predictive Dashboard</h1>
                        <p>AI-Powered Retinal Biomarker Analysis</p>
                    </div>
                </div>
                <div className="ocu-actions" style={{ display: 'flex', gap: '10px' }}>
                    <button className="ocu-upload-btn" onClick={handleReset} style={{ background: 'transparent', border: '1px solid var(--border-color)', color: 'white' }}>
                        <Trash2 size={18} />
                        <span>Discard</span>
                    </button>
                    {/* File upload has been moved to the Patient Scan section */}
                </div>
            </header>

            <div className="ocu-content-grid">
                <div className="ocu-top-row">
                    <section className="ocu-scan-preview glass-card">
                        <div className="card-header">
                            <h2><Activity size={18} /> Patient Scan</h2>
                        </div>
                        <label className="scan-placeholder" style={{ cursor: 'pointer', display: 'block' }}>
                            <input type="file" hidden accept="image/*" onChange={handleImageUpload} />
                            {selectedImage ? (
                                <img src={selectedImage} alt="Retinal Scan" className="img-fit" />
                            ) : (
                                <div className="empty-scan">
                                    <Upload size={40} />
                                    <p>Click to select or upload a fundus image to begin analysis.</p>
                                </div>
                            )}
                        </label>
                    </section>

                    <section className="ocu-outcomes glass-card">
                        <div className="card-header">
                            <h2><CheckCircle2 size={18} /> Predictive Outcomes</h2>
                            {loading && <div className="header-loader"><Loader2 size={16} className="animate-spin" /> <span>Analyzing...</span></div>}
                        </div>
                        <div className="outcomes-grid">
                            {[
                                { task: 'Diabetes', key: 'Diabetes' },
                                { task: 'Nephropathy', key: 'Nephropathy' },
                                { task: 'Edema', key: 'Edema' },
                                { task: 'Neuropathy', key: 'Neuropathy' },
                                { task: 'AMI Risk', key: 'AMI' },
                                { task: 'Cardio Risk', key: 'Cardiovascular_Risk' },
                                { task: 'ICDR', key: 'ICDR' },
                                { task: 'Hypertension', key: 'Hypertension' },
                                { task: 'Gender', key: 'Gender' },
                                { task: 'Age', key: 'Age' }
                            ].map(item => {
                                const data = outcomes[item.key];
                                return (
                                    <div key={item.key} className="outcome-item">
                                        <div className="outcome-info">
                                            <span className="outcome-name">{item.task}</span>
                                            {data?.probability !== null && data?.probability !== undefined && !loading && (
                                                <span className="outcome-prob">{Math.round(data.probability * 100)}% conf</span>
                                            )}
                                        </div>
                                        <span className={`outcome-value ${data ? 'has-data' : ''} ${loading ? 'is-loading' : ''}`}>
                                            {loading ? (
                                                <Loader2 size={18} className="animate-spin" style={{ color: 'var(--primary)' }} />
                                            ) : (
                                                data?.prediction !== undefined && data?.prediction !== null
                                                    ? (item.key === 'Age'
                                                        ? data.prediction
                                                        : item.key === 'Gender'
                                                            ? (data.prediction === 1 ? 'Female' : 'Male')
                                                            : (data.prediction === 1 ? 'Positive' : 'Negative'))
                                                    : '--'
                                            )}
                                        </span>
                                    </div>
                                );
                            })}
                        </div>
                    </section>
                </div>

                <div className="ocu-report-row">
                    <section className="ocu-report glass-card">
                        <div className="card-header">
                            <h2><FileText size={18} /> Clinical AI Report</h2>
                            {loading && <Loader2 size={16} className="animate-spin ocu-header-spin" />}

                            {/* Export & Share Mechanisms */}
                            <div className="report-actions">
                                <button
                                    className="chat-action-btn"
                                    title="Download Clinical Report as PDF"
                                    onClick={handleDownloadPdf}
                                    disabled={loading || !report}
                                >
                                    <FileText size={16} />
                                    <span>Export PDF</span>
                                </button>
                                <button
                                    className="chat-action-btn"
                                    title="Share conversation"
                                    onClick={() => setShowShareModal(true)}
                                    disabled={loading || !report}
                                >
                                    <Share2 size={16} />
                                    <span>Share</span>
                                </button>
                            </div>
                        </div>
                        <div className="report-body">
                            {loading ? (
                                <div className="report-loading">
                                    <Loader2 size={30} className="animate-spin" style={{ color: 'var(--primary)' }} />
                                    <p>PRISM is analyzing scan data...</p>
                                </div>
                            ) : report ? (
                                <>
                                    <Markdown className="markdown-content">
                                        {report.replace(/!\[.*?\]\(.*?\)/g, '')}
                                    </Markdown>
                                    {Object.entries(outcomes).filter(([_, v]) => (v as any)?.gradcam_heatmap_url).length > 0 && (
                                        <div className="gradcam-maps-container" style={{ marginTop: '2rem' }}>
                                            <h3 style={{ borderBottom: '1px solid #ddd', paddingBottom: '0.5rem', marginBottom: '1rem' }}>GradCAM++ Attention Maps</h3>
                                            <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) minmax(0, 1fr)', gap: '1rem' }}>
                                                {Object.entries(outcomes).map(([task, data]: [string, any]) => {
                                                    if (!data?.gradcam_heatmap_url) return null;
                                                    return (
                                                        <div
                                                            key={task}
                                                            className="gradcam-item"
                                                            style={{ textAlign: 'center', cursor: 'pointer', position: 'relative' }}
                                                            onClick={() => {
                                                                setSelectedMapUrl(`${API_BASE_URL}${data.gradcam_heatmap_url}`);
                                                                setSelectedMapTask(task);
                                                            }}
                                                        >
                                                            <div className="gradcam-overlay-hover">
                                                                <span className="expand-icon"><Download size={20} /> View & Export</span>
                                                            </div>
                                                            <img src={`${API_BASE_URL}${data.gradcam_heatmap_url}`} alt={`${task} GradCAM`} style={{ width: '100%', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)' }} />
                                                            <p style={{ marginTop: '0.5rem', fontSize: '0.85rem', fontWeight: '500' }}>{task}</p>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        </div>
                                    )}

                                    {/* GradCAM Map Modal */}
                                    {selectedMapUrl && (
                                        <div className="gradcam-modal" onClick={() => setSelectedMapUrl(null)}>
                                            <div className="gradcam-modal-content" onClick={e => e.stopPropagation()}>
                                                <div className="gradcam-modal-header">
                                                    <h3>{selectedMapTask} - GradCAM++ Attention Map</h3>
                                                    <button className="chat-action-btn" onClick={() => setSelectedMapUrl(null)} style={{ padding: '6px' }}><X size={20} /></button>
                                                </div>
                                                <img src={selectedMapUrl} alt="Attention Map Large" />
                                                <div className="gradcam-modal-footer">
                                                    <button
                                                        className="btn-export"
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            const a = document.createElement('a');
                                                            a.href = selectedMapUrl;
                                                            a.download = `${selectedMapTask.replace(/\s+/g, '_')}_GradCAM.png`;
                                                            document.body.appendChild(a);
                                                            a.click();
                                                            document.body.removeChild(a);
                                                        }}
                                                    >
                                                        <Download size={16} /> Export Map
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </>
                            ) : (
                                <div className="empty-report">
                                    <AlertCircle size={30} />
                                    <p>Comprehensive report will appear here after analysis.</p>
                                </div>
                            )}
                        </div>
                    </section>
                </div>
            </div>

            {showShareModal && (
                <ShareModal
                    agentName="Oculomics AI"
                    agentRole="Retina Engine"
                    chatText={buildChatText()}
                    onClose={() => setShowShareModal(false)}
                    onExportPDF={handleDownloadPdf}
                />
            )}
        </div>
    );
};

export default OculomicsDashboard;