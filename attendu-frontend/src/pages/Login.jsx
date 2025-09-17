// src/pages/Login.jsx
import React, { useState } from "react";
import "./signup.css";
import { login, getMe } from "../api";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext.jsx";

// functional component returns UI, dashboard
// export default -> component can be imported/used anywhere else.
export default function Login() {
  // two state variables here, input and erros
  const [input, setInput] = useState({});
  const [errors, setErrors] = useState({});
  const navigate = useNavigate();                 // just a simple redirect-er
  const { setAuthed, setUser } = useAuth();                // from AuthContext, updates authentication status (logged in/out)

  // this runs whenever the user types in a field
  const handleChange = (e) =>
    setInput((s) => ({ ...s, [e.target.name]: e.target.value }));

  // handles form submission (for logging in)
  const handleSubmit = async (e) => {
    // again, submitting a form refreshes entire page by default
    e.preventDefault();     // for an SPA we dont want page refreshing here
    setErrors({});
    const eMap = {};        // temp object to get see errors
    if (!input.email) eMap.email = <p className="error-message">❗ Email is required.</p>;
    if (!input.password) eMap.password = <p className="error-message">❗ Password is required.</p>;

    // if there are any errors, show them on screen and stop here.
    if (Object.keys(eMap).length) return setErrors(eMap);

    try {
      await login({ email: input.email, password: input.password });  // CALLS LOGIN API, SET COOKIES
      const me = await getMe();
      setAuthed(true);                                                // MARK USER AS LOGGED IN!
      setUser(me?.user ?? null);
      navigate("/dashboard", { replace: true });                      // REDIRECT TO DASHBOARD
    } catch (err) {
      setErrors({ password: <p className="error-message">❗ {err.message}</p> });
    }
  };

  return ( 
    <div className="page">
      <div className="card">
        <form onSubmit={handleSubmit}> {/* call handle submit when you log in */}
          <h3 className="title">Log In</h3>

          <label className="signup-label">
            Email {/* THE EMAIL FIELD */}
            <input
              name="email"                                            // important since we use it in handlChange() 
              type="text"
              placeholder="email"
              value={input.email || ""}                               // controlled input
              onChange={handleChange}                                 // update state whenever you type
              className="input"
            />
            {errors.email}                                            {/*if theres an email error, show it below the field */}
          </label>

          <label className="signup-label">
            Password {/* THE PASSWORD FIELD - same just hidden */}
            <input
              name="password"
              type="password"
              placeholder="password"
              value={input.password || ""}
              onChange={handleChange}
              className="input"
            />
            {errors.password}
          </label>
          
          {/* submits form and triggers handle submit */}
          <input className="submit-button" type="submit" value="Log in" />  
        </form>
      </div>
    </div>
  );
}
