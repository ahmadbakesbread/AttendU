// THE WELCOME PAGE!
import { Link } from "react-router-dom";      // like <a> tag but doesnt refresh page

export default function Welcome() {
  return (                                     // here we set the main layout for welcome page
    <div style={{
      minHeight: '100vh',
      width: '100%',
      display: 'flex',
      flexDirection: 'column',
      background: '#01161E',
      color: '#f0f0f0'
    }}>
      <header style={{                          // the top nav bar
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '16px 32px',
        background: '#124559'
      }}>                                       {/* Currently our app name AttendU functions as the logo... 
                                                    not great but whatever*/}
        <h3 style={{ margin: 0, fontWeight: 700 }}>AttendU</h3>
        <nav style={{ display: 'flex', gap: 24 }}>
          <a 
            href="https://github.com/ahmadbakesbread/AttendU" 
            target="_blank" 
            rel="noreferrer" 
            style={{  // some color for the contact. log in.
              background: '#124559',
              color: '#f0f0f0',
              padding: '6px 12px',
              borderRadius: '6px',
              textDecoration: 'none'
          }}
          
          >contact.</a>
          <Link to="/login" 
          style={{  // some color for the  log in.
            background: '#124559',
            color: '#f0f0f0',
            padding: '6px 12px',
            borderRadius: '6px',
            textDecoration: 'none'
        }}
          >log in.</Link>
          <Link to="/signup/decision"
          style={{  // some color for the  log in.
            background: '#124559',
            color: '#f0f0f0',
            padding: '6px 12px',
            borderRadius: '6px',
            textDecoration: 'none'
        }}>sign up.</Link>
        </nav>
      </header>

      <main style={{
        flex: 1,
        width: '100%',
        display: 'grid',
        placeItems: 'center',
        padding: '40px 20px',
        textAlign: 'center'
      }}>
        <div style={{ maxWidth: 900, width: '100%' }}>
          <h1 style={{ margin: '0 0 12px' }}>Take Attendance with Ease.</h1>  {/* THE MAIN HEADLINE */}
          <p style={{ margin: 0, opacity: 0.85 }}>Redesigning the Traditional Roll Call</p> {/* THE SUBTITLE */}
          <p style={{ margin: 0, opacity: 0.85 }}>Automated & Accessible</p> {/* THE SUBTITLE 2 */}
          <div style={{ marginTop: 24 }}>
          <Link to="/signup/decision">
          <button                               // i originally had a normal button but i didnt like it lol so i overdid this one.
            style={{
              padding: "12px 24px",
              backgroundColor: "#50C878",
              color: "#fff",
              fontSize: "16px",
              fontWeight: "600",
              border: "none",
              borderRadius: "8px",
              cursor: "pointer",
              transition: "background-color 0.2s ease, transform 0.15s ease",
            }}
            onMouseOver={(e) => (e.target.style.backgroundColor = "#2E8B57")}
            onMouseOut={(e) => (e.target.style.backgroundColor = "#50C878")}
            onMouseDown={(e) => (e.target.style.transform = "scale(0.96)")}
            onMouseUp={(e) => (e.target.style.transform = "scale(1)")}
          >
            Get Started
          </button>
        </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
