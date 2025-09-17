import { Link } from "react-router-dom";

export default function ListCardLink({ to, title, right }) {
  return (
    <Link to={to} style={{ textDecoration: "none", color: "inherit" }}>
      <li
        style={{
          background: "#051E27",
          border: "1px solid #ffffff",
          borderRadius: 10,
          padding: "12px 14px",
          cursor: "pointer",
          transition: "background 0.2s"
        }}
        onMouseEnter={(e) => (e.currentTarget.style.background = "#073543")}
        onMouseLeave={(e) => (e.currentTarget.style.background = "#051E27")}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span style={{ fontSize: 16 }}>{title}</span>
          {right ? <span style={{ opacity: 0.7, fontSize: 12 }}>{right}</span> : null}
        </div>
      </li>
    </Link>
  );
}
