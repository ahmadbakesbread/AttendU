// src/pages/classes/ClassDashboard.jsx
import React, { useEffect, useState, useRef } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import {
  getClassStudents,
  getClassCode,
  getTodayAttendanceForClass,
  removeStudentFromClass,
  logout,
  markAttendanceFromFrame
} from "../../api.js";
import { useAuth } from "../../AuthContext.jsx";
import { ActionButton } from "../../components/ActionButton.jsx"

export default function ClassDashboard() {
  const { id } = useParams();              // class id
  const classId = Number(id);
  const navigate = useNavigate();
  const { setAuthed, setUser } = useAuth();

  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState("");
  const [students, setStudents] = useState([]);
  const [classCode, setClassCode] = useState("");
  const [todayMap, setTodayMap] = useState({}); // { studentId: true/false }
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviting, setInviting] = useState(false);
  const [joinReqs, setJoinReqs] = useState([]);
  const [attRunning, setAttRunning] = useState(false);
  const [recentMarks, setRecentMarks] = useState([]);
  const [attMsg, setAttMsg] = useState("");
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const timerRef = useRef(null);
  const streamRef = useRef(null);

  async function load() {
    setLoading(true);
    setMsg("");
    try {
      const [stuRes, codeRes, attRes, reqRes] = await Promise.allSettled([
      getClassStudents(classId),
      getClassCode(classId),
      getTodayAttendanceForClass ? getTodayAttendanceForClass(classId) : Promise.resolve({}),
      import("../../api.js").then(m => m.getTeacherClassJoinRequests(classId)),
    ]);

      if (reqRes.status === "fulfilled") {
        setJoinReqs(reqRes.value?.requests ?? []);
      }

      if (stuRes.status === "fulfilled") {
        setStudents(Array.isArray(stuRes.value?.students) ? stuRes.value.students : []);
      } else {
        setMsg(stuRes.reason?.message || "Failed to load students.");
      }

      if (codeRes.status === "fulfilled") {
        setClassCode(codeRes.value?.data ?? "");
      }

      if (getTodayAttendanceForClass && attRes.status === "fulfilled") {
        // expect: { records: [{ student_id, attended }] }
        const m = {};
        (attRes.value?.records ?? []).forEach(r => { m[r.student_id] = !!r.attended; });
        setTodayMap(m);
      }
    } catch (e) {
      setMsg(e?.message || "Failed to load class.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); /* eslint-disable-next-line */ }, [classId]);

  async function handleRemove(studentId) {
    if (!window.confirm("Remove this student from the class?")) return;
    setMsg("");
    try {
      await removeStudentFromClass(classId, studentId);
      setStudents(s => s.filter(x => x.id !== studentId));
      setMsg("Student removed.");
    } catch (e) {
      setMsg(e?.message || "Failed to remove student.");
    }
  }

  async function handleLogout() {
    try { await logout(); } catch {}
    setAuthed(false);
    setUser(null);
    navigate("/login", { replace: true });
  }

  function copyCode() {
    if (!classCode) return;
    navigator.clipboard.writeText(classCode).then(() => setMsg("Class code copied!"));
  }

  async function handleInvite(e) {
  e.preventDefault();
  const email = inviteEmail.trim();
  if (!email) return setMsg("Please enter a student email.");
  setInviting(true);
  setMsg("");
  try {
    const api = await import("../../api.js");
    if (!api.teacherInviteStudent) {
      setMsg("Invites aren’t enabled in this build.");
      return;
    }
    await api.teacherInviteStudent(classId, email);
    setInviteEmail("");
    setMsg("Invite sent successfully.");
  } catch (err) {
    setMsg(err?.message || "Failed to send invite.");
  } finally {
    setInviting(false);
  }
}

async function handleRequest(requestId, decision) {
  setMsg("");
  try {
    const { teacherRespondToJoinRequest } = await import("../../api.js");
    await teacherRespondToJoinRequest(classId, requestId, decision);
    // remove from list
    setJoinReqs(rs => rs.filter(r => r.request_id !== requestId));
    // if accepted, student is now in the class -> refresh students
    if (decision === "accept") {
      const s = await getClassStudents(classId);
      setStudents(Array.isArray(s?.students) ? s.students : []);
      setMsg("Request accepted.");
    } else {
      setMsg("Request rejected.");
    }
  } catch (e) {
    setMsg(e?.message || "Failed to process request.");
  }
}

async function startAttendance() {
  setAttMsg("");
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" }, audio: false });
    streamRef.current = stream;
    if (videoRef.current) {
      videoRef.current.srcObject = stream;
      await videoRef.current.play();
    }
    setAttRunning(true);
    timerRef.current = setInterval(captureAndSend, 2000);
  } catch (e) {
    setAttMsg(e?.message || "Failed to open camera.");
  }
}

function stopAttendance() {
  setAttRunning(false);
  if (timerRef.current) clearInterval(timerRef.current);
  if (videoRef.current) videoRef.current.pause();
  if (streamRef.current) {
    streamRef.current.getTracks().forEach(t => t.stop());
    streamRef.current = null;
  }
}

useEffect(() => () => stopAttendance(), []);

async function captureAndSend() {
  const video = videoRef.current, canvas = canvasRef.current;
  if (!video || !canvas) return;

  const w = video.videoWidth || 640, h = video.videoHeight || 480;
  canvas.width = w; canvas.height = h;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(video, 0, 0, w, h);

  const blob = await new Promise(res => canvas.toBlob(res, "image/jpeg", 0.85));
  if (!blob) return;

  try {
    const res = await markAttendanceFromFrame(classId, blob);
    if (res?.matched_student) {
      const item = {
        id: res.matched_student.id,
        name: res.matched_student.name,
        already: !!res.already_marked,
        distance: Number(res.distance).toFixed(3),
      };
      setRecentMarks(prev => [item, ...prev.slice(0, 7)]);
      setTodayMap(m => ({ ...m, [item.id]: true }));
    }
  } catch (e) {
    // expected common cases: 422 (no face), 404 (no confident match)
    // keep quiet to avoid spam; optionally set a subtle status:
    // setAttMsg(e?.message || "No match")
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

  const Row = ({ children }) => (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        gap: 12,
        padding: "10px 12px",
        border: "1px solid #ffffff",
        borderLeft: "6px solid #2563EB",
        borderRadius: 10,
        background: "#061B20",
      }}
    >
      {children}
    </div>
  );


  return (
    <div className="page">
      <div className="card" style={{ maxWidth: 900, width: "100%", display: "grid", gap: 16 }}>
        {/* Header / Nav */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
            <Link to="/dashboard" className="link">← Back</Link>
            <h3 className="title" style={{ margin: 0 }}>Class #{classId}</h3>
          </div>
          <button onClick={handleLogout}>Log out</button>
        </div>

        {msg && <p>{msg}</p>}

        {loading ? (
          <p>Loading…</p>
        ) : (
          <>
            {/* Class Code */}
            <section>
              <h4 style={{ margin: "4px 0 8px" }}>Class Code</h4>
              <Row>
                <div style={{ fontSize: 16 }}>
                  {classCode ? <code style={{ fontSize: 18 }}>{classCode}</code> : "—"}
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  <button onClick={copyCode} disabled={!classCode}>Copy</button>
                </div>
              </Row>
              <p style={{ opacity: 0.8, marginTop: 6 }}>
                Share this code with students so they can submit a join request.
              </p>
            </section>

            <section>
              <h4 style={{ margin: "12px 0 8px" }}>Invite a Student</h4>
              <form onSubmit={handleInvite} style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 8 }}>
                <input
                  className="input"
                  type="email"
                  placeholder="student@email.com"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                />
                <button type="submit" disabled={inviting}>Invite</button>
              </form>
              <p style={{ opacity: 0.8, marginTop: 6 }}>
                We’ll send a class invitation to this email. They’ll see it on their dashboard.
              </p>
            </section>

            {/* Join Requests */}
            <section>
              <h4 style={{ margin: "12px 0 8px" }}>Join Requests</h4>
              {joinReqs.length === 0 ? (
                <p style={{ opacity: 0.8, margin: 0 }}>No pending requests.</p>
              ) : (
                <div style={{ display: "grid", gap: 10 }}>
                  {joinReqs.map((r) => (
                    <Card key={r.request_id} accent="#8B5CF6" border="#C4B5FD">
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10 }}>
                        <div>
                          <div style={{ fontSize: 16, fontWeight: 600 }}>
                            {r.student_name}{" "}
                            <span style={{ opacity: 0.8, fontSize: 12 }}>&lt;{r.student_email}&gt;</span>
                          </div>
                          <div style={{ fontSize: 12, opacity: 0.8 }}>wants to join your class</div>
                        </div>
                        <div style={{ display: "flex", gap: 8 }}>
                          <ActionButton variant="danger" onClick={() => handleRequest(r.request_id, "reject")}>✖ Reject</ActionButton>
                          <ActionButton variant="success" onClick={() => handleRequest(r.request_id, "accept")}>✔ Accept</ActionButton>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              )}
            </section>

            <section>
              <h4 style={{ margin: "12px 0 8px" }}>Attendance (Face Scan)</h4>
              <div style={{ display: "grid", gap: 8 }}>
                <div style={{ display: "flex", gap: 8 }}>
                  {!attRunning ? (
                    <button onClick={startAttendance}>Start Attendance</button>
                  ) : (
                    <button onClick={stopAttendance}>Stop</button>
                  )}
                  {attMsg && <span style={{ opacity: 0.9 }}>{attMsg}</span>}
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                  <div style={{ border: "1px solid #fff", borderRadius: 10, overflow: "hidden", background: "#000" }}>
                    <video ref={videoRef} playsInline muted style={{ width: "100%", height: "auto" }} />
                    <canvas ref={canvasRef} style={{ display: "none" }} />
                  </div>
                  <div>
                    <h5 style={{ marginTop: 0 }}>Recent Matches</h5>
                    {recentMarks.length === 0 ? (
                      <p style={{ opacity: 0.8 }}>—</p>
                    ) : (
                      <div style={{ display: "grid", gap: 6 }}>
                        {recentMarks.map((m, i) => (
                          <div key={i} style={{ display: "flex", justifyContent: "space-between", border: "1px solid #fff", borderRadius: 8, padding: "6px 8px" }}>
                            <span>{m.name}</span>
                            <span style={{ fontSize: 12, opacity: 0.85 }}>
                              {m.already ? "already marked" : "marked"} · d={m.distance}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                <p style={{ opacity: 0.8, marginTop: 6 }}>
                  Keep the camera running; every 2s it checks for a face and marks today’s attendance on a confident match.
                </p>
              </div>
            </section>


            {/* Students */}
            <section>
              <h4 style={{ margin: "12px 0 8px" }}>Students</h4>
              {students.length === 0 ? (
                <p style={{ opacity: 0.8, margin: 0 }}>No students yet.</p>
              ) : (
                <div style={{ display: "grid", gap: 10 }}>
                  {students.map(s => (
                    <Row key={s.id}>
                      <div style={{ display: "grid" }}>
                        <span style={{ fontWeight: 600 }}>{s.name}</span>
                        <span style={{ opacity: 0.8, fontSize: 12 }}>{s.email}</span>
                      </div>

                      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                        {/* Attendance chip (optional) */}
                        {getTodayAttendanceForClass && (
                          <span
                            style={{
                              padding: "2px 8px",
                              borderRadius: 999,
                              border: "1px solid #fff",
                              fontSize: 12,
                              opacity: 0.9,
                            }}
                            title="Attendance today"
                          >
                            {todayMap[s.id] ? "Present today" : "Not marked"}
                          </span>
                        )}

                        <button onClick={() => handleRemove(s.id)}>Remove</button>
                      </div>
                    </Row>
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
