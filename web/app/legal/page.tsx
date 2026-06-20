"use client";

import { useState, useRef, useEffect } from "react";
import { ragChat } from "@/lib/api";

interface Message {
  role: "user" | "bot";
  content: string;
  sections?: {
    section: string;
    title: string;
    fine: number;
    score: number;
  }[];
}

const SUGGESTIONS = [
  "What is the penalty for not wearing a helmet?",
  "What is the fine for triple riding?",
  "Is riding without helmet compoundable?",
  "What does Section 194D say?",
  "What are the penalties under MV Act for dangerous driving?",
  "Can you explain Section 194C?",
];

export default function LegalPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "bot",
      content:
        "Hello! I'm the **MV Act Legal Assistant**. I can answer questions about the Motor Vehicles Act 1988 (as amended by the 2019 Amendment).\n\nAsk me about any traffic violation — helmet, triple riding, speeding, drunk driving, and more. My answers are grounded in the actual legal text using RAG retrieval from the Act.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEnd = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (text?: string) => {
    const msg = text || input.trim();
    if (!msg || loading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: msg }]);
    setLoading(true);

    try {
      const data = await ragChat(msg);
      setMessages((prev) => [
        ...prev,
        {
          role: "bot",
          content: data.answer || "I could not find relevant information.",
          sections: data.sections,
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "bot",
          content: "⚠️ Failed to connect to the backend. Make sure it's running on port 8000.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="page-container">
      <div className="page-header animate-in">
        <h1><span className="gradient-text">Legal AI Assistant</span></h1>
        <p>Ask questions about the Motor Vehicles Act 1988 — powered by RAG retrieval.</p>
      </div>

      <div className="glass-strong animate-in animate-in-delay-1 chat-container" style={{ borderRadius: "var(--radius-lg)" }}>
        {/* Messages */}
        <div className="chat-messages">
          {messages.map((m, i) => (
            <div key={i} className={`chat-bubble ${m.role}`}>
              <div style={{ whiteSpace: "pre-wrap" }}>{m.content}</div>

              {/* Retrieved sections */}
              {m.sections && m.sections.length > 0 && (
                <div style={{ marginTop: 12, paddingTop: 12, borderTop: "1px solid rgba(255,255,255,0.1)" }}>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: 8 }}>
                    📚 Retrieved Sections (relevance score)
                  </div>
                  {m.sections.map((s, j) => (
                    <div key={j} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "4px 0" }}>
                      <span style={{ fontSize: "0.8rem" }}>
                        <span className="badge badge-info" style={{ marginRight: 6 }}>§{s.section}</span>
                        {s.title}
                      </span>
                      <span className="mono" style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                        {(s.score * 100).toFixed(0)}%
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="chat-bubble bot" style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <div className="spinner" />
              <span style={{ color: "var(--text-muted)" }}>Searching MV Act...</span>
            </div>
          )}
          <div ref={messagesEnd} />
        </div>

        {/* Suggestions (show if no user messages yet) */}
        {messages.length <= 1 && (
          <div style={{ padding: "0 24px 12px", display: "flex", flexWrap: "wrap", gap: 8 }}>
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                className="btn btn-ghost btn-sm"
                onClick={() => handleSend(s)}
                style={{ fontSize: "0.78rem" }}
              >
                {s}
              </button>
            ))}
          </div>
        )}

        {/* Input */}
        <div className="chat-input-row">
          <input
            className="input"
            placeholder="Ask about any traffic violation or MV Act section..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
          />
          <button className="btn btn-primary" onClick={() => handleSend()} disabled={loading || !input.trim()}>
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
