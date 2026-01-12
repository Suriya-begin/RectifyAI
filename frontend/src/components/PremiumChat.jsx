import React, { useEffect, useRef, useState } from "react";
import "./premium-chat.css";

// tiny helper for timestamps
const nowTime = () =>
  new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

// Simulated streaming: yields text chunk by chunk
async function streamSimulatedReply(text, onChunk, delay = 20) {
  for (let i = 1; i <= text.length; i++) {
    onChunk(text.slice(0, i));
    await new Promise((r) => setTimeout(r, delay));
  }
}

export default function PremiumChat({
  botName = "Aura",
  botAvatar = "https://i.ibb.co/6W4kTqZ/bot.png",
  userAvatar = "https://i.ibb.co/9gtb8Cp/user.png",
  storageKey = "premium_chat_history_v1",
}) {
  // UI state
  const [open, setOpen] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("premium_chat_open")) ?? true;
    } catch {
      return true;
    }
  });
  const [dark, setDark] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("premium_chat_dark")) ?? false;
    } catch {
      return false;
    }
  });

  // chat state
  const [messages, setMessages] = useState(() => {
    try {
      const raw = localStorage.getItem(storageKey);
      return raw ? JSON.parse(raw) : [
        { id: 1, from: "bot", text: `Hi! I'm ${botName}. Ask me anything.`, time: nowTime() },
      ];
    } catch {
      return [{ id: 1, from: "bot", text: `Hi! I'm ${botName}. Ask me anything.`, time: nowTime() }];
    }
  });

  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [suggestions] = useState([
    "What can you do?",
    "Give me 3 tips to improve productivity",
    "Explain closures in JavaScript",
  ]);

  const containerRef = useRef(null);
  const textAreaRef = useRef(null);
  const idRef = useRef(1000);

  // persist open/dark state
  useEffect(() => localStorage.setItem("premium_chat_open", JSON.stringify(open)), [open]);
  useEffect(() => localStorage.setItem("premium_chat_dark", JSON.stringify(dark)), [dark]);

  // persist messages
  useEffect(() => {
    localStorage.setItem(storageKey, JSON.stringify(messages));
    // scroll to bottom on new message
    setTimeout(() => {
      containerRef.current?.scrollTo({ top: containerRef.current.scrollHeight, behavior: "smooth" });
    }, 60);
  }, [messages, storageKey]);

  // small helper to add message
  const push = (from, text) => {
    const m = { id: ++idRef.current, from, text, time: nowTime() };
    setMessages((s) => [...s, m]);
    return m;
  };

  // Send user message -> simulate backend reply (replace with real API call later)
  const send = async (text) => {
    if (!text || !text.trim()) return;
    push("user", text);
    setInput("");
    setIsTyping(true);

    // Simulate AI thinking delay
    await new Promise((r) => setTimeout(r, 600));

    // Simulated reply (you'd call your backend here)
    const simulated = generateSimulatedReply(text);

    // show a placeholder bot message for streaming
    const botId = ++idRef.current;
    setMessages((s) => [...s, { id: botId, from: "bot", text: "", time: nowTime(), streaming: true }]);

    await streamSimulatedReply(simulated, (partial) => {
      setMessages((s) => s.map((m) => (m.id === botId ? { ...m, text: partial } : m)));
    }, 8);

    // mark streaming done
    setMessages((s) => s.map((m) => (m.id === botId ? { ...m, streaming: false } : m)));
    setIsTyping(false);
  };

  // Replace this with real LLM call in future (fetch / axios)
  function generateSimulatedReply(userText) {
    // quick lightweight responses
    const low = userText.toLowerCase();
    if (low.includes("productivity")) {
      return "Focus on single-tasking, take short breaks using the Pomodoro method, and do a weekly review to plan your important tasks.";
    }
    if (low.includes("closures") || low.includes("javascript")) {
      return "A closure is a function bundled with its lexical environment. It lets inner functions access outer scope variables even after the outer function finishes.";
    }
    return `Nice question — you asked: "${userText}". I can answer in detail when you connect a backend. For now this is a frontend demo with streaming text.`;
  }

  // handle submit from input
  const onSubmit = (e) => {
    e?.preventDefault();
    if (input.trim() === "") return;
    send(input.trim());
    textAreaRef.current?.focus();
  };

  // quick reply click
  const onQuick = (q) => send(q);

  // clear chat
  const clearChat = () => {
    setMessages([{ id: 1, from: "bot", text: `Hi! I'm ${botName}. Ask me anything.`, time: nowTime() }]);
    localStorage.removeItem(storageKey);
  };

  return (
    <>
      {/* floating toggle button */}
      <div className={`premium-chat-floating ${open ? "open" : "closed"} ${dark ? "dark" : ""}`}>
        <div className="pc-header">
          <div className="pc-left">
            <img className="pc-avatar" src={botAvatar} alt="bot" />
            <div>
              <div className="pc-title">{botName}</div>
              <div className="pc-sub">Instant help • Frontend demo</div>
            </div>
          </div>

          <div className="pc-actions">
            <button
              className="pc-btn"
              title="Theme"
              onClick={() => setDark((d) => !d)}
              aria-label="Toggle theme"
            >
              {dark ? "☀️" : "🌙"}
            </button>
            <button
              className="pc-btn"
              title="Clear chat"
              onClick={clearChat}
              aria-label="Clear chat"
            >
              🗑️
            </button>
            <button
              className="pc-minimize"
              onClick={() => {
                setOpen((o) => {
                  localStorage.setItem("premium_chat_open", JSON.stringify(!o));
                  return !o;
                });
              }}
              aria-label="Minimize"
            >
              {open ? "—" : "✕"}
            </button>
          </div>
        </div>

        {open && (
          <div className="pc-body">
            <div className="pc-messages" ref={containerRef}>
              {messages.map((m) => (
                <div key={m.id} className={`pc-message ${m.from === "user" ? "user" : "bot"} ${m.streaming ? "streaming" : ""}`}>
                  <img src={m.from === "user" ? userAvatar : botAvatar} alt="" className="pc-msg-avatar" />
                  <div className="pc-msg-content">
                    <div className="pc-msg-bubble">{m.text}</div>
                    <div className="pc-msg-time">{m.time}</div>
                  </div>
                </div>
              ))}
              {isTyping && (
                <div className="pc-message bot typing">
                  <img src={botAvatar} alt="" className="pc-msg-avatar" />
                  <div className="pc-msg-content">
                    <div className="pc-msg-bubble typing-bubble">
                      <span className="dots"><span></span><span></span><span></span></span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="pc-suggestions">
              {suggestions.map((s, i) => (
                <button key={i} className="chip" onClick={() => onQuick(s)}>
                  {s}
                </button>
              ))}
            </div>

            <form className="pc-input-row" onSubmit={onSubmit}>
              <textarea
                ref={textAreaRef}
                className="pc-input"
                placeholder="Type a message..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                rows={1}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    onSubmit();
                  }
                }}
              />
              <button type="submit" className="pc-send">Send</button>
            </form>
          </div>
        )}
      </div>

      {/* minimized badge when closed */}
      {!open && (
        <button
          className={`pc-floating-badge ${dark ? "dark" : ""}`}
          onClick={() => setOpen(true)}
          aria-label="Open chat"
        >
          <img src={botAvatar} alt="bot" />
        </button>
      )}
    </>
  );
}
