import "./ProductRecCard.css";

const PRIORITY_BADGE = { High: "badge-red", Medium: "badge-yellow", Low: "badge-green" };

export default function ProductRecCard({ rec }) {
  return (
    <div className="prod-rec-card">
      <div className="prod-rec-top">
        <div>
          <div className="prod-rec-name">{rec.product}</div>
          <div className="prod-rec-category">{rec.category}</div>
        </div>
        <span className={`badge ${PRIORITY_BADGE[rec.priority] || "badge-purple"}`}>{rec.priority} priority</span>
      </div>
      <p className="prod-rec-reason">{rec.reason}</p>
      <div className="prod-rec-footer">
        {rec.regulated && <span className="badge badge-purple">Needs RM sign-off</span>}
        <div className="prod-rec-actions">
          <button className="btn btn-ghost prod-rec-btn">Learn More</button>
          <button className="btn btn-primary prod-rec-btn">Invest Now</button>
        </div>
      </div>
    </div>
  );
}
