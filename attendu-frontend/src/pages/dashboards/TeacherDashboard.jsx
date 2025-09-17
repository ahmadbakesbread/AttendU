import React, { useEffect, useState } from "react";
import { createClass, getClasses, logout } from "../../api.js";
import { useAuth } from "../../AuthContext.jsx";
import { useNavigate } from "react-router-dom";
import ListCardLink from "../../components/ListCardLink.jsx";

export default function TeacherDashboard() {
  const [items, setItems] = useState([]);
  const [className, setClassName] = useState("");
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(true);
  const { setAuthed, setUser } = useAuth();
  const navigate = useNavigate();

  async function load() {
    setLoading(true);
    setMsg("");
    try {
      const data = await getClasses();
      setItems(data?.classes ?? []);
    } catch (err) {
      setMsg(err?.message || "Failed to load.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function handleCreate(e) {
    e.preventDefault();
    setMsg("");
    if (!className.trim()) return setMsg("Class name is required.");
    try {
      await createClass(className.trim());
      setClassName("");
      await load();
      setMsg("Class created.");
    } catch (err) {
      setMsg(err?.message || "Failed to create class.");
    }
  }

  async function handleLogout() {
    try { await logout(); } catch {}
    setAuthed(false);
    setUser(null);
    navigate("/login", { replace: true });
  }

  return (
    <div className="page">
      <div className="card" style={{ maxWidth: 720, width: "100%" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
          <h3 className="title" style={{ margin: 0 }}>Classes</h3>
          <button onClick={handleLogout}>Log out</button>
        </div>

        <form onSubmit={handleCreate} style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 8, marginBottom: 16 }}>
          <input
            className="input"
            type="text"
            placeholder="New class name"
            value={className}
            onChange={(e) => setClassName(e.target.value)}
          />
          <button type="submit">Create</button>
        </form>

        {msg && <p style={{ marginBottom: 12 }}>{msg}</p>}

        {loading ? (
          <p>Loading…</p>
        ) : items.length === 0 ? (
          <p>No classes yet. Create your first one above.</p>
        ) : (
          <ul style={{ listStyle: "none", padding: 0, display: "grid", gap: 8 }}>
            {items.map((it) => (
              <ListCardLink key={it.id} to={`/classes/${it.id}`} title={it.name} right={`ID: ${it.id}`} />
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
