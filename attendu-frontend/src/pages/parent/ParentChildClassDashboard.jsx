import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  getParentChildClassMeta,
  getParentChildAttendanceToday,
  getParentChildAttendanceHistory,
} from "../../api.js";

export default function ParentChildClassDashboard() {
  const { childId, classId } = useParams();
  const cid = Number(classId);
  const sid = Number(childId);

  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState("");
  const [meta, setMeta] = useState(null);
  const [today, setToday] = useState(null);
  const [history, setHistory] = useState([]);

  async function load() {
    setLoading(true);
    setMsg("");
    try {
      const [m, t, h] = await Promise.all([
        getParentChildClassMeta(sid, cid),
        getParentChildAttendanceToday(sid, cid),
        getParentChildAttendanceHistory(sid, cid, { limit: 30 }),
      ]);
      setMeta(m?.meta ?? null);
      setToday(t?.today ?? null);
      setHistory(Array.isArray(h?.history) ? h.history : []);
    } catch (e) {
      setMsg(e?.message || "Failed to load class.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); /* eslint-disable-next-line */ }, [sid, cid]);

  const Card = ({ children, accent = "#2563EB", border = "#ffffff" }) => (
    <div style={{
      background: "#061B20",
      border: `1px solid ${border}`,
      borderLeft: `6px solid ${accent}`,
      borderRadius: 10,
      padding: "12px 14px"
    }}>{children}</div>
  );

  return (
    <div className="page">
      <div className="card" style={{ maxWidth: 900, width: "100%", display: "grid", gap: 16 }}>
        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <Link to={`/parent/children/${sid}`} className="link">← Back</Link>
          <h3 className="title" style={{ margin: 0 }}>
            {meta ? `${meta.class_name} — Child #${sid}` : `Class #${cid}`}
          </h3>
        </div>

        {msg && <p>{msg}</p>}
        {loading ? (
          <p>Loading…</p>
        ) : (
          <>
            {/* Teacher */}
            <section>
              <h4 style={{ margin: "4px 0 8px" }}>Teacher</h4>
              <Card accent="#3B82F6">
                {meta?.teacher ? (
                  <div>
                    <div style={{ fontSize: 16, fontWeight: 600 }}>{meta.teacher.name}</div>
                    <div style={{ fontSize: 12, opacity: 0.8 }}>{meta.teacher.email}</div>
                  </div>
                ) : (
                  <div style={{ opacity: 0.8 }}>—</div>
                )}
              </Card>
            </section>

            {/* Today */}
            <section>
              <h4 style={{ margin: "12px 0 8px" }}>Today</h4>
              <Card accent="#10B981">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div>
                    <div style={{ fontSize: 14, opacity: 0.8 }}>
                      {today?.date || "—"}
                    </div>
                    <div style={{ fontSize: 18, fontWeight: 600 }}>
                      {today?.attended ? "Present ✅" : "Not checked in"}
                    </div>
                  </div>
                </div>
              </Card>
            </section>

            {/* History */}
            <section>
              <h4 style={{ margin: "12px 0 8px" }}>Attendance History</h4>
              {history.length === 0 ? (
                <p style={{ opacity: 0.8, margin: 0 }}>No attendance records yet.</p>
              ) : (
                <div style={{ display: "grid", gap: 8 }}>
                  {history.map((r) => (
                    <Card key={r.date} accent={r.attended ? "#22C55E" : "#EF4444"}>
                      <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <span>{r.date}</span>
                        <span>{r.attended ? "Present" : "Absent"}</span>
                      </div>
                    </Card>
                  ))}
                </div>
              )}
            </section>
          </>
        )}
      </div>
    </div>
  );
}
