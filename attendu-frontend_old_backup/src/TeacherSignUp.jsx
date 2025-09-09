import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom'; // Added useLocation here
import MyDecision from './MyDecision';
import { registerTeacher } from './api';
import './signup.css';


function TeacherSignUp() { // Teacher Sign Up

    const location = useLocation(); // Hook to access the current location object
    const { userType } = location.state || {}; // Fallback to an empty object if state is undefined
    const [input, setInput] = useState({}); // State to hold form inputs
    const [errors, setErrors] = useState({}); // State to hold validation errors

    // Function to handle changes in text inputs and update state accordingly
    const handleTextChange = (event) => {
        const { name, value } = event.target;
        setInput(prevState => ({ ...prevState, [name]: value }));
    }

    // Function to handle form submission
    const handleSubmit = async (event) => {
        event.preventDefault();
        setErrors({});
        let newErrors = {}; // Reset error state to account for previous errors.

        // Basic validation checks
        if (!input.name) newErrors.name = <p className='error-message'>❗ Name is required.</p>;
        if (!input.email) newErrors.email = <p className='error-message'>❗ Email is required.</p>;
        if (!input.password) newErrors.password = <p className='error-message'>❗ Password is required.</p>;
        if (!input.confirmPassword) newErrors.confirmPassword = <p className='error-message'>❗ Must Confirm Password.</p>;

        // If there are errors, update the errors state and abort submission
        if (Object.keys(newErrors).length > 0) {
            setErrors(newErrors);
            return;
        }

        // Attempt to register the teacher via API call
        try {
            const formData = new FormData();
            formData.append('name', input.name);
            formData.append('email', input.email);
            formData.append('password', input.password);
            formData.append('confirmPassword', input.confirmPassword);

            const result = await registerTeacher(formData);
            console.log(result);
        } catch (error) {
            console.error(error);
        }
    };

    // Render the signup form
    return (
        // Form and related inputs
        <div>
            <div className="cool-block">
                <div className="space"></div>
                <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Outfit:wght@100;200;300;400;500;600;700;800;900&display=swap" />
                <form onSubmit={handleSubmit}>
                    <h3 style={{ fontFamily: 'Outfit, sans-serif', fontSize: 25, fontWeight: 500, textAlign: 'center', marginBottom: '1%' }}>
                        Sign Up as a {userType}:
                    </h3>
                    <h3 style={{ fontFamily: 'Outfit, sans-serif', fontSize: 18, fontWeight: 300, textAlign: 'center' }}>
                        Let's Get Started!
                    </h3>

                    <label className="signup-label" htmlFor="nameInput">
                        Enter Your Full Name:
                        <br />
                        <input
                            name="name"
                            type="text"
                            value={input.name || ""}
                            onChange={handleTextChange}
                            style={{ color: "#AEC3B0", backgroundColor: "#051E27", border: "1px solid #ffffff", borderRadius: "5px", height: "20px", width: "400px", fontFamily: 'Outfit, sans-serif', paddingLeft: '1.5%' }}
                        />
                        {errors.name && errors.name}
                    </label>
                    <br />
                    <label className="signup-label" htmlFor="emailInput">
                        Enter Your Email:
                        <br />
                        <input
                            name="email"
                            type="text"
                            value={input.email || ""}
                            onChange={handleTextChange}
                            style={{ color: "#AEC3B0", backgroundColor: "#051E27", border: "1px solid #ffffff", borderRadius: "5px", height: "20px", width: "400px", fontFamily: 'Outfit, sans-serif', paddingLeft: '1.5%' }}
                        />
                        {errors.email && errors.email}
                    </label>
                    <br />
                    <label className="signup-label" htmlFor="passwordInput">
                        Enter Your Password:
                        <br />
                        <input
                            name="password"
                            type="password"
                            value={input.password || ""}
                            onChange={handleTextChange}
                            style={{ color: "#AEC3B0", backgroundColor: "#051E27", border: "1px solid #ffffff", borderRadius: "5px", height: "20px", width: "400px", fontFamily: 'Outfit, sans-serif', paddingLeft: '1.5%' }}
                        />
                        {errors.password && errors.password}
                    </label>
                    <br />
                    <label className="signup-label" htmlFor="confirmPasswordInput">
                        Confirm Password:
                        <br />
                        <input
                            name="confirmPassword"
                            type="password"
                            value={input.confirmPassword || ""}
                            onChange={handleTextChange}
                            style={{ color: "#AEC3B0", backgroundColor: "#051E27", border: "1px solid #ffffff", borderRadius: "5px", height: "20px", width: "400px", fontFamily: 'Outfit, sans-serif', paddingLeft: '1.5%' }}
                        />
                        {errors.confirmPassword && errors.confirmPassword}
                    </label>
                    <br />
                    <input className="submit-button" type="submit" value="Submit" style={{ marginTop: "5%" }} />
                </form>
                <div className="light_circle"></div>
            </div>
        </div>
    );
}

export default TeacherSignUp;
