import { useState } from "react";
import { DEMO_CUSTOMERS, useCustomer } from "../context/CustomerContext";
import "./CustomerSwitcher.css";

export default function CustomerSwitcher({ compact = false }) {
  const { customerId, setCustomerId, currentDemo } = useCustomer();
  const [open, setOpen] = useState(false);

  return (
    <div className="switcher-wrap">
      <button
        type="button"
        className={`chip switcher-trigger ${compact ? "switcher-compact" : ""}`}
        onClick={() => setOpen((o) => !o)}
      >
        <span className="switcher-avatar-dot" />
        {compact ? currentDemo.name.split(" ")[0] : `${currentDemo.name} · ${currentDemo.segment}`}
        <span className="switcher-caret">{open ? "▲" : "▼"}</span>
      </button>
      {open && (
        <>
          <div className="switcher-backdrop" onClick={() => setOpen(false)} />
          <div className="switcher-menu card-glass">
            <div className="switcher-menu-title">Demo customer profiles</div>
            {DEMO_CUSTOMERS.map((c) => (
              <button
                key={c.id}
                className={`switcher-item ${c.id === customerId ? "switcher-item-active" : ""}`}
                onClick={() => {
                  setCustomerId(c.id);
                  setOpen(false);
                }}
              >
                <div className="switcher-item-main">
                  <span className="switcher-item-name">{c.name}</span>
                  <span className="switcher-item-city">{c.city}</span>
                </div>
                <div className="switcher-item-tags">
                  <span className="badge badge-purple">{c.segment}</span>
                  <span className="badge badge-gold">{c.risk}</span>
                </div>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
