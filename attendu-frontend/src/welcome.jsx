import React from 'react';
import './welcomepage.css';
import { Link } from 'react-router-dom'

function Welcome() {
    return (
        <>
            <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Outfit:wght@100;200;300;400;500;600;700;800;900&display=swap" />
<div style={{ position: 'absolute', top: '0', left: '0', marginBottom: '200px' }} className="light_circle"></div>
            <header>
                <h3>AttendU</h3>
                <h4>
                    {/* TODO: Add a link that transitions you down */}
                    <a className="hover-underline" href="" style={{marginLeft: '400px', textDecoration: 'none'}}>about.</a></h4> 
                <h4><a className="hover-underline" href="https://ca.linkedin.com/in/ahmad-kanoun-8270a2265/" target="_blank"
                    style={{marginLeft: '150px', textDecoration: 'none'}}>contact.</a></h4>
                <Link to="/login" className="hover-underline" style={{marginLeft: '150px', marginTop: '19px', fontWeight: '300', textDecoration: 'none'}}>log in.</Link>
                <Link to="/signup" className="hover-underline" style={{marginLeft: '150px', marginTop: '19px',textDecoration: 'none', fontWeight: '500'}}>Sign Up.</Link>
            </header>
            
            <h4 style={{
                fontWeight: '600',
                fontStyle: 'normal',
                fontSize: '50px',
                marginRight: '80px',
                marginTop: '120px',
                color: '#f0f0f0',
                fontFamily: 'Outfit, sans-serif'
            }}>
                Take Attendance <br /> With Ease.
            </h4>
            <div style={{marginLeft: '30%'}}> </div>
            <p style={{
                fontWeight: '200',
                fontSize: '20px',
                marginTop: '-38px',
                fontFamily: 'Outfit, sans-serif',
                marginRight: '80px',
                color: '#FFFFFF'
            }}>
                Attendance Reimagined: Accurate, <br /> Automated, Accessible.
            </p>
            
            <div className="shift-right shift-down"> 
                {/* TODO: Let the button push you down. */}
                <input type="button" className="button" value="LEARN MORE" />
            </div>
            
            <div style={{ marginLeft: '700px', marginBottom: '200px' }} className="light_circle"></div>
            
            <img style={{marginLeft: '700px', marginTop: '-375px'}} src="./frontend_images/pc.png" alt="Computer" width="500" height="500" />
        </>
    );
}
export default Welcome;
