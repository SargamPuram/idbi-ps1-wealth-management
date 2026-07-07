import { useMemo, useState } from "react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, LineChart, Line, XAxis, YAxis, CartesianGrid, Legend } from "recharts";
import PageHeader from "../components/PageHeader";
import AnimatedNumber, { formatINR } from "../components/AnimatedNumber";
import { LoadingBlock, ErrorBlock } from "../components/StateViews";
import { useCustomer } from "../context/CustomerContext";
import { api } from "../api/client";
import useFetch from "../hooks/useFetch";
import "./Portfolio.css";

const ASSET_META = {
  fixed_deposits: { label: "Fixed Deposits", color: "#3987e5" },
  mutual_funds: { label: "Mutual Funds", color: "#199e70" },
  insurance: { label: "Insurance", color: "#9085e9" },
  nps: { label: "NPS", color: "#008300" },
  stocks: { label: "Stocks", color: "#d95926" },
  gold: { label: "Gold", color: "#c98500" },
  ppf: { label: "PPF", color: "#e66767" },
};

function seededTrend(seed, endValue, months = 12) {
  let x = 0;
  for (let i = 0; i < seed.length; i++) x = (x * 31 + seed.charCodeAt(i)) >>> 0;
  const rnd = () => {
    x ^= x << 13;
    x ^= x >>> 17;
    x ^= x << 5;
    x >>>= 0;
    return (x % 1000) / 1000;
  };
  const startValue = endValue / 1.14;
  const portfolio = [];
  const benchmark = [];
  let pv = startValue;
  let bv = startValue;
  for (let m = 0; m < months; m++) {
    const pStep = (Math.log(endValue / startValue) / months) + (rnd() - 0.5) * 0.05;
    const bStep = (Math.log(1.10) / 12) + (rnd() - 0.5) * 0.03;
    pv = m === months - 1 ? endValue : pv * Math.exp(pStep);
    bv = bv * Math.exp(bStep);
    portfolio.push(Math.round(pv));
    benchmark.push(Math.round(bv));
  }
  const today = new Date();
  return portfolio.map((v, i) => {
    const d = new Date(today.getFullYear(), today.getMonth() - (months - 1 - i), 1);
    return {
      month: d.toLocaleDateString("en-IN", { month: "short" }),
      portfolio: v,
      benchmark: benchmark[i],
    };
  });
}

