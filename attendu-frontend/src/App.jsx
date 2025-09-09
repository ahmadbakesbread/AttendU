// this is the central routing hub of the frontend
import { Routes, Route, Navigate } from "react-router-dom";
import Welcome from "./pages/Welcome.jsx";
import Login from "./pages/Login.jsx";
import SignupDecision from "./pages/SignupDecision.jsx";
import SignupStudent from "./pages/SignupStudent.jsx";
import SignupTeacher from "./pages/SignupTeacher.jsx";
import SignupParent from "./pages/SignupParent.jsx";
import Dashboard from "./pages/Dashboard.jsx";

// custom route guards to decide who can visit what.
import { RequireAuth, PublicOnly } from "./routes.jsx";

// wraps the entire app in a Routes component
export default function App() {
  return (
    <Routes>
      {/* PUBLIC ONLY ROUTES - route guards from routes.jsx*/}
      <Route element={<PublicOnly />}>
        <Route path="/" element={<Welcome />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup/decision" element={<SignupDecision />} />
        <Route path="/signup/student" element={<SignupStudent />} />
        <Route path="/signup/teacher" element={<SignupTeacher />} />
        <Route path="/signup/parent" element={<SignupParent />} />
      </Route>

      {/* PROTECTED ROUTES - requires authentication (from routes.jsx)*/}
      <Route element={<RequireAuth />}>
        <Route path="/dashboard" element={<Dashboard />} />
      </Route>

      {/* FALLBACK ROUTE... handles any unknown URL, redirect to / */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
