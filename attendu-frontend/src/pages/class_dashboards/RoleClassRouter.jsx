import React from "react";
import { useParams } from "react-router-dom";
import { useAuth } from "../../AuthContext.jsx";
import TeacherClassDashboard from "./TeacherClassDashboard.jsx";
import StudentClassDashboard from "./StudentClassDashboard.jsx";

export default function RoleClassRouter() {
  const { user } = useAuth();
  const { id } = useParams(); // class id

  if (!user?.role) return <p style={{ padding: 16 }}>Loading…</p>;

  if (user.role === "teacher") return <TeacherClassDashboard />;
  if (user.role === "student") return <StudentClassDashboard />;
  if (user.role === "parent")  return <ParentClassDashboard />;

  return <p style={{ padding: 16 }}>Unsupported role.</p>;
}