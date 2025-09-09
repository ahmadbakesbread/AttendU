import React, { useEffect, useState } from "react";
import { createClass, getClasses, logout } from "../api.js";
import { useAuth } from "../AuthContext.jsx";
import { useNavigate } from "react-router-dom";

// functional component returns UI, dashboard
// export default -> component can be imported/used anywhere else.
export default function Dashboard() {
  // hooks that manage component's state (FOUR HERE)
  const [classes, setClasses] = useState([]);       // stores list of classes fetched from server, empty array
  const [className, setClassName] = useState("");   // stores name of class, starts as empty string
  const [msg, setMsg] = useState("");               // stores error/response msg
  const [loading, setLoading] = useState(true);     // true/false val to show loading spinner while fetching

  const { setAuthed } = useAuth();                  // from AuthContext, updates authentication status (logged in/out)
  const navigate = useNavigate();                   // just a simple redirect-er


  // function to fetch the list of classes
  async function loadClasses() {
    setLoading(true);
    setMsg("");                                     //  clear old response msg
    try {
      const data = await getClasses();              // get class data from backend (from api.js)   
      setClasses(data?.classes ?? []);              // if api response has data.classes save in state (else default to [])
    } catch (err) {
      setMsg(err?.message || "Failed to load classes.");
    } finally {
      setLoading(false);
    }
  }

  // when dashboard component first loads, automatically fetch classes.
  useEffect(() => {
    loadClasses();
  }, []);

  // handles creating a new class
  async function handleCreate(e) {                    
    // submitting a form refreshes entire page by default
    e.preventDefault();                             // this is an SPA, so prevent refreshing entire page
    setMsg("");
    if (!className.trim()) {                        // if name is empty (remove whitespace)
      setMsg("Class name is required.");
      return;
    }
    try {
      await createClass(className.trim());          // send new class name to backend
      setClassName("");                             // clear input field after creation
      await loadClasses();                          // call function we made earlier
      setMsg("Class created.");
    } catch (err) {
      setMsg(err?.message || "Failed to create class.");
    }
  }

  async function handleLogout() {
    try {
      await logout();                               // calls backend to logout
    } catch {}
    setAuthed(false);                               // mark user as NOT logged in
    navigate("/login", { replace: true });          // route me back to login page
  }

  // dashboard layout
  return (
    <div className="page">
      {/* inner div has a card style that centers the dashboard */}
      <div className="card" style={{ maxWidth: 720, width: "100%" }}>

        {/* flexbox header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
          <h3 className="title" style={{ margin: 0, textAlign: "left" }}>Classes</h3>
          <button onClick={handleLogout}>Log out</button>
        </div>

        {/* creating class form, call handlecreate when user presses create */}
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

        {/* the display messages (responses) */}
        {msg && <p style={{ marginBottom: 12 }}>{msg}</p>}

        {/* how we will display the classes or the loading state, conditional rendering */}
        {loading ? (
          <p>Loading…</p> // case 1 (loading)
        ) : classes.length === 0 ? ( // case 2 (no classes)
          <p>No classes yet. Create your first one above.</p>
        ) : ( // case 3 (show (unordered, remove bulleted) list of classes, loop thru classes array, create one <li> - list item, per class)
          <ul style={{ listStyle: "none", padding: 0, display: "grid", gap: 8 }}> 
            {classes.map((c) => (
              <li key={c.id} style={{ background: "#051E27", border: "1px solid #ffffff", borderRadius: 10, padding: "12px 14px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontSize: 16 }}>{c.name}</span>
                  <span style={{ opacity: 0.7, fontSize: 12 }}>ID: {c.id}</span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
