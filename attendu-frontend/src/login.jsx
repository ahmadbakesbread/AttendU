import React, { useState } from 'react';
import './signup.css';


function MySignup() {
    const [input, setInput] = useState({});

    const handleChange = (event) => {
        const name = event.target.name;
        const value = event.target.value;
        setInput(prevState => ({ ...prevState, [name]: value }));
    }

    const handleSubmit = (event) => {
        event.preventDefault();
        window.location.reload(); // This line specifically refreshes the page, fix it later so that it only refreshes if incorrect parameters.
        alert(JSON.stringify(input));
    }

    return (
        
        <body>
        <div className="cool-block">
        <div className="space"></div>
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Outfit:wght@100;200;300;400;500;600;700;800;900&display=swap" />
        <form onSubmit={handleSubmit}>
        <h3 style={{fontFamily: 'Outfit, sans-serif', fontSize: 25, fontWeight: 500, textAlign: 'center', marginBottom: '1%'}}>
            Log In:
        </h3>
        <h3 style={{fontFamily: 'Outfit, sans-serif', fontSize: 18, fontWeight: 300, textAlign: 'center'}}>
            Welcome Back!
        </h3>

            <label className="signup-label" htmlFor="emailInput">
            <br></br>
                <input
                    name="name"
                    type="text"
                    placeholder="name."
                    value={input.name || ""}
                    onChange={handleChange}
                    style={{ color: "#AEC3B0", backgroundColor: "#051E27", border: "1px solid #ffffff",
                     borderRadius: "5px", height: "20px", width: "400px", fontFamily: 'Outfit, sans-serif', paddingLeft: '1.5%' }}
                />
            </label>
            <br></br>
            <label className="signup-label">
                <br></br>
                <input 
                    name="email"
                    type="text"
                    placeholder="email."
                    value={input.email || ""}
                    onChange={handleChange}
                    style={{ color: "#AEC3B0", backgroundColor: "#051E27", border: "1px solid #ffffff",
                    borderRadius: "5px", height: "20px", width: "400px", fontFamily: 'Outfit, sans-serif', paddingLeft: '1.5%'}}                
                />
            </label>
            <br />
            <label className="signup-label" for="pwd">
            <br></br>
                <input 
                    name="password"
                    type="password"
                    placeholder="password."
                    value={input.password || ""}
                    onChange={handleChange}
                    style={{ color: "#AEC3B0", backgroundColor: "#051E27", border: "1px solid #ffffff",
                    borderRadius: "5px", height: "20px", width: "400px", fontFamily: 'Outfit, sans-serif', paddingLeft: '1.5%' }}                
                />
                </label>
                <br></br>
            <input className="submit-button" type="submit" value="log in." />
        </form>
        <div className="light_circle"></div> 
        </div>
        </body>
        
    );
}

export default MySignup;
