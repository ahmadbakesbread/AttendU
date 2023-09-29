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
            Sign Up:
        </h3>
        <h3 style={{fontFamily: 'Outfit, sans-serif', fontSize: 18, fontWeight: 300, textAlign: 'center'}}>
            Let's Get Started!
        </h3>

            <label className="signup-label" htmlFor="emailInput">
                Enter Your Name:
                <br></br>
                <input
                    name="name"
                    type="text"
                    value={input.name || ""}
                    onChange={handleChange}
                    style={{ color: "#AEC3B0", backgroundColor: "#051E27", border: "1px solid #ffffff",
                     borderRadius: "5px", height: "20px", width: "400px", fontFamily: 'Outfit, sans-serif', paddingLeft: '1.5%' }}
                />
            </label>
            <br></br>
            <label className="signup-label">
                Enter Your Email:
                <br></br>
                <input 
                    name="email"
                    type="text"
                    value={input.email || ""}
                    onChange={handleChange}
                    style={{ color: "#AEC3B0", backgroundColor: "#051E27", border: "1px solid #ffffff",
                    borderRadius: "5px", height: "20px", width: "400px", fontFamily: 'Outfit, sans-serif', paddingLeft: '1.5%'}}                
                />
            </label>
            <br />
            <label className="signup-label" for="pwd">
                Enter Your Password:
                <br></br>
                <input 
                    name="password"
                    type="password"
                    value={input.password || ""}
                    onChange={handleChange}
                    style={{ color: "#AEC3B0", backgroundColor: "#051E27", border: "1px solid #ffffff",
                    borderRadius: "5px", height: "20px", width: "400px", fontFamily: 'Outfit, sans-serif', paddingLeft: '1.5%' }}                
                />
                </label>
                <br />
                <label className="signup-label" htmlFor="confirmPassword">
                    Confirm Password:
                    <br></br>
                    <input 
                    name="confirmPassword"
                    type="password"
                    value={input.confirmPassword || ""}
                    onChange={handleChange}
                    style={{ color: "#AEC3B0", backgroundColor: "#051E27", border: "1px solid #ffffff",
                    borderRadius: "5px", height: "20px", width: "400px", fontWeight: 'bold', fontFamily: 'Outfit, sans-serif' }}                
                    />
                    </label>
                    <br />


            <input className="submit-button" type="submit" value="Submit" />
        </form>
        <div className="light_circle"></div> 
        </div>
        </body>
        
    );
}

export default MySignup;