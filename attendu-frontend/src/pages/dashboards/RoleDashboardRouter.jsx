import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../../AuthContext.jsx";
import TeacherDashboard from "./TeacherDashboard.jsx";
import StudentDashboard from "./StudentDashboard.jsx";
import ParentDashboard from "./ParentDashboard.jsx";

export default function RoleDashboardRouter() {
  const { user } = useAuth();

  if (!user?.role) {
    return <p style={{ padding: 16 }}>Loading…</p>;
  }

  if (user.role === "teacher") return <TeacherDashboard />;
  if (user.role === "student") return <StudentDashboard />;
  if (user.role === "parent")  return <ParentDashboard />;

  // fallback (unknown role)
  return <Navigate to="/" replace />;
}