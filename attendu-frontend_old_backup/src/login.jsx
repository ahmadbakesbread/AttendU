import React, { useState } from 'react';
import './signup.css';
import { login } from './api';


function Login() { // Login Form
    const [input, setInput] = useState({}); // State to hold form inputs
    const [errors, setErrors] = useState({}); // State to hold validation errors

    // Function to handle changes in text inputs and update state accordingly
    const handleChange = (event) => {
        const { name, value } = event.target;
        setInput(prevState => ({ ...prevState, [name]: value }));
    }

    // Function to handle form submission
    const handleSubmit = async (event) => {
        event.preventDefault();
        setErrors({});
        let newErrors = {}; // Reset error state to account for previous errors.

        // Basic validation checks
        if (!input.email) newErrors.email = <p className='error-message'>❗ Email is required.</p>;
        if (!input.password) newErrors.password = <p className='error-message'>❗ Password is required.</p>;

        // If there are any errors, stop the form submission and display the errors
        if (Object.keys(newErrors).length > 0) {
            setErrors(newErrors);
            return; // Stop the form submission
        }

        // Attempt to login the user via API call
        try {
            const result = await login(JSON.stringify({
                email: input.email,
                password: input.password
            }));
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
                        Log In:
                    </h3>
                    <h3 style={{ fontFamily: 'Outfit, sans-serif', fontSize: 18, fontWeight: 300, textAlign: 'center' }}>
                        Welcome Back!
                    </h3>

                    <label className="signup-label">
                        <br />
                        <input
                            name="email"
                            type="text"
                            placeholder="email."
                            value={input.email || ""}
                            onChange={handleChange}
                            style={{ color: "#AEC3B0", backgroundColor: "#051E27", border: "1px solid #ffffff", borderRadius: "5px", height: "20px", width: "400px", fontFamily: 'Outfit, sans-serif', paddingLeft: '1.5%' }}
                        />
                        {errors.email && <span className="error">{errors.email}</span>}
                    </label>
                    <br />
                    <label className="signup-label">
                        <br />
                        <input
                            name="password"
                            type="password"
                            placeholder="password."
                            value={input.password || ""}
                            onChange={handleChange}
                            style={{ color: "#AEC3B0", backgroundColor: "#051E27", border: "1px solid #ffffff", borderRadius: "5px", height: "20px", width: "400px", fontFamily: 'Outfit, sans-serif', paddingLeft: '1.5%' }}
                        />
                        {errors.password && <span className="error">{errors.password}</span>}
                    </label>
                    <br />
                    <input className="submit-button" type="submit" value="log in." />
                </form>
                <div className="light_circle"></div>
            </div>
        </div>
    );
}

export default Login;