export default function Portfolio() {
  const { customerId } = useCustomer();
  const { data, loading, error } = useFetch(() => api.portfolio(customerId), [customerId]);
  const [selectedAsset, setSelectedAsset] = useState(null);

  const pieData = useMemo(() => {
    if (!data) return [];
    return Object.entries(data.asset_breakdown)
      .filter(([, v]) => v > 0)
      .map(([key, value]) => ({ key, name: ASSET_META[key]?.label || key, value }))
      .sort((a, b) => b.value - a.value);
  }, [data]);

  const trend = useMemo(() => {
    if (!data) return [];
    return seededTrend(customerId, data.total_net_worth);
  }, [data, customerId]);

  if (loading) {
    return (
      <>
        <PageHeader title="Portfolio" subtitle="Your complete financial picture" />
        <LoadingBlock height={180} />
        <div style={{ height: 12 }} />
        <LoadingBlock height={260} />
      </>
    );
  }
  if (error) {
    return (
      <>
        <PageHeader title="Portfolio" subtitle="Your complete financial picture" />
        <ErrorBlock message={error.message} />
      </>
    );
  }

  const h = data.holdings;

  return (
    <>
      <PageHeader title="Portfolio" subtitle={`${data.name} · ${data.customer_segment} · ${data.risk_profile}`} />

      <div className="card networth-card">
        <div className="networth-label">Total Net Worth</div>
        <div className="networth-value">
          <AnimatedNumber value={data.total_net_worth} prefix="₹" />
        </div>
        <div className="networth-meta">
          <span className="badge badge-green">Diversification {data.analytics.diversification_score}/100</span>
          <span className="badge badge-purple">SIP ₹{data.analytics.monthly_sip_total.toLocaleString("en-IN")}/mo</span>
        </div>
      </div>

      <div className="section-title">Asset Allocation</div>
      <div className="card">
        <div className="donut-wrap">
          <ResponsiveContainer width="100%" height={230}>
            <PieChart>
              <Pie
                data={pieData}
                dataKey="value"
                nameKey="name"
                innerRadius={62}
                outerRadius={92}
                paddingAngle={2}
                stroke="none"
                onClick={(entry) => setSelectedAsset(selectedAsset === entry.key ? null : entry.key)}
              >
                {pieData.map((entry) => (
                  <Cell
                    key={entry.key}
                    fill={ASSET_META[entry.key]?.color || "#888"}
                    opacity={selectedAsset && selectedAsset !== entry.key ? 0.35 : 1}
                    style={{ cursor: "pointer" }}
                  />
                ))}
              </Pie>
              <Tooltip
                formatter={(value, name) => [`₹${formatINR(value, { compact: true })}`, name]}
                contentStyle={{ background: "#1a1f35", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 10 }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="donut-center">
            <div className="donut-center-value">₹{formatINR(data.total_net_worth, { compact: true })}</div>
            <div className="donut-center-label">Net Worth</div>
          </div>
        </div>
        <div className="legend-grid">
          {pieData.map((entry) => (
            <button
              key={entry.key}
              className={`legend-item ${selectedAsset === entry.key ? "legend-item-active" : ""}`}
              onClick={() => setSelectedAsset(selectedAsset === entry.key ? null : entry.key)}
            >
              <span className="legend-dot" style={{ background: ASSET_META[entry.key]?.color }} />
              <span className="legend-name">{entry.name}</span>
              <span className="legend-pct">{data.asset_allocation_pct[entry.key]}%</span>
            </button>
          ))}
        </div>
      </div>

      <div className="section-title">Holdings</div>

      {(!selectedAsset || selectedAsset === "fixed_deposits") && h.fixed_deposits.length > 0 && (
        <div className="card card-hover holding-card">
          <div className="holding-header">
            <span>🏦 Fixed Deposits</span>
            <span className="badge badge-purple">{h.fixed_deposits.length}</span>
          </div>
          {h.fixed_deposits.map((fd, i) => (
            <div className="holding-row" key={i}>
              <div>
                <div className="holding-row-title">{fd.bank}</div>
                <div className="holding-row-sub">Matures {fd.maturity_date}</div>
              </div>
              <div className="holding-row-right">
                <div className="holding-row-amount">₹{formatINR(fd.amount, { compact: true })}</div>
                <div className="holding-row-sub">{fd.rate}% p.a.</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {(!selectedAsset || selectedAsset === "mutual_funds") && h.mutual_funds.length > 0 && (
        <div className="card card-hover holding-card">
          <div className="holding-header">
            <span>📈 Mutual Funds</span>
            <span className="badge badge-purple">{h.mutual_funds.length}</span>
          </div>
          {h.mutual_funds.map((mf, i) => {
            const ret = mf.invested_amount ? ((mf.current_value - mf.invested_amount) / mf.invested_amount) * 100 : 0;
            return (
              <div className="holding-row" key={i}>
                <div>
                  <div className="holding-row-title">{mf.scheme_name}</div>
                  <div className="holding-row-sub">
                    {mf.type} {mf.sip_amount > 0 && `· SIP ₹${mf.sip_amount} on ${mf.sip_date}${ordinalSuffix(mf.sip_date)}`}
                  </div>
                </div>
                <div className="holding-row-right">
                  <div className="holding-row-amount">₹{formatINR(mf.current_value, { compact: true })}</div>
                  <div className={`holding-row-sub ${ret >= 0 ? "text-green" : "text-red"}`}>
                    {ret >= 0 ? "+" : ""}
                    {ret.toFixed(1)}%
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {(!selectedAsset || selectedAsset === "insurance") && h.insurance.length > 0 && (
        <div className="card card-hover holding-card">
          <div className="holding-header">
            <span>🛡️ Insurance</span>
            <span className="badge badge-purple">{h.insurance.length}</span>
          </div>
          {h.insurance.map((ins, i) => (
            <div className="holding-row" key={i}>
              <div>
                <div className="holding-row-title">{ins.plan_name}</div>
                <div className="holding-row-sub">
                  {ins.type} · {ins.provider}
                </div>
              </div>
              <div className="holding-row-right">
                <div className="holding-row-amount">₹{formatINR(ins.sum_assured, { compact: true })}</div>
                <div className="holding-row-sub">₹{ins.premium.toLocaleString("en-IN")}/{ins.premium_frequency.toLowerCase()}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {(!selectedAsset || selectedAsset === "nps") && h.nps.tier1_balance > 0 && (
        <div className="card card-hover holding-card">
          <div className="holding-header">
            <span>🏛️ NPS</span>
          </div>
          <div className="holding-row">
            <div>
              <div className="holding-row-title">Tier 1</div>
              <div className="holding-row-sub">Monthly ₹{h.nps.monthly_contribution.toLocaleString("en-IN")}</div>
            </div>
            <div className="holding-row-right">
              <div className="holding-row-amount">₹{formatINR(h.nps.tier1_balance, { compact: true })}</div>
            </div>
          </div>
          {h.nps.tier2_balance > 0 && (
            <div className="holding-row">
              <div className="holding-row-title">Tier 2</div>
              <div className="holding-row-right">
                <div className="holding-row-amount">₹{formatINR(h.nps.tier2_balance, { compact: true })}</div>
              </div>
            </div>
          )}
        </div>
      )}

      {(!selectedAsset || selectedAsset === "stocks") && h.stocks.length > 0 && (
        <div className="card card-hover holding-card">
          <div className="holding-header">
            <span>📊 Stocks</span>
            <span className="badge badge-purple">{h.stocks.length}</span>
          </div>
          {h.stocks.map((s, i) => {
            const ret = ((s.current_price - s.avg_price) / s.avg_price) * 100;
            return (
              <div className="holding-row" key={i}>
                <div>
                  <div className="holding-row-title">{s.symbol}</div>
                  <div className="holding-row-sub">{s.quantity} shares @ ₹{s.avg_price}</div>
                </div>
                <div className="holding-row-right">
                  <div className="holding-row-amount">₹{formatINR(s.quantity * s.current_price, { compact: true })}</div>
                  <div className={`holding-row-sub ${ret >= 0 ? "text-green" : "text-red"}`}>
                    {ret >= 0 ? "+" : ""}
                    {ret.toFixed(1)}%
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {(!selectedAsset || selectedAsset === "gold") && (h.gold.physical_grams + h.gold.digital_grams + h.gold.sgb_units > 0) && (
        <div className="card card-hover holding-card">
          <div className="holding-header">
            <span>🥇 Gold</span>
          </div>
          <div className="holding-row">
            <div className="holding-row-title">
              {h.gold.physical_grams}g physical · {h.gold.digital_grams}g digital · {h.gold.sgb_units} SGB units
            </div>
            <div className="holding-row-right">
              <div className="holding-row-amount">₹{formatINR(data.asset_breakdown.gold, { compact: true })}</div>
            </div>
          </div>
        </div>
      )}

      {(!selectedAsset || selectedAsset === "ppf") && h.ppf.balance > 0 && (
        <div className="card card-hover holding-card">
          <div className="holding-header">
            <span>🌱 PPF</span>
          </div>
          <div className="holding-row">
            <div className="holding-row-title">Yearly contribution ₹{h.ppf.yearly_contribution.toLocaleString("en-IN")}</div>
            <div className="holding-row-right">
              <div className="holding-row-amount">₹{formatINR(h.ppf.balance, { compact: true })}</div>
            </div>
          </div>
        </div>
      )}

      <div className="section-title">Returns Performance</div>
      <div className="card">
        <div className="chart-caption">Portfolio value vs. a broad market benchmark (illustrative 12-month trend)</div>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={trend} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" vertical={false} />
            <XAxis dataKey="month" tick={{ fill: "#6b7191", fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis
              tick={{ fill: "#6b7191", fontSize: 10 }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => formatINR(v, { compact: true })}
              width={48}
            />
            <Tooltip
              formatter={(value, name) => [`₹${formatINR(value, { compact: true })}`, name === "portfolio" ? "Your Portfolio" : "Benchmark"]}
              contentStyle={{ background: "#1a1f35", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 10 }}
            />
            <Legend
              formatter={(value) => (value === "portfolio" ? "Your Portfolio" : "Benchmark")}
              wrapperStyle={{ fontSize: 12, color: "#a2a8c3" }}
            />
            <Line type="monotone" dataKey="benchmark" stroke="#6b7191" strokeWidth={2} strokeDasharray="4 4" dot={false} />
            <Line type="monotone" dataKey="portfolio" stroke="#667eea" strokeWidth={2.5} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div style={{ height: 8 }} />
    </>
  );
}

function ordinalSuffix(n) {
  if (!n) return "";
  const s = ["th", "st", "nd", "rd"];
  const v = n % 100;
  return s[(v - 20) % 10] || s[v] || s[0];
}
