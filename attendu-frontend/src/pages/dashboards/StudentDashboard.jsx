import React, { useEffect, useState } from "react";
import {
  getClasses,
  getMyParentsAsStudent,
  getStudentFamilyRequests,      // GET /api/students/family/requests?status=pending
  getStudentClassInvites,        // GET /api/students/classes/requests?status=pending
  studentRespondToParentRequest, // PATCH /api/students/family/requests/:id
  studentRespondToClassInvite,   // PATCH /api/students/classes/requests/:id
  logout,
  studentSendParentRequest
} from "../../api.js";
import { useAuth } from "../../AuthContext.jsx";
import { useNavigate, Link } from "react-router-dom";
import {ActionButton} from "../../components/ActionButton.jsx";

export default function StudentDashboard() {
  const [classes, setClasses] = useState([]);
  const [parents, setParents] = useState([]);        // current family (connected parents)
  const [familyReqs, setFamilyReqs] = useState([]);  // incoming family requests
  const [classInvites, setClassInvites] = useState([]); // incoming class invites
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(true);
  const { setAuthed, setUser } = useAuth();
  const [joinCode, setJoinCode] = useState("");
  const [joining, setJoining] = useState(false);
  const [parentEmail, setParentEmail] = useState("");
  const [invitingParent, setInvitingParent] = useState(false);
  const navigate = useNavigate();

  async function load() {
  setLoading(true);
  setMsg("");

  const [clsRes, famRes, famReqRes, clsReqRes] = await Promise.allSettled([
    getClasses(),
    getMyParentsAsStudent(),
    getStudentFamilyRequests("pending"),
    getStudentClassInvites("pending"),
  ]);

  // Classes
  if (clsRes.status === "fulfilled") {
    setClasses(clsRes.value?.classes ?? []);
  } else {
    setMsg((m) => m || clsRes.reason?.message || "Failed to load classes.");
  }

  // Connected parents (family)
  if (famRes.status === "fulfilled") {
    setParents(famRes.value?.parents ?? []);
  } else {
    setMsg((m) => m || famRes.reason?.message || "Failed to load family.");
  }

  // Family requests
  if (famReqRes.status === "fulfilled") {
    setFamilyReqs(famReqRes.value?.requests ?? []);
  } else {
    // don’t block the page if this one fails
    setFamilyReqs([]);
  }

  // Class invites
  if (clsReqRes.status === "fulfilled") {
    setClassInvites(clsReqRes.value?.requests ?? []);
  } else {
    setClassInvites([]);
  }

  setLoading(false);
}

  useEffect(() => { load(); }, []);

  async function handleLogout() {
    try { await logout(); } catch {}
    setAuthed(false);
    setUser(null);
    navigate("/login", { replace: true });
  }

  async function handleFamilyReq(reqId, decision) {
    setMsg("");
    try {
      await studentRespondToParentRequest(reqId, decision); // PATCH
      setFamilyReqs((s) => s.filter((r) => r.request_id !== reqId));

      if (decision === "accept") {
        const fam = await getMyParentsAsStudent();          // refresh connected parents
        setParents(fam?.parents ?? []);
      }
      setMsg(decision === "accept" ? "Connected to parent." : "Request rejected.");
    } catch (err) {
      setMsg(err?.message || "Failed to process family request.");
    }
  }

  async function handleClassInvite(reqId, decision) {
    setMsg("");
    try {
      await studentRespondToClassInvite(reqId, decision);   // PATCH
      setClassInvites((s) => s.filter((r) => r.request_id !== reqId));

      if (decision === "accept") {
        const cls = await getClasses();                     // refresh classes
        setClasses(cls?.classes ?? []);
      }
      setMsg(decision === "accept" ? "Class invite accepted." : "Class invite rejected.");
    } catch (err) {
      setMsg(err?.message || "Failed to process invite.");
    }
  }

  async function handleJoinByCode(e) {
  e.preventDefault();
  const code = joinCode.trim();
  if (!code) return setMsg("Please enter a class code.");
  setJoining(true);
  setMsg("");
  try {
    const api = await import("../../api.js");
    if (!api.studentJoinClassByCode) {
      setMsg("Joining by code isn’t enabled in this build.");
      return;
    }
    await api.studentJoinClassByCode(code);
    setJoinCode("");
    setMsg("Join request sent. You’ll see the class after the teacher accepts.");

    // refresh pending invites since we may implement auto-accept flows later...
    try {
      const clsReqs = await getStudentClassInvites("pending");
      setClassInvites(clsReqs?.requests ?? []);
    } catch {}
  } catch (err) {
    setMsg(err?.message || "Failed to send join request.");
  } finally {
    setJoining(false);
  }
}

  async function handleInviteParent(e) {
    e.preventDefault();
    const email = parentEmail.trim();
    if (!email) return setMsg("Please enter a parent email.");
    setInvitingParent(true);
    setMsg("");
    try {
      await studentSendParentRequest(email);
      setParentEmail("");
      setMsg("Request sent to parent.");
      // Optional: in the future you could fetch an “outgoing” list if you add a backend for it.
    } catch (err) {
      setMsg(err?.message || "Failed to send parent request.");
    } finally {
      setInvitingParent(false);
    }
  }

  const Card = ({ children, accent = "#124559", border = "#ffffff" }) => (
    <div style={{ background: "#051E27", border: `1px solid ${border}`, borderLeft: `6px solid ${accent}`, borderRadius: 10, padding: "12px 14px" }}>
      {children}
    </div>
  );

  return (
    <div className="page">
      <div className="card" style={{ maxWidth: 820, width: "100%", display: "grid", gap: 16 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h3 className="title" style={{ margin: 0 }}>Student Dashboard</h3>
          <button onClick={handleLogout}>Log out</button>
        </div>

        {msg && <p>{msg}</p>}

        {loading ? (
          <p>Loading…</p>
        ) : (
          <>
            {/* Family (connected) */}
            <section>
              <h4 style={{ margin: "4px 0 8px" }}>Family</h4>
              {parents.length === 0 ? (
                <p style={{ opacity: 0.8, margin: 0 }}>No family connected.</p>
              ) : (
                <div style={{ display: "grid", gap: 10 }}>
                  {parents.map(p => (
                    <Card key={p.id} accent="#3B82F6" border="#BFDBFE">
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10 }}>
                        <div>
                          <div style={{ fontSize: 16, fontWeight: 600 }}>{p.name}</div>
                          <div style={{ fontSize: 12, opacity: 0.8 }}>{p.email}</div>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              )}
            </section>

            {/* Connect a Parent */}
            <section>
              <h4 style={{ margin: "12px 0 8px" }}>Connect a Parent</h4>
              <form
                onSubmit={handleInviteParent}
                style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 8 }}
              >
                <input
                  className="input"
                  type="email"
                  placeholder="parent@email.com"
                  value={parentEmail}
                  onChange={(e) => setParentEmail(e.target.value)}
                />
                <button type="submit" disabled={invitingParent}>Invite</button>
              </form>
              <p style={{ opacity: 0.8, marginTop: 6 }}>
                We’ll send a connection request to this email. They’ll see it on their dashboard.
              </p>
            </section>

            {/* Family Requests */}
            <section>
              <h4 style={{ margin: "12px 0 8px" }}>Family Requests</h4>
              {familyReqs.length === 0 ? (
                <p style={{ opacity: 0.8, margin: 0 }}>No pending family requests.</p>
              ) : (
                <div style={{ display: "grid", gap: 10 }}>
                  {familyReqs.map(r => (
                    <Card key={r.request_id} accent="#8B5CF6" border="#C4B5FD">
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10 }}>
                        <div>
                          <div style={{ fontSize: 16, fontWeight: 600 }}>{r.from_parent_name || "Parent"}</div>
                          <div style={{ fontSize: 12, opacity: 0.8 }}>{r.from_parent_email}</div>
                        </div>
                        <div style={{ display: "flex", gap: 8 }}>
                          <ActionButton variant="danger" onClick={() => handleFamilyReq(r.request_id, "reject")}>✖ Reject</ActionButton>
                          <ActionButton variant="success" onClick={() => handleFamilyReq(r.request_id, "accept")}>✔ Accept</ActionButton>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              )}
            </section>

            {/* Class Invites */}
            <section>
              <h4 style={{ margin: "12px 0 8px" }}>Class Invites</h4>
              {classInvites.length === 0 ? (
                <p style={{ opacity: 0.8, margin: 0 }}>No pending class invites.</p>
              ) : (
                <div style={{ display: "grid", gap: 10 }}>
                  {classInvites.map(r => (
                    <Card key={r.request_id} accent="#10B981" border="#A7F3D0">
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10 }}>
                        <div>
                          <div style={{ fontSize: 16, fontWeight: 600 }}>{r.class_name || "Class"}</div>
                          <div style={{ fontSize: 12, opacity: 0.8 }}>
                            {r.teacher_name ? `Teacher: ${r.teacher_name}` : null} &nbsp; | &nbsp; ID: {r.class_id}
                          </div>
                        </div>
                        <div style={{ display: "flex", gap: 8 }}>
                          <ActionButton variant="danger" onClick={() => handleClassInvite(r.request_id, "reject")}>✖ Reject</ActionButton>
                          <ActionButton variant="success" onClick={() => handleClassInvite(r.request_id, "accept")}>✔ Accept</ActionButton>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              )}
            </section>

            {/* Join a Class */}
            <section>
              <h4 style={{ margin: "12px 0 8px" }}>Join a Class</h4>
              <form onSubmit={handleJoinByCode} style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 8 }}>
                <input
                  className="input"
                  type="text"
                  placeholder="Enter class code"
                  value={joinCode}
                  onChange={(e) => setJoinCode(e.target.value)}
                />
                <button type="submit" disabled={joining}>Request</button>
              </form>
              <p style={{ opacity: 0.8, marginTop: 6 }}>
                Ask your teacher for the code and paste it here to request access.
              </p>
            </section>

            {/* My Classes */}
            <section>
              <h4 style={{ margin: "12px 0 8px" }}>My Classes</h4>
              {classes.length === 0 ? (
                <p style={{ opacity: 0.8, margin: 0 }}>You’re not in any classes yet.</p>
              ) : (
                <ul style={{ listStyle: "none", padding: 0, display: "grid", gap: 8 }}>
                  {classes.map((it) => (
                    <Link key={it.id} to={`/classes/${it.id}`} style={{ textDecoration: "none", color: "inherit" }}>
                      <li
                        style={{
                          background: "#061B20",
                          border: "1px solid #ffffff",
                          borderLeft: "6px solid #2563EB",
                          borderRadius: 10,
                          padding: "12px 14px",
                          cursor: "pointer",
                          transition: "background 0.2s"
                        }}
                        onMouseEnter={(e) => (e.currentTarget.style.background = "#073543")}
                        onMouseLeave={(e) => (e.currentTarget.style.background = "#061B20")}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <span style={{ fontSize: 16 }}>{it.name}</span>
                          <span style={{ opacity: 0.7, fontSize: 12 }}>ID: {it.id}</span>
                        </div>
                      </li>
                    </Link>
                  ))}
                </ul>
              )}
            </section>
          </>
        )}
      </div>
    </div>
  );
}
