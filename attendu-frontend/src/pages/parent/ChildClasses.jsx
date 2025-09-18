import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getChildClasses } from "../../api.js";

export default function ChildClasses() {
  const { childId } = useParams();
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState("");
  const [classes, setClasses] = useState([]);

  async function load() {
    setLoading(true);
    setMsg("");
    try {
      const res = await getChildClasses(Number(childId));
      setClasses(res?.classes ?? []);
    } catch (e) {
      setMsg(e?.message || "Failed to load classes.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); /* eslint-disable-next-line */ }, [childId]);

  return (
    <div className="page">
      <div className="card" style={{ maxWidth: 900, width: "100%", display: "grid", gap: 16 }}>
        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <Link to="/dashboard" className="link">← Back</Link>
          <h3 className="title" style={{ margin: 0 }}>Child #{childId} — Classes</h3>
        </div>

        {msg && <p>{msg}</p>}
        {loading ? (
          <p>Loading…</p>
        ) : classes.length === 0 ? (
          <p style={{ opacity: 0.8 }}>No classes yet.</p>
        ) : (
          <ul style={{ listStyle: "none", padding: 0, display: "grid", gap: 8 }}>
            {classes.map((c) => (
              <Link key={c.id} to={`/parent/children/${childId}/classes/${c.id}`} style={{ textDecoration: "none", color: "inherit" }}>
                <li
                  style={{
                    background: "#061B20",
                    border: "1px solid #ffffff",
                    borderLeft: "6px solid #2563EB",
                    borderRadius: 10,
                    padding: "12px 14px",
                    cursor: "pointer",
                    transition: "background 0.2s",
                  }}
                  onMouseEnter={(e) => {
                        e.currentTarget.style.background = "#0A2C36";
                    }}
                    onMouseLeave={(e) => {
                        e.currentTarget.style.background = "#061B20";
                    }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <div>
                      <div style={{ fontSize: 16 }}>{c.name}</div>
                      <div style={{ fontSize: 12, opacity: 0.8 }}>
                        {c.teacher_name ? `Teacher: ${c.teacher_name}` : "—"}
                        {c.teacher_email ? ` • ${c.teacher_email}` : ""}
                      </div>
                    </div>
                    <span style={{ opacity: 0.7, fontSize: 12 }}>ID: {c.id}</span>
                  </div>
                </li>
              </Link>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
