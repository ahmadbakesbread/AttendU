// this file wires up the global auth state !
import { createContext, useContext, useEffect, useState } from "react";
import { refresh, getMe } from "./api";

// creates a react context to share auth info without prop-drilling, skip middle layers
// reminder:  prop-drilling is when we need to pass data from top level component down
//            to deeply nested child component.
const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [authed, setAuthed] = useState(false);    // authed = logged in? flag
  const [user, setUser] = useState(null);         // carries id, role, etc.
  const [loading, setLoading] = useState(true);   // loading: precents rendering app before we know user status

  // on first load: try to refresh session.
  useEffect(() => {
    (async () => {
      try {
        await refresh();              // sets a fresh access cookie (200 or throws)
        const me = await getMe();     // <-- fetch user after refresh
        setAuthed(true);
        setUser(me?.user ?? null);
      } catch {
        setAuthed(false);
        setUser(null);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  // provide the value to the app.
  const value = {authed, setAuthed, user, setUser};

  if (loading) return <div style={{ padding: 16, color: "#ddd" }}>Loading…</div>; // to avoid route flicker. TODO: add a spinner later.
  // exposes authed and setAuthed globally.
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// THE HOOK: convenience hook so components can do const { authed, setAuthed } = useAuth();
export function useAuth() {
  return useContext(AuthContext);
}
