import { useMemo, useState } from "react";
import PageHeader from "../components/PageHeader";
import { LoadingBlock, ErrorBlock } from "../components/StateViews";
import { useCustomer } from "../context/CustomerContext";
import { api } from "../api/client";
import useFetch from "../hooks/useFetch";
import "./Products.css";

const CATEGORY_ORDER = ["FDs", "MFs", "Insurance", "NPS", "Gold", "PPF", "Bonds"];

export default function Products() {
  const { customerId } = useCustomer();
  const { data, loading, error } = useFetch(() => api.products(customerId), [customerId]);
  const [activeTab, setActiveTab] = useState("FDs");
  const [compareSet, setCompareSet] = useState([]);

  const categories = useMemo(() => {
    if (!data) return [];
    return CATEGORY_ORDER.filter((c) => data.categories[c]);
  }, [data]);

  if (loading) {
    return (
      <>
        <PageHeader title="Product Catalog" subtitle="FDs, Mutual Funds, Insurance, NPS, Gold, PPF & Bonds" />
        <LoadingBlock height={300} />
      </>
    );
  }
  if (error) {
    return (
      <>
        <PageHeader title="Product Catalog" subtitle="FDs, Mutual Funds, Insurance, NPS, Gold, PPF & Bonds" />
        <ErrorBlock message={error.message} />
      </>
    );
  }

  const products = data.categories[activeTab] || [];

  function toggleCompare(name) {
    setCompareSet((prev) =>
      prev.includes(name) ? prev.filter((n) => n !== name) : prev.length < 3 ? [...prev, name] : prev
    );
  }

  const compareProducts = products.filter((p) => compareSet.includes(p.name));

  return (
    <>
      <PageHeader title="Product Catalog" subtitle="FDs, Mutual Funds, Insurance, NPS, Gold, PPF & Bonds" />

      <div className="prod-tabs">
        {categories.map((c) => (
          <button
            key={c}
            className={`prod-tab ${activeTab === c ? "prod-tab-active" : ""}`}
            onClick={() => setActiveTab(c)}
          >
            {c}
          </button>
        ))}
      </div>

      {compareSet.length > 0 && (
        <div className="card compare-bar">
          <span className="compare-bar-label">Comparing {compareSet.length} product{compareSet.length > 1 ? "s" : ""}</span>
          <button className="btn btn-ghost" onClick={() => setCompareSet([])}>
            Clear
          </button>
        </div>
      )}

      {compareSet.length > 1 && (
        <div className="compare-table-wrap card">
          <table className="compare-table">
            <thead>
              <tr>
                <th>Product</th>
                <th>Risk</th>
                <th>Returns</th>
                <th>Min. Investment</th>
                <th>Lock-in</th>
              </tr>
            </thead>
            <tbody>
              {compareProducts.map((p) => (
                <tr key={p.name}>
                  <td>{p.name}</td>
                  <td>{p.risk}</td>
                  <td>{p.returns_range}</td>
                  <td>₹{p.min_investment.toLocaleString("en-IN")}</td>
                  <td>{p.lock_in}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="prod-grid">
        {products.map((p) => (
          <div className="card prod-card" key={p.name}>
            {p.recommended_for_you && <span className="badge badge-purple prod-rec-badge">Recommended for you</span>}
            <div className="prod-card-name">{p.name}</div>
            <div className="prod-card-risk">Risk: {p.risk}</div>
            <div className="prod-card-row">
              <span className="prod-card-label">Returns</span>
              <span className="prod-card-value">{p.returns_range}</span>
            </div>
            <div className="prod-card-row">
              <span className="prod-card-label">Min. Investment</span>
              <span className="prod-card-value">₹{p.min_investment.toLocaleString("en-IN")}</span>
            </div>
            <div className="prod-card-row">
              <span className="prod-card-label">Lock-in</span>
              <span className="prod-card-value">{p.lock_in}</span>
            </div>
            <div className="prod-card-actions">
              <label className="prod-compare-check">
                <input
                  type="checkbox"
                  checked={compareSet.includes(p.name)}
                  onChange={() => toggleCompare(p.name)}
                  disabled={!compareSet.includes(p.name) && compareSet.length >= 3}
                />
                Compare
              </label>
              <a
                className="btn btn-primary prod-cta"
                href="https://www.idbibank.in"
                target="_blank"
                rel="noreferrer"
              >
                Invest via IDBI Bank
              </a>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
