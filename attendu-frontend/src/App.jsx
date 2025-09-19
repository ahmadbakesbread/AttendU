// this is the central routing hub of the frontend
import { Routes, Route, Navigate } from "react-router-dom";
import Welcome from "./pages/Welcome.jsx";
import Login from "./pages/Login.jsx";
import SignupDecision from "./pages/SignupDecision.jsx";
import SignupStudent from "./pages/SignupStudent.jsx";
import SignupTeacher from "./pages/SignupTeacher.jsx";
import SignupParent from "./pages/SignupParent.jsx";
import RoleDashboardRouter from "./pages/dashboards/RoleDashboardRouter.jsx";
import RoleClassRouter from "./pages/class_dashboards/RoleClassRouter.jsx";
import ChildClasses from "./pages/parent/ChildClasses.jsx";
import ParentChildClassDashboard from "./pages/parent/ParentChildClassDashboard.jsx";
import Kiosk from "./pages/Kiosk.jsx";

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
        <Route path="/dashboard" element={<RoleDashboardRouter />} />
        <Route path="/classes/:id" element={<RoleClassRouter />} />
        <Route path="/classes/:id/kiosk" element={<Kiosk />} />

        {/* Parent deep links */}
        <Route path="/parent/children/:childId" element={<ChildClasses />} />
        <Route path="/parent/children/:childId/classes/:classId" element={<ParentChildClassDashboard />} />
      </Route>

      {/* FALLBACK ROUTE... handles any unknown URL, redirect to / */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
