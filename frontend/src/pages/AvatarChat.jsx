import { useEffect, useRef, useState } from "react";
import Avatar from "../components/Avatar";
import ChatBubble from "../components/ChatBubble";
import ProductRecCard from "../components/ProductRecCard";
import EscalationBanner from "../components/EscalationBanner";
import CustomerSwitcher from "../components/CustomerSwitcher";
import { useCustomer, LANGUAGES } from "../context/CustomerContext";
import { api } from "../api/client";
import { WELCOME_MESSAGES, QUICK_ACTIONS } from "../i18n";
import "./AvatarChat.css";

function timeNow() {
  return new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
}

let msgIdCounter = 0;
const nextId = () => ++msgIdCounter;

export default function AvatarChat() {
  const { customerId, language, setLanguage } = useCustomer();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [avatarState, setAvatarState] = useState("idle");
  const [isTyping, setIsTyping] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [bannerError, setBannerError] = useState(null);
  const [muted, setMuted] = useState(() => localStorage.getItem("dhanvi_tts_muted") === "1");
  const [ttsMsgId, setTtsMsgId] = useState(null);
  const [ttsPhase, setTtsPhase] = useState(null); // "loading" | "playing" | null
  const scrollRef = useRef(null);
  const recognitionRef = useRef(null);
  const audioRef = useRef(null);
  const audioUrlRef = useRef(null);
  const ttsSeqRef = useRef(0);
  const mutedRef = useRef(muted);

  useEffect(() => {
    mutedRef.current = muted;
    localStorage.setItem("dhanvi_tts_muted", muted ? "1" : "0");
    if (muted) cancelSpeech();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [muted]);

  // Stops/clears any in-flight or playing Dhanvi audio and invalidates stale
  // TTS requests (so a slow /tts response for an old message can't suddenly
  // start playing over a newer one).
  function cancelSpeech() {
    ttsSeqRef.current += 1;
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.onended = null;
      audioRef.current.onerror = null;
      audioRef.current = null;
    }
    if (audioUrlRef.current) {
      URL.revokeObjectURL(audioUrlRef.current);
      audioUrlRef.current = null;
    }
    setTtsMsgId(null);
    setTtsPhase(null);
  }

  // Fetches /tts for a bot message and plays it. Decoupled from /chat — this
  // only runs after the text response is already rendered.
  async function speakMessage(msgId, text, lang) {
    cancelSpeech();
    if (mutedRef.current) {
      setTimeout(() => setAvatarState("idle"), 1600);
      return;
    }
    const seq = ttsSeqRef.current;
    setTtsMsgId(msgId);
    setTtsPhase("loading");
    try {
      const blob = await api.tts({ text, language: lang });
      if (seq !== ttsSeqRef.current) return; // superseded while the request was in flight
      const url = URL.createObjectURL(blob);
      audioUrlRef.current = url;
      const audio = new Audio(url);
      audioRef.current = audio;
      const finish = () => {
        if (seq === ttsSeqRef.current) {
          setTtsPhase(null);
          setTtsMsgId(null);
          setAvatarState("idle");
        }
      };
      audio.onended = finish;
      audio.onerror = finish;
      setTtsPhase("playing");
      await audio.play();
    } catch (err) {
      if (seq === ttsSeqRef.current) {
        setTtsPhase(null);
        setTtsMsgId(null);
        setAvatarState("idle");
      }
      // Non-fatal: a broken/unreachable /tts shouldn't break the text chat.
      console.warn("Dhanvi voice reply failed:", err.message);
    }
  }

  // Reset conversation whenever the demo persona or language changes.
  useEffect(() => {
    cancelSpeech();
    const welcomeText = WELCOME_MESSAGES[language] || WELCOME_MESSAGES.English;
    const welcomeId = nextId();
    setMessages([
      {
        id: welcomeId,
        role: "bot",
        text: welcomeText,
        timestamp: timeNow(),
      },
    ]);
    // The welcome line is a genuine Dhanvi reply too (just not from /chat), so
    // speak it on load/persona-switch — that's the moment a demo needs to land.
    speakMessage(welcomeId, welcomeText, language);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [customerId, language]);

  // Stop any playing audio if the user navigates away from this page.
  useEffect(() => {
    return () => cancelSpeech();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, isTyping]);

  async function sendMessage(text) {
    const trimmed = (text ?? input).trim();
    if (!trimmed) return;
    setInput("");
    setBannerError(null);
    // Starting a new turn should cut off any reply Dhanvi is still speaking,
    // rather than letting it overlap/garble with the next response.
    cancelSpeech();

    const userMsg = { id: nextId(), role: "user", text: trimmed, timestamp: timeNow() };
    const history = messages
      .filter((m) => m.role === "user" || m.role === "bot")
      .slice(-8)
      .map((m) => ({ role: m.role === "bot" ? "assistant" : "user", content: m.text }));

    setMessages((prev) => [...prev, userMsg]);
    setIsTyping(true);
    setAvatarState("thinking");

    try {
      const res = await api.chat({
        customer_id: customerId,
        message: trimmed,
        language,
        conversation_history: history,
      });

      setAvatarState("speaking");
      const botMsgId = nextId();
      setMessages((prev) => [
        ...prev,
        {
          id: botMsgId,
          role: "bot",
          text: res.response,
          timestamp: timeNow(),
          aiPowered: res.ai_powered,
          recs: res.product_recommendations || [],
          escalation: res.escalation_needed ? res.escalation_reason : null,
        },
      ]);
      speakMessage(botMsgId, res.response, language);
    } catch (err) {
      setAvatarState("idle");
      setMessages((prev) => [
        ...prev,
        {
          id: nextId(),
          role: "bot",
          text: `Sorry, I couldn't reach the backend. ${err.message}`,
          timestamp: timeNow(),
          isError: true,
        },
      ]);
    } finally {
      setIsTyping(false);
    }
  }

  async function handleEscalate(msgId, reason) {
    try {
      await api.escalate({
        customer_id: customerId,
        reason,
        context_summary: `Raised from Dhanvi chat on ${new Date().toLocaleDateString("en-IN")}`,
      });
      setMessages((prev) => prev.map((m) => (m.id === msgId ? { ...m, escalated: true } : m)));
    } catch (err) {
      setBannerError(err.message);
    }
  }

  function toggleVoiceInput() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setBannerError("Voice input isn't supported in this browser. Try Chrome on desktop or Android.");
      return;
    }
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
      return;
    }
    const recognition = new SpeechRecognition();
    recognition.lang = language === "Hindi" ? "hi-IN" : "en-IN";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setInput((prev) => (prev ? `${prev} ${transcript}` : transcript));
    };
    recognition.onend = () => setIsListening(false);
    recognition.onerror = () => setIsListening(false);
    recognitionRef.current = recognition;
    recognition.start();
    setIsListening(true);
  }

  return (
    <div className="chat-page">
      <div className="chat-topbar">
        <div>
          <div className="chat-topbar-title">Dhanvi</div>
          <div className="chat-topbar-subtitle">Your IDBI Wealth Advisor</div>
        </div>
        <div className="chat-topbar-controls">
          <button
            type="button"
            className={`mute-btn ${muted ? "mute-btn-muted" : ""}`}
            onClick={() => setMuted((m) => !m)}
            aria-label={muted ? "Unmute Dhanvi's voice" : "Mute Dhanvi's voice"}
            aria-pressed={muted}
            title={muted ? "Dhanvi's voice is muted" : "Dhanvi speaks her replies aloud"}
          >
            {muted ? "🔇" : "🔊"}
          </button>
          <select
            className="lang-select"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            aria-label="Select language"
          >
            {LANGUAGES.map((l) => (
              <option key={l} value={l}>
                {l}
              </option>
            ))}
          </select>
          <CustomerSwitcher compact />
        </div>
      </div>

      <div className="avatar-section">
        <Avatar state={avatarState} />
        <div className="avatar-name">Dhanvi</div>
        <div className="avatar-tag">IDBI Bank · AI Wealth Coach</div>
      </div>

      <div className="chat-scroll" ref={scrollRef}>
        {messages.map((m) => (
          <div key={m.id}>
            <ChatBubble
              role={m.role}
              text={m.text}
              timestamp={m.timestamp}
              ttsPhase={m.role === "bot" && ttsMsgId === m.id ? ttsPhase : null}
            />
            {m.recs && m.recs.length > 0 && m.recs.map((rec, i) => <ProductRecCard key={i} rec={rec} />)}
            {m.escalation && (
              <EscalationBanner
                reason={m.escalation}
                escalated={m.escalated}
                onEscalate={() => handleEscalate(m.id, m.escalation)}
              />
            )}
          </div>
        ))}
        {isTyping && (
          <div className="chat-row chat-row-bot">
            <div className="chat-avatar-dot" />
            <div className="chat-bubble chat-bubble-bot">
              <div className="typing-indicator">
                <span />
                <span />
                <span />
              </div>
            </div>
          </div>
        )}
        {bannerError && <div className="chat-inline-error">{bannerError}</div>}
      </div>

      <div className="quick-actions hscroll">
        {QUICK_ACTIONS.map((q) => (
          <button key={q.label} className="chip" onClick={() => sendMessage(q.message)}>
            <span>{q.icon}</span> {q.label}
          </button>
        ))}
      </div>

      <form
        className="chat-input-bar"
        onSubmit={(e) => {
          e.preventDefault();
          sendMessage();
        }}
      >
        <button
          type="button"
          className={`voice-btn ${isListening ? "voice-btn-active" : ""}`}
          onClick={toggleVoiceInput}
          aria-label="Voice input"
          title="Voice input"
        >
          🎤
        </button>
        <input
          className="chat-input"
          placeholder="Ask Dhanvi anything about your money..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button type="submit" className="send-btn" disabled={!input.trim()} aria-label="Send">
          ➤
        </button>
      </form>
    </div>
  );
}
