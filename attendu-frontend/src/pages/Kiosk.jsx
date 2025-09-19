// src/pages/kiosk/Kiosk.jsx
import React, { useEffect, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext.jsx";
import { markAttendanceFromFrame } from "../api.js";

export default function Kiosk() {
  const { id } = useParams();
  const classId = Number(id);
  const navigate = useNavigate();
  const { user } = useAuth();

  useEffect(() => {
    if (user?.role && user.role !== "teacher") {
      navigate(`/classes/${classId}`, { replace: true });
    }
    // eslint-disable-next-line
  }, [user, classId]);

  const [attRunning, setAttRunning] = useState(false);
  const [attMsg, setAttMsg] = useState("");
  const [recentMarks, setRecentMarks] = useState([]);
  const [scanState, setScanState] = useState({ state: "idle", text: "Idle" });
  const [isFs, setIsFs] = useState(false); // fullscreen state

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const pageRef = useRef(null);
  const wrapRef = useRef(null); // wrapper around the video
  const streamRef = useRef(null);
  const timerRef = useRef(null);
  const lastMarkRef = useRef(new Map());
  const [todayMap, setTodayMap] = useState({});

  useEffect(() => {
    const onFsChange = () => setIsFs(Boolean(document.fullscreenElement));
    document.addEventListener("fullscreenchange", onFsChange);
    return () => document.removeEventListener("fullscreenchange", onFsChange);
  }, []);

  function beep(freq = 980, duration = 120, volume = 0.12) {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain); gain.connect(ctx.destination);
      osc.type = "sine"; osc.frequency.value = freq; gain.gain.value = volume;
      osc.start();
      setTimeout(() => {
        gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.05);
        osc.stop(); ctx.close();
      }, duration);
    } catch {}
    navigator.vibrate?.(80);
  }

  async function startAttendance() {
    setAttMsg("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user", width: { ideal: 1920 }, height: { ideal: 1080 } },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setAttRunning(true);
      setScanState({ state: "scanning", text: "Scanning…" });
      timerRef.current = setInterval(captureAndSend, 1800);
    } catch (e) {
      setAttMsg(e?.message || "Failed to open camera.");
      setScanState({ state: "error", text: "Camera error" });
    }
  }

  function stopAttendance() {
    setAttRunning(false);
    setScanState({ state: "idle", text: "Stopped" });
    if (timerRef.current) clearInterval(timerRef.current);
    if (videoRef.current) videoRef.current.pause();
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
  }

  useEffect(() => {
    startAttendance();
    return () => stopAttendance();
    // eslint-disable-next-line
  }, [classId]);

  async function captureAndSend() {
    const video = videoRef.current, canvas = canvasRef.current;
    if (!video || !canvas) return;

    const w = video.videoWidth || 640, h = video.videoHeight || 480;
    canvas.width = w; canvas.height = h;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, w, h);

    const blob = await new Promise((res) => canvas.toBlob(res, "image/jpeg", 0.85));
    if (!blob) return;

    setScanState((s) => (s.state === "matched" ? s : { state: "scanning", text: "Scanning…" }));

    try {
      const res = await markAttendanceFromFrame(classId, blob);

      if (res?.matched_student) {
        const sid = res.matched_student.id;
        const name = res.matched_student.name;
        const now = Date.now();
        const last = lastMarkRef.current.get(sid) || 0;

        if (now - last > 3000) {
          lastMarkRef.current.set(sid, now);
          if (!res.already_marked) beep(980, 120);
        }

        const item = { id: sid, name, already: !!res.already_marked, distance: Number(res.distance).toFixed(3) };
        setRecentMarks((prev) => [item, ...prev.slice(0, 9)]);
        setTodayMap((m) => ({ ...m, [sid]: true }));
        setScanState({
          state: "matched",
          text: `Recognized ${name}${res.already_marked ? " (already)" : ""} · d=${Number(res.distance).toFixed(3)}`,
        });
        return;
      }

      setScanState({ state: "unknown", text: "Unknown face" });
    } catch (e) {
      const msg = (e?.message || "").toLowerCase();
      if (msg.includes("face recognition disabled")) {
        setScanState({ state: "disabled", text: "Face engine disabled" });
      } else if (msg.includes("no single face")) {
        setScanState({ state: "no_face", text: "No face detected" });
      } else if (msg.includes("no confident match")) {
        setScanState({ state: "unknown", text: "Unknown face" });
      } else {
        setScanState({ state: "error", text: "Error" });
      }
    }
  }

  async function goFullscreen() {
    const el = wrapRef.current || pageRef.current;
    if (!el) return;
    try {
      if (!document.fullscreenElement) {
        await (el.requestFullscreen?.() || el.webkitRequestFullscreen?.());
      } else {
        await (document.exitFullscreen?.() || document.webkitExitFullscreen?.());
      }
    } catch {}
  }

  const borderColor =
    scanState.state === "matched" ? "#16a34a" :
    scanState.state === "unknown" ? "#f59e0b" :
    scanState.state === "no_face" ? "#9ca3af" :
    scanState.state === "disabled" ? "#ef4444" :
    scanState.state === "error" ? "#ef4444" : "#ffffff";

  // sizes
  const shellStyle = isFs
    ? { padding: 0, width: "100vw", height: "100vh" }
    : { padding: 16, minHeight: "100vh" };

  const cardStyle = isFs
    ? { width: "100%", height: "100%", background: "#051E27", padding: 12 }
    : { maxWidth: 1400, margin: "0 auto", background: "#051E27", padding: 16 };

  const gridStyle = isFs
    ? { display: "grid", gridTemplateColumns: "3fr 1fr", gap: 16, height: "calc(100% - 56px)" }
    : { display: "grid", gridTemplateColumns: "2fr 1fr", gap: 16 };

  const videoWrapStyle = isFs
    ? { border: `4px solid ${borderColor}`, borderRadius: 16, overflow: "hidden", background: "#000",
        position: "relative", width: "100%", height: "100%" }
    : { border: `4px solid ${borderColor}`, borderRadius: 16, overflow: "hidden", background: "#000",
        position: "relative", width: "100%", height: "min(70vh, 720px)", aspectRatio: "16 / 9" };

  const videoStyle = isFs
    ? { width: "100%", height: "100%", display: "block", objectFit: "cover" }
    : { width: "100%", height: "100%", display: "block", objectFit: "cover" };

  return (
    <div ref={pageRef} className="page" style={shellStyle}>
      <div className="card" style={cardStyle}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
          <h3 style={{ margin: 0 }}>Kiosk · Class #{classId}</h3>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {!attRunning ? <button onClick={startAttendance}>Start</button> : <button onClick={stopAttendance}>Stop</button>}
            <button onClick={goFullscreen}>{isFs ? "Exit Fullscreen" : "Fullscreen"}</button>
            <button onClick={() => navigate(`/classes/${classId}`, { replace: true })}>Exit</button>
          </div>
        </div>

        {attMsg && <p style={{ marginTop: 0 }}>{attMsg}</p>}

        <div style={gridStyle}>
          <div ref={wrapRef} style={videoWrapStyle}>
            <div style={{
              position: "absolute", top: 12, left: 12,
              background: "rgba(0,0,0,0.6)", padding: "6px 10px",
              borderRadius: 999, fontSize: 13, border: "1px solid #fff", opacity: 0.95, zIndex: 2
            }}>
              {scanState.text}
            </div>
            <video ref={videoRef} playsInline muted style={videoStyle} />
            <canvas ref={canvasRef} style={{ display: "none" }} />
          </div>

          <div style={{ overflow: "auto" }}>
            <h4 style={{ marginTop: 0 }}>Recent Matches</h4>
            {recentMarks.length === 0 ? (
              <p style={{ opacity: 0.8 }}>—</p>
            ) : (
              <div style={{ display: "grid", gap: 8 }}>
                {recentMarks.map((m, i) => (
                  <div key={i} style={{
                    display: "flex", justifyContent: "space-between",
                    border: "1px solid #fff", borderRadius: 10, padding: "8px 10px"
                  }}>
                    <span>{m.name}</span>
                    <span style={{ fontSize: 12, opacity: 0.85 }}>
                      {m.already ? "already marked" : "marked"} · d={m.distance}
                    </span>
                  </div>
                ))}
              </div>
            )}
            <p style={{ opacity: 0.8, marginTop: 10 }}>
              Tip: place the device ~1m from the door, good light, one face in frame.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
