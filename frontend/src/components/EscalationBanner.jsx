import "./EscalationBanner.css";

export default function EscalationBanner({ reason, onEscalate, escalated }) {
  return (
    <div className="escalation-banner">
      <div className="escalation-icon">🧑‍💼</div>
      <div className="escalation-body">
        <div className="escalation-title">This needs a certified Relationship Manager</div>
        <p className="escalation-reason">{reason}</p>
      </div>
      <button className="btn btn-gold escalation-btn" disabled={escalated} onClick={onEscalate}>
        {escalated ? "Escalated ✓" : "Connect RM"}
      </button>
    </div>
  );
}
