import { useMemo, useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { formatINR } from "./AnimatedNumber";
import { GOAL_ICONS, monthsToReachTarget } from "../utils/goalMath";
import "./GoalDetailModal.css";

const SCENARIO_COLORS = { conservative: "#199e70", moderate: "#3987e5", aggressive: "#d95926" };

export default function GoalDetailModal({ goal, plan, onClose }) {
  const [extraSip, setExtraSip] = useState(0);

  const baseMonths = plan.years_to_goal * 12;
  const usedScenarioKey = { Conservative: "conservative", Moderate: "moderate", Aggressive: "aggressive" }[plan.risk_profile_used] || "moderate";
  const usedScenario = plan.scenarios[usedScenarioKey];
  const annualRate = usedScenario.assumed_annual_return_pct / 100;

  const newMonths = useMemo(() => {
    return monthsToReachTarget(
      goal.target_amount,
      goal.current_progress,
      plan.recommended_monthly_sip + extraSip,
      annualRate
    );
  }, [extraSip, goal, plan, annualRate]);

  const monthsEarlier = newMonths === null ? 0 : Math.max(0, Math.round(baseMonths - newMonths));

  const chartData = useMemo(() => {
    const maxYears = Math.max(
      ...Object.values(plan.scenarios).map((s) => s.growth_projection.length)
    );
    const rows = [];
    for (let i = 0; i < maxYears; i++) {
      const row = { year: `Y${i + 1}` };
      for (const [key, s] of Object.entries(plan.scenarios)) {
        row[key] = s.growth_projection[i]?.projected_value ?? null;
      }
      rows.push(row);
    }
    return rows;
  }, [plan]);

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-sheet card-glass" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title">
            <span className="modal-icon">{GOAL_ICONS[goal.type] || "🎯"}</span> {goal.type}
          </div>
          <button className="modal-close" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="modal-timeline">
          <div className="timeline-track">
            <div
              className="timeline-fill"
              style={{ width: `${Math.min(100, (goal.current_progress / goal.target_amount) * 100)}%` }}
            />
          </div>
          <div className="timeline-labels">
            <span>₹{formatINR(goal.current_progress, { compact: true })} saved</span>
            <span>Target ₹{formatINR(goal.target_amount, { compact: true })}</span>
          </div>
          <div className="timeline-date">
            Target date: {new Date(goal.target_date).toLocaleDateString("en-IN", { month: "long", year: "numeric" })} (
            {plan.years_to_goal} yrs away)
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

        <div className="modal-section-title">What if you invest more?</div>
        <div className="whatif-box">
          <div className="whatif-row">
            <span>
              Current plan: <strong>₹{plan.recommended_monthly_sip.toLocaleString("en-IN")}/mo</strong>
            </span>
            <span>
              +₹{extraSip.toLocaleString("en-IN")}/mo
            </span>
          </div>
          <input
            type="range"
            min={0}
            max={Math.max(5000, Math.round(plan.recommended_monthly_sip))}
            step={500}
            value={extraSip}
            onChange={(e) => setExtraSip(Number(e.target.value))}
            className="whatif-slider"
          />
          <div className="whatif-result">
            {monthsEarlier > 0 ? (
              <>
                Reach your goal <strong className="text-green">{monthsEarlier} months earlier</strong> by adding ₹
                {extraSip.toLocaleString("en-IN")}/month.
              </>
            ) : (
              "Move the slider to see how much sooner you could reach this goal."
            )}
          </div>
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
                strokeWidth={key === usedScenarioKey ? 2.75 : 1.75}
                dot={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
