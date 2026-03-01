import React, { useState } from 'react';
import { Loader2, MessageSquare, Send, X, Check, Eye, Edit2 } from 'lucide-react';

const API_BASE = "https://emily-portfolio-copilot.onrender.com";

export default function Copilot() {
    const [token, setToken] = useState(localStorage.getItem('copilot_token'));
    const [isOpen, setIsOpen] = useState(false);
    const [showLogin, setShowLogin] = useState(false);
    const [password, setPassword] = useState('');

    const [prompt, setPrompt] = useState('');
    const [loading, setLoading] = useState(false);
    const [statusText, setStatusText] = useState('');
    const [previewUrl, setPreviewUrl] = useState(null);

    // Expose this so App.jsx footer can trigger it
    React.useEffect(() => {
        window.openCopilotLogin = () => {
            if (!token) setShowLogin(true);
            else setIsOpen(true);
        };
    }, [token]);

    const handleLogin = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE}/api/auth`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ password })
            });
            if (res.ok) {
                const data = await res.json();
                setToken(data.token);
                localStorage.setItem('copilot_token', data.token);
                setShowLogin(false);
                setIsOpen(true);
            } else {
                alert("Invalid Admin Password");
            }
        } catch (err) {
            alert("Auth Error: " + err.message);
        }
        setLoading(false);
    };

    const handlePreview = async (e) => {
        e.preventDefault();
        if (!prompt) return;
        setLoading(true);
        setStatusText('Architecting Changes...');
        setPreviewUrl(null);
        try {
            const res = await fetch(`${API_BASE}/api/preview`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ prompt })
            });

            if (res.status === 401) {
                localStorage.removeItem('copilot_token');
                setToken(null);
                setShowLogin(true);
                setLoading(false);
                setStatusText('');
                return;
            }
            if (!res.ok) {
                throw new Error(`Server returned ${res.status}`);
            }

            // Stream the responses 
            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let done = false;

            while (!done) {
                const { value, done: readerDone } = await reader.read();
                done = readerDone;
                if (value) {
                    const chunk = decoder.decode(value, { stream: true });
                    const messages = chunk.split('\n\n');
                    for (const msg of messages) {
                        if (msg.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(msg.slice(6));
                                if (data.error) throw new Error(data.error);
                                if (data.status) setStatusText(data.status);
                                if (data.previewUrl) {
                                    setPreviewUrl(`${API_BASE}${data.previewUrl}?t=${Date.now()}`);
                                    setIsOpen(false);
                                }
                            } catch (err) {
                                if (err.message.includes("Gemini Error") || err.message.includes("Webpack")) {
                                    throw err;
                                }
                                // ignore partial JSON parses mid-stream
                            }
                        }
                    }
                }
            }
        } catch (err) {
            alert("Request Error: " + err.message);
        }
        setLoading(false);
        setStatusText('');
    };

    const handleAction = async (endpoint) => {
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE}/api/${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                }
            });
            if (res.status === 401) {
                localStorage.removeItem('copilot_token');
                setToken(null);
                setShowLogin(true);
                return;
            }
            if (res.ok) {
                setPreviewUrl(null);
                setPrompt('');
                if (endpoint === 'publish') {
                    alert("Success! Changes published to GitHub.");
                }
            } else {
                alert(`Failed to ${endpoint}`);
            }
        } catch (err) {
            alert(`Error during ${endpoint}: ` + err.message);
        }
        setLoading(false);
    };

    if (!token && !showLogin) return null;

    return (
        <>
            {/* Login Modal */}
            {showLogin && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center bg-charcoal/80 backdrop-blur-sm">
                    <form onSubmit={handleLogin} className="bg-moss p-8 rounded-[2rem] shadow-2xl w-full max-w-sm relative">
                        <button type="button" onClick={() => setShowLogin(false)} className="absolute top-6 right-6 text-cream/50 hover:text-cream">
                            <X size={20} />
                        </button>
                        <h3 className="font-serif italic text-3xl text-cream mb-6">Admin Access</h3>
                        <input
                            type="password"
                            value={password}
                            onChange={e => setPassword(e.target.value)}
                            placeholder="Enter password..."
                            className="w-full bg-cream/10 border border-cream/20 rounded-xl px-4 py-3 text-cream mb-6 outline-none focus:border-clay transition-colors"
                            autoFocus
                        />
                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full bg-clay text-cream font-bold rounded-xl py-3 flex justify-center items-center hover:bg-clay/90 transition-colors disabled:opacity-50"
                        >
                            {loading ? <Loader2 size={20} className="animate-spin" /> : "Authenticate"}
                        </button>
                    </form>
                </div>
            )}


            {/* Copilot Drawer */}
            <div className={`fixed right-0 top-0 bottom-0 w-full max-w-md bg-moss/95 backdrop-blur-xl border-l border-cream/10 z-[100] transform transition-transform duration-500 ease-[cubic-bezier(0.16,1,0.3,1)] ${isOpen ? 'translate-x-0' : 'translate-x-full'}`}>
                <div className="flex flex-col h-full p-8 text-cream">
                    <div className="flex justify-between items-center mb-8 border-b border-cream/10 pb-6">
                        <h3 className="font-serif italic text-3xl">On-Page Copilot</h3>
                        <button onClick={() => setIsOpen(false)} className="text-cream/50 hover:text-cream">
                            <X size={24} />
                        </button>
                    </div>

                    <div className="flex-1 overflow-y-auto">
                        <p className="font-mono text-sm text-cream/70 mb-8 leading-relaxed">
                            Describe the UI, text, or layout changes you want to apply to the portfolio.
                            The AI will architect the change and generate a live preview.
                        </p>

                        <form onSubmit={handlePreview} className="relative">
                            <textarea
                                value={prompt}
                                onChange={e => setPrompt(e.target.value)}
                                placeholder="e.g. Change the hero text to say..."
                                className={`w-full bg-cream/5 border ${loading ? 'border-clay' : 'border-cream/20'} rounded-2xl p-4 min-h-[160px] text-cream outline-none focus:border-clay transition-colors resize-none mb-4`}
                                disabled={loading}
                            />
                            <button
                                type="submit"
                                disabled={loading || !prompt.trim()}
                                className="absolute bottom-10 right-4 bg-clay p-2 rounded-xl text-cream disabled:opacity-50 hover:bg-clay/90 transition-colors"
                                style={{ cursor: loading && !prompt.trim() ? "not-allowed" : "pointer" }}
                            >
                                {loading ? <Loader2 size={20} className="animate-spin" /> : <Send size={20} />}
                            </button>

                            {loading && statusText && (
                                <div className="flex flex-col gap-2 mt-2 px-2">
                                    <span className="font-mono text-xs text-clay uppercase tracking-widest">{statusText}</span>
                                    <div className="h-1 w-full bg-cream/10 rounded overflow-hidden">
                                        <div className="h-full bg-clay animate-pulse w-full"></div>
                                    </div>
                                </div>
                            )}
                        </form>
                    </div>
                </div>
            </div>

            {/* Full Screen Live Preview Iframe */}
            {previewUrl && (
                <div className="fixed inset-0 z-[200] bg-charcoal flex flex-col">
                    {/* Top Control Bar */}
                    <div className="h-16 bg-moss border-b border-cream/10 px-8 flex justify-between items-center shrink-0">
                        <div className="flex items-center gap-4 text-cream">
                            <Eye size={20} className="text-clay animate-pulse" />
                            <span className="font-mono text-sm uppercase tracking-widest text-cream/70">Live Preview Mode</span>
                        </div>

                        <div className="flex gap-4">
                            <button
                                onClick={() => handleAction('revert')}
                                disabled={loading}
                                className="flex items-center gap-2 px-4 py-2 rounded-full border border-cream/20 text-cream/70 hover:text-cream hover:bg-cream/10 transition-colors disabled:opacity-50"
                            >
                                <X size={16} /> Discard
                            </button>
                            <button
                                onClick={() => { setPreviewUrl(null); setIsOpen(true); }}
                                disabled={loading}
                                className="flex items-center gap-2 px-4 py-2 rounded-full border border-clay/50 text-clay hover:text-cream hover:bg-clay/20 transition-colors disabled:opacity-50"
                            >
                                <Edit2 size={16} /> Refine
                            </button>
                            <button
                                onClick={() => handleAction('publish')}
                                disabled={loading}
                                className="flex items-center gap-2 px-5 py-2 rounded-full bg-clay text-cream font-bold hover:bg-clay/90 transition-colors disabled:opacity-50"
                            >
                                {loading ? <Loader2 size={16} className="animate-spin" /> : <Check size={16} />}
                                Approve & Publish
                            </button>
                        </div>
                    </div>

                    {/* Iframe Frame */}
                    <div className="flex-1 w-full bg-white relative">
                        {loading && (
                            <div className="absolute inset-0 bg-charcoal/50 flex items-center justify-center z-10 backdrop-blur-sm">
                                <Loader2 size={48} className="animate-spin text-clay" />
                            </div>
                        )}
                        <iframe
                            src={previewUrl}
                            className="w-full h-full border-none"
                            title="Live Preview"
                        />
                    </div>
                </div>
            )}

            {/* Global loading overlay for initial generation */}
            {loading && !previewUrl && !isOpen && (
                <div className="fixed inset-0 z-[300] bg-charcoal/80 backdrop-blur-md flex flex-col items-center justify-center text-cream">
                    <Loader2 size={64} className="animate-spin text-clay mb-6" />
                    <p className="font-serif italic text-2xl animate-pulse">Architecting Changes...</p>
                </div>
            )}
        </>
    );
}
