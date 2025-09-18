import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  logout,
  getMyChildren,
  parentSendChildRequest,
  getParentIncomingFamilyRequests,
  getParentOutgoingFamilyRequests,
  parentRespondToStudentRequest,
} from "../../api.js";
import { useAuth } from "../../AuthContext.jsx";
import { useNavigate } from "react-router-dom";
import { ActionButton } from "../../components/ActionButton.jsx";

export default function ParentDashboard() {
  const [children, setChildren] = useState([]);
  const [incoming, setIncoming] = useState([]);
  const [outgoingPending, setOutgoingPending] = useState([]);
  const [outgoingRejected, setOutgoingRejected] = useState([]);
  const [inviteEmail, setInviteEmail] = useState("");
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(true);

  const { setAuthed, setUser } = useAuth();
  const navigate = useNavigate();

  async function load() {
    setLoading(true);
    setMsg("");
    try {
      const [kids, inc, outPend, outRej] = await Promise.all([
        getMyChildren(),                                   // current children
        getParentIncomingFamilyRequests("pending"),        // students -> me
        getParentOutgoingFamilyRequests("pending"),        // my sent (pending)
        getParentOutgoingFamilyRequests("rejected"),       // my sent (rejected)
      ]);
      setChildren(kids?.children ?? []);
      setIncoming(inc?.requests ?? []);
      setOutgoingPending(outPend?.requests ?? []);
      setOutgoingRejected(outRej?.requests ?? []);
    } catch (err) {
      setMsg(err?.message || "Failed to load.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function handleLogout() {
    try { await logout(); } catch {}
    setAuthed(false);
    setUser(null);
    navigate("/login", { replace: true });
  }

  async function handleInvite(e) {
    e.preventDefault();
    setMsg("");
    try {
      if (!inviteEmail.trim()) return setMsg("Email is required.");
      await parentSendChildRequest(inviteEmail.trim());
      setInviteEmail("");
      const outPend = await getParentOutgoingFamilyRequests("pending");
      setOutgoingPending(outPend?.requests ?? []);
      setMsg("Request sent.");
    } catch (err) {
      setMsg(err?.message || "Failed to send request.");
    }
  }

  async function handleIncoming(reqId, decision) {
    setMsg("");
    try {
      await parentRespondToStudentRequest(reqId, decision);
      setIncoming((s) => s.filter((r) => r.request_id !== reqId));
      if (decision === "accept") {
        const kids = await getMyChildren();
        setChildren(kids?.children ?? []);
      }
      setMsg(decision === "accept" ? "Connected to student." : "Request rejected.");
    } catch (err) {
      setMsg(err?.message || "Failed to process request.");
    }
  }

  const Card = ({ children, accent = "#124559", border = "#ffffff" }) => (
    <div
      style={{
        background: "#051E27",
        border: `1px solid ${border}`,
        borderLeft: `6px solid ${accent}`,
        borderRadius: 10,
        padding: "12px 14px",
      }}
    >
      {children}
    </div>
  );

  return (
    <div className="page">
      <div className="card" style={{ maxWidth: 820, width: "100%", display: "grid", gap: 16 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h3 className="title" style={{ margin: 0 }}>Parent Dashboard</h3>
          <button onClick={handleLogout}>Log out</button>
        </div>

        {msg && <p>{msg}</p>}

        {loading ? (
          <p>Loading…</p>
        ) : (
          <>
            {/* My Children */}
            <section>
              <h4 style={{ margin: "4px 0 8px" }}>My Children</h4>
              {children.length === 0 ? (
                <p style={{ opacity: 0.8, margin: "0 0 8px" }}>No children connected yet. Invite one below.</p>
              ) : (
                <ul style={{ listStyle: "none", padding: 0, display: "grid", gap: 8 }}>
                  {children.map((c) => (
                      <Link key={c.id} to={`/parent/children/${c.id}`} style={{ textDecoration: "none", color: "inherit" }}>
                        <li
                          key={c.id}
                          style={{
                            background: "#061B20",
                            border: "1px solid #ffffff",
                            borderRadius: 10,
                            padding: "12px 14px",
                            cursor: "pointer",
                            transition: "background 0.2s",
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.background = "#0A2C36"; // hover color
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.background = "#061B20"; // reset
                          }}
                          onClick={() => navigate(`/parent/children/${c.id}/classes`)} // still clickable
                        >
                          <div style={{ display: "flex", justifyContent: "space-between" }}>
                            <span style={{ fontSize: 16 }}>{c.name}</span>
                            <span style={{ opacity: 0.7, fontSize: 12 }}>ID: {c.id}</span>
                          </div>
                        </li>
                      </Link>
                    ))}
                </ul>
              )}
            </section>

            {/* Invite Child */}
            <section>
              <h4 style={{ margin: "12px 0 8px" }}>Invite a Child</h4>
              <form onSubmit={handleInvite} style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 8 }}>
                <input
                  className="input"
                  type="email"
                  placeholder="Student email"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                />
                <button type="submit">Send</button>
              </form>
            </section>

            {/* Requests */}
            <section>
              <h4 style={{ margin: "12px 0 8px" }}>Requests</h4>

              {/* Incoming */}
              <div style={{ marginBottom: 12 }}>
                <div style={{ opacity: 0.8, fontSize: 14, marginBottom: 6 }}>Incoming</div>
                {incoming.length === 0 ? (
                  <p style={{ opacity: 0.8, margin: 0 }}>No pending incoming requests.</p>
                ) : (
                  <div style={{ display: "grid", gap: 10 }}>
                    {incoming.map((r) => (
                      <Card key={r.request_id} accent="#8B5CF6" border="#C4B5FD">
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10 }}>
                          <div>
                            <div style={{ fontSize: 16, fontWeight: 600 }}>
                              {r.from_student_name} <span style={{ opacity: 0.8, fontSize: 12 }}>&lt;{r.from_student_email}&gt;</span>
                            </div>
                            <div style={{ fontSize: 12, opacity: 0.8 }}>wants to connect as your child</div>
                          </div>
                          <div style={{ display: "flex", gap: 8 }}>
                            <ActionButton variant="danger" onClick={() => handleIncoming(r.request_id, "reject")}>
                            ✖ Reject
                            </ActionButton>
                            <ActionButton variant="success" onClick={() => handleIncoming(r.request_id, "accept")}>
                            ✔ Accept                            
                            </ActionButton>
                        </div>
                        </div>
                      </Card>
                    ))}
                  </div>
                )}
              </div>

              {/* Outgoing summary */}
              <div>
                <div style={{ opacity: 0.8, fontSize: 14, marginBottom: 6 }}>My Sent Requests</div>

                <Card accent="#4B5563" border="#9CA3AF">
                  <div style={{ display: "grid", gap: 10 }}>
                    <div>
                      <div style={{ opacity: 0.7, fontSize: 13, marginBottom: 4 }}>Pending</div>
                      {outgoingPending.length === 0 ? (
                        <p style={{ opacity: 0.8, margin: 0 }}>None pending.</p>
                      ) : (
                        <ul style={{ listStyle: "none", padding: 0, display: "grid", gap: 6 }}>
                          {outgoingPending.map((r) => (
                            <li key={r.request_id} style={{ padding: "6px 8px", border: "1px solid #335", borderRadius: 8 }}>
                              {r.to_student_name} <span style={{ opacity: 0.7 }}>&lt;{r.to_student_email}&gt;</span>
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>

                    <div>
                      <div style={{ opacity: 0.7, fontSize: 13, marginBottom: 4 }}>Rejected</div>
                      {outgoingRejected.length === 0 ? (
                        <p style={{ opacity: 0.8, margin: 0 }}>No rejections.</p>
                      ) : (
                        <ul style={{ listStyle: "none", padding: 0, display: "grid", gap: 6 }}>
                          {outgoingRejected.map((r) => (
                            <li
                              key={r.request_id}
                              style={{
                                padding: "6px 8px",
                                border: "1px solid #553",
                                borderRadius: 8,
                                background: "#2b1a1a",
                              }}
                            >
                              {r.to_student_name} <span style={{ opacity: 0.7 }}>&lt;{r.to_student_email}&gt;</span>{" "}
                              — <span style={{ color: "#f88" }}>Rejected</span>
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  </div>
                </Card>
              </div>
            </section>
          </>
        )}
      </div>
    </div>
  );
}
