import { Link } from 'react-router-dom'   // works like an <a> tag in HTML but DOES NOT refresh the page.

export default function SignupDecision(){
  return (
    // div covering the entire screen, centering everyth
    <div style={{minHeight:'100vh', display:'grid', placeItems:'center', background:'#01161E'}}>
      {/* This is the sign up card where title/description/buttons sit*/}
      <div style={{width:420, background:'#051E27', padding:24, borderRadius:16, color:'#f0f0f0', textAlign:'center'}}>
        <h3 style={{marginTop:0}}>Sign Up</h3>
        <p>Please select your role:</p>
        <div style={{display:'grid', gap:12}}>
          {/* Role selection buttons */}
          <Link to="/signup/parent"><button className="submit-button">Parent</button></Link>
          <Link to="/signup/student"><button className="submit-button">Student</button></Link>
          <Link to="/signup/teacher"><button className="submit-button">Teacher</button></Link>
        </div>
      </div>
    </div>
  )
}
