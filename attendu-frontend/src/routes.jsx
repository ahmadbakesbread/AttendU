// where we define route guards
// outlet is a placeholder where the child content will be rendered
import { Navigate, Outlet } from "react-router-dom";    
import { useAuth } from "./AuthContext.jsx";

/** Only allow authed users. Otherwise send to /login. */
// ex: if im logged out trying to access my dashboard.
export function RequireAuth() {
  const { authed } = useAuth();
  if (!authed) return <Navigate to="/login" replace />;
  return <Outlet />;
}

/** Only allow public (not authed). If authed, go to /dashboard. */
// ex: if im logged in trying to log in, again.
export function PublicOnly() {
  const { authed } = useAuth();
  if (authed) return <Navigate to="/dashboard" replace />;
  return <Outlet />;
}
