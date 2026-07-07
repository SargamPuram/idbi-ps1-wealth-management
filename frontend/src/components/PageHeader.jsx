import CustomerSwitcher from "./CustomerSwitcher";
import "./PageHeader.css";

export default function PageHeader({ title, subtitle }) {
  return (
    <div className="page-header">
      <div>
        <h1 className="page-title">{title}</h1>
        {subtitle && <p className="page-subtitle">{subtitle}</p>}
      </div>
      <CustomerSwitcher compact />
    </div>
  );
}
