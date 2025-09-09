// src/pages/SignupStudent.jsx
import React, { useState } from "react";
import { registerStudent } from "../api";               // function that sends signup data to backend
import { useNavigate } from "react-router-dom";         // allows for redirection
import "./signup.css";                                  // styles the signup forms


/* EVERYTHING FROM THIS FILE IS THE SAME AS SignupParent and SignupTeacher but here the student must
upload an image! */

// if confused look at SignupParent for my comments
export default function SignupStudent() {
  // useState manages form input and errors!
  const [input, setInput] = useState({});
  const [errors, setErrors] = useState({});
  const [imageAdded, setImageAdded] = useState(false);
  const navigate = useNavigate();

  const handleTextChange = (e) =>
    setInput((s) => ({ ...s, [e.target.name]: e.target.value }));

  // this handles the image being uploaded.
  const handleImageChange = (e) => {
    const file = e.target.files?.[0];           // choose the first uploaded image.
    if (file) {
      setInput((s) => ({ ...s, profilePic: file }));
      setImageAdded(true);
    }
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    const eMap = {};
    if (!input.name) eMap.name = <p className="error-message">❗ Name is required.</p>;
    if (!input.email) eMap.email = <p className="error-message">❗ Email is required.</p>;
    if (!input.password) eMap.password = <p className="error-message">❗ Password is required.</p>;
    if (!input.confirmPassword) eMap.confirmPassword = <p className="error-message">❗ Must Confirm Password.</p>;
    
    // WE MUST ADD AN IMAGE!
    if (!imageAdded) eMap.imageAdded = <p className="error-message">❗ Image is required.</p>;

    // if there are any errors stop and display message.
    if (Object.keys(eMap).length) return setErrors(eMap);

    // prep data to be sent to backend
    const formData = new FormData();
    formData.append("name", input.name);
    formData.append("email", input.email);
    formData.append("password", input.password);
    formData.append("confirmPassword", input.confirmPassword);
    formData.append("image", input.profilePic);

    try {
      await registerStudent(formData);            // send data to backend
      navigate("/login", { replace: true });      // if successful, reroute to login page
    } catch (err) {
      setErrors({ email: <p className="error-message">❗ {err.message}</p> });
    }
  };

  return (
    <div className="page">
      <div className="card">
        <form onSubmit={handleSubmit}>
          <h3 className="title">Sign Up as a Student</h3>
          
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

          <label className="signup-label">
            Profile Image
            <input id="profilePic" name="profilePic" type="file" accept="image/*" onChange={handleImageChange} />
            {errors.imageAdded}
            {imageAdded && <span style={{ marginLeft: 8, fontSize: 12, opacity: 0.8 }}>✓ image selected</span>}
          </label>

          <input className="submit-button" type="submit" value="Create account" />
        </form>
      </div>
    </div>
  );
}
