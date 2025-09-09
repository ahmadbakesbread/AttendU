import React, { useState } from "react";
import { registerTeacher } from "../api";
import { useNavigate } from "react-router-dom";
import "./signup.css";

// EVERYTHING FROM THIS FILE IS THE SAME AS SignupParent but here the student
// look at SignupParent for my comments!
export default function SignupTeacher() {
  const [input, setInput] = useState({ name: "", email: "", password: "", confirmPassword: "" });
  const [errors, setErrors] = useState({});
  const navigate = useNavigate();

  const handleTextChange = (e) => setInput((s) => ({ ...s, [e.target.name]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    const eMap = {};
    if (!input.name) eMap.name = <p className="error-message">❗ Name is required.</p>;
    if (!input.email) eMap.email = <p className="error-message">❗ Email is required.</p>;
    if (!input.password) eMap.password = <p className="error-message">❗ Password is required.</p>;
    if (!input.confirmPassword) eMap.confirmPassword = <p className="error-message">❗ Must Confirm Password.</p>;
    if (Object.keys(eMap).length) return setErrors(eMap);

    const formData = new FormData();
    formData.append("name", input.name);
    formData.append("email", input.email);
    formData.append("password", input.password);
    formData.append("confirmPassword", input.confirmPassword);

    try {
      await registerTeacher(formData);
      navigate("/login", { replace: true });
    } catch (err) {
      setErrors({ email: <p className="error-message">❗ {err.message}</p> });
    }
  };

  return (
    <div className="page">
      <div className="card">
        <form onSubmit={handleSubmit}>
          <h3 className="title">Sign Up as a Teacher</h3>

          <label className="signup-label">
            Full Name
            <input name="name" type="text" value={input.name} onChange={handleTextChange} className="input" />
            {errors.name}
          </label>

          <label className="signup-label">
            Email
            <input name="email" type="text" value={input.email} onChange={handleTextChange} className="input" />
            {errors.email}
          </label>

          <label className="signup-label">
            Password
            <input name="password" type="password" value={input.password} onChange={handleTextChange} className="input" />
            {errors.password}
          </label>

          <label className="signup-label">
            Confirm Password
            <input name="confirmPassword" type="password" value={input.confirmPassword} onChange={handleTextChange} className="input" />
            {errors.confirmPassword}
          </label>

          <input className="submit-button" type="submit" value="Create account" />
        </form>
      </div>
    </div>
  );
}
