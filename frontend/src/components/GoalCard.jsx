import { GOAL_ICONS } from "../utils/goalMath";
import { formatINR } from "./AnimatedNumber";
import "./GoalCard.css";

const STATUS_LABEL = { green: "On track", yellow: "Slightly behind", red: "Needs attention" };

export default function GoalCard({ goal, plan, status, onClick }) {
  const pctFunded = Math.min(100, Math.round((goal.current_progress / goal.target_amount) * 100));
  const color = { green: "var(--green)", yellow: "var(--yellow)", red: "var(--red)" }[status] || "var(--text-muted)";

  return (
    <button className="goal-card card card-hover" onClick={onClick}>
      <div
        className="goal-ring"
        style={{
          background: `conic-gradient(${color} ${pctFunded * 3.6}deg, rgba(255,255,255,0.08) 0deg)`,
        }}
      >
        <div className="goal-ring-inner">
          <span className="goal-icon">{GOAL_ICONS[goal.type] || "🎯"}</span>
        </div>
      </div>
      <div className="goal-card-name">{goal.type}</div>
      <div className="goal-card-target">₹{formatINR(goal.target_amount, { compact: true })}</div>
      <div className="goal-card-date">by {new Date(goal.target_date).toLocaleDateString("en-IN", { month: "short", year: "numeric" })}</div>
      <div className={`badge ${status === "green" ? "badge-green" : status === "yellow" ? "badge-yellow" : "badge-red"} goal-status-badge`}>
        {pctFunded}% · {STATUS_LABEL[status] || "..."}
      </div>
      {plan && (
        <div className="goal-card-sip">
          Needs <strong>₹{plan.recommended_monthly_sip.toLocaleString("en-IN")}</strong>/mo
        </div>
      )}
    </button>
  );
}
