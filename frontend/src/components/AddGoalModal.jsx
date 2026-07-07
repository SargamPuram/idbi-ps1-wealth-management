import { useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { formatINR } from "./AnimatedNumber";
import { GOAL_ICONS } from "../utils/goalMath";
import { api } from "../api/client";
import { useCustomer } from "../context/CustomerContext";
import "./GoalDetailModal.css";
import "./AddGoalModal.css";

const SCENARIO_COLORS = { conservative: "#199e70", moderate: "#3987e5", aggressive: "#d95926" };
const GOAL_TYPES = Object.keys(GOAL_ICONS);

function defaultTargetDate(yearsAhead = 5) {
  const d = new Date();
  d.setFullYear(d.getFullYear() + yearsAhead);
  return d.toISOString().slice(0, 10);
}

export default function AddGoalModal({ onClose }) {
  const { customerId } = useCustomer();
  const [form, setForm] = useState({
    goal_type: "Wealth Growth",
    target_amount: 1000000,
    target_date: defaultTargetDate(),
    current_progress: 0,
  });
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const result = await api.goalPlan({ customer_id: customerId, ...form });
      setPlan(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const chartData = plan
    ? (() => {
        const maxYears = Math.max(...Object.values(plan.scenarios).map((s) => s.growth_projection.length));
        const rows = [];
        for (let i = 0; i < maxYears; i++) {
          const row = { year: `Y${i + 1}` };
          for (const [key, s] of Object.entries(plan.scenarios)) {
            row[key] = s.growth_projection[i]?.projected_value ?? null;
          }
          rows.push(row);
        }
        return rows;
      })()
    : [];

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-sheet card-glass" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title">
            <span className="modal-icon">✨</span> Plan a new goal
          </div>
          <button className="modal-close" onClick={onClose}>
            ✕
          </button>
        </div>

        {!plan && (
          <form onSubmit={handleSubmit} className="add-goal-form">
            <label className="form-label">
              Goal type
              <select
                className="form-input"
                value={form.goal_type}
                onChange={(e) => setForm({ ...form, goal_type: e.target.value })}
              >
                {GOAL_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {GOAL_ICONS[t]} {t}
                  </option>
                ))}
              </select>
            </label>
            <label className="form-label">
              Target amount (₹)
              <input
                type="number"
                className="form-input"
                min={10000}
                step={10000}
                value={form.target_amount}
                onChange={(e) => setForm({ ...form, target_amount: Number(e.target.value) })}
              />
            </label>
            <label className="form-label">
              Target date
              <input
                type="date"
                className="form-input"
                value={form.target_date}
                onChange={(e) => setForm({ ...form, target_date: e.target.value })}
              />
            </label>
            <label className="form-label">
              Already saved (₹)
              <input
                type="number"
                className="form-input"
                min={0}
                step={1000}
                value={form.current_progress}
                onChange={(e) => setForm({ ...form, current_progress: Number(e.target.value) })}
              />
            </label>
            {error && <div className="chat-inline-error">{error}</div>}
            <button className="btn btn-primary" type="submit" disabled={loading} style={{ width: "100%", marginTop: 6 }}>
              {loading ? "Calculating..." : "Generate Plan"}
            </button>
          </form>
        )}

        {plan && (
          <>
            <div className="plan-result-hero">
              <div className="plan-result-label">Monthly SIP needed</div>
              <div className="plan-result-value">₹{plan.recommended_monthly_sip.toLocaleString("en-IN")}</div>
              <div className="plan-result-sub">
                over {plan.years_to_goal} years, assuming {plan.risk_profile_used} risk profile
              </div>
            </div>

            <div className="modal-section-title">Recommended instruments</div>
            <div className="instrument-chips">
              {plan.recommended_instruments.map((ins) => (
                <span key={ins} className="chip" style={{ cursor: "default" }}>
                  {ins}
                </span>
              ))}
            </div>

            <div className="modal-section-title">Growth projection (by risk scenario)</div>
            <ResponsiveContainer width="100%" height={190}>
              <LineChart data={chartData} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" vertical={false} />
                <XAxis dataKey="year" tick={{ fill: "#6b7191", fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis
                  tick={{ fill: "#6b7191", fontSize: 10 }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={(v) => formatINR(v, { compact: true })}
                  width={44}
                />
                <Tooltip
                  formatter={(value, name) => [`₹${formatINR(value, { compact: true })}`, name]}
                  contentStyle={{ background: "#1a1f35", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 10 }}
                />
                <Legend wrapperStyle={{ fontSize: 11, color: "#a2a8c3" }} />
                {Object.keys(plan.scenarios).map((key) => (
                  <Line
                    key={key}
                    type="monotone"
                    dataKey={key}
                    name={key.charAt(0).toUpperCase() + key.slice(1)}
                    stroke={SCENARIO_COLORS[key]}
                    strokeWidth={2}
                    dot={false}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
            <button className="btn btn-ghost" style={{ width: "100%", marginTop: 10 }} onClick={() => setPlan(null)}>
              Plan another goal
            </button>
          </>
        )}
      </div>
    </div>
  );
}
