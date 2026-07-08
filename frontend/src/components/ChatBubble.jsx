import ReactMarkdown from "react-markdown";
import "./ChatBubble.css";

export default function ChatBubble({ role, text, timestamp, ttsPhase }) {
  const isUser = role === "user";
  return (
    <div className={`chat-row ${isUser ? "chat-row-user" : "chat-row-bot"}`}>
      {!isUser && <div className="chat-avatar-dot" />}
      <div className={`chat-bubble ${isUser ? "chat-bubble-user" : "chat-bubble-bot"}`}>
        {isUser ? (
          <p className="chat-bubble-text">{text}</p>
        ) : (
          <div className="chat-bubble-text chat-bubble-markdown">
            <ReactMarkdown>{text}</ReactMarkdown>
          </div>
        )}
        {(timestamp || ttsPhase) && (
          <div className="chat-bubble-footer">
            {timestamp && <span className="chat-bubble-time">{timestamp}</span>}
            {ttsPhase === "loading" && (
              <span className="chat-tts-indicator chat-tts-loading" title="Generating Dhanvi's voice...">
                <span />
                <span />
                <span />
              </span>
            )}
            {ttsPhase === "playing" && (
              <span className="chat-tts-indicator chat-tts-playing" title="Speaking">
                🔊
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
