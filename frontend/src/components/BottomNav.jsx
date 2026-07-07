import { NavLink } from "react-router-dom";
import "./BottomNav.css";

const ITEMS = [
  { to: "/", label: "Dhanvi", icon: "💬", end: true },
  { to: "/portfolio", label: "Portfolio", icon: "📊" },
  { to: "/goals", label: "Goals", icon: "🎯" },
  { to: "/market", label: "Market", icon: "📈" },
  { to: "/products", label: "Products", icon: "🛍️" },
];

export default function BottomNav() {
  return (
    <nav className="bottom-nav">
      {ITEMS.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.end}
          className={({ isActive }) => `bottom-nav-item ${isActive ? "bottom-nav-item-active" : ""}`}
        >
          <span className="bottom-nav-icon">{item.icon}</span>
          <span className="bottom-nav-label">{item.label}</span>
        </NavLink>
      ))}
    </nav>
  );
}
