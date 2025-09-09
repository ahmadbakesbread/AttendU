// parent sign up page
import React, { useState } from "react";
import { registerParent } from "../api";          // function that sends signup data to backend
import { useNavigate } from "react-router-dom";   // allows for redirection
import "./signup.css";                            // styles the signup forms

export default function SignupParent() {
  // useState manages form input and errors!
  const [input, setInput] = useState({});         // sees what user types into form (name, email, pass, etc.)
  const [errors, setErrors] = useState({});       // stores error messages to display under inputs
  const navigate = useNavigate();                 // basically to send to login after success

  // this function runs whenever user types into the field
  // e.target.name matches input's name attribute (e.g. email)
  // e.target.value is WHAT the user typed
  // {...s} keeps existing vals and updates the one field the user changed
  const handleTextChange = (e) =>
    setInput((s) => ({ ...s, [e.target.name]: e.target.value }));

  // handles the submission of the sign up form..
  const handleSubmit = async (e) => {
    e.preventDefault();                           // again, prevents refresh on form submission (SPA)
    const eMap = {};
    if (!input.name) eMap.name = <p className="error-message">❗ Name is required.</p>;
    if (!input.email) eMap.email = <p className="error-message">❗ Email is required.</p>;
    if (!input.password) eMap.password = <p className="error-message">❗ Password is required.</p>;
    if (!input.confirmPassword) eMap.confirmPassword = <p className="error-message">❗ Must Confirm Password.</p>;
    
    // if at least one error exists, stop and display errors in the form
    if (Object.keys(eMap).length) return setErrors(eMap);
    
    // o.w. prep data for submission
    const formData = new FormData();              // creating form data object to send to backend
    formData.append("name", input.name);
    formData.append("email", input.email);
    formData.append("password", input.password);
    formData.append("confirmPassword", input.confirmPassword);

    try {
      await registerParent(formData);             // sends the signup info to the backend
      navigate("/login", { replace: true });      // if successful reroute us to the login page
    } catch (err) {
      setErrors({ email: <p className="error-message">❗ {err.message}</p> });
    }
  };

  return (
    <div className="page">
      <div className="card">
        {/* handlesubmit when the user clicks create account*/}
        <form onSubmit={handleSubmit}>
          <h3 className="title">Sign Up as a Parent</h3>

          {/* ALL THE INPUTS*/}
          <label className="signup-label">
            Full Name
            <input name="name" type="text" value={input.name || ""} onChange={handleTextChange} className="input" />
            {errors.name}
          </label>

          <label className="signup-label">
            Email
            <input name="email" type="text" value={input.email || ""} onChange={handleTextChange} className="input" />
            {errors.email}
          </label>

          <label className="signup-label">
            Password
            <input name="password" type="password" value={input.password || ""} onChange={handleTextChange} className="input" />
            {errors.password}
          </label>

          <label className="signup-label">
            Confirm Password
            <input name="confirmPassword" type="password" value={input.confirmPassword || ""} onChange={handleTextChange} className="input" />
            {errors.confirmPassword}
          </label>

          <input className="submit-button" type="submit" value="Create account" />
        </form>
      </div>
    </div>
  );
}
