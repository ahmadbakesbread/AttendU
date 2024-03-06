import { useHistory } from 'react-router-dom';

// This component provides a decision page for new users to select their role
function MyDecision() {
    const history = useHistory(); // Provides access to history instance for navigation

    // These functions use the history object to navigate to different sign-up forms based on the role
    const navigateToStudentSignUp = (userType) => {
        console.log(`Navigating as ${userType}`);
        history.push("/signup/studentForm", { userType }); // Updated path
    };

    const navigateToTeacherSignUp = (userType) => {
        console.log(`Navigating as ${userType}`);
        history.push("/signup/teacherForm", { userType }); // Updated path
    };

    const navigateToParentSignUp = (userType) => {
        console.log(`Navigating as ${userType}`);
        history.push("/signup/parentForm", { userType }); // Updated path
    };

    // The render method returns UI elements allowing the user to choose their role
    return(
        // React Fragment to group the list of children without adding extra nodes to the DOM
        <>
        <div className="small-cool-block">
            <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Outfit:wght@100;200;300;400;500;600;700;800;900&display=swap" />
                <h3 style={{ fontFamily: 'Outfit, sans-serif', fontSize: 25, fontWeight: 500, textAlign: 'center', marginBottom: '20px' }}>
                    Sign Up:
                </h3>
                <br></br>
                <h3 style={{ fontFamily: 'Outfit, sans-serif', fontSize: 18, fontWeight: 300, textAlign: 'center', marginBottom: '20px' }}>
                    Please Select Your Role:
                </h3>
                <br></br>
                <div style={{display: "flex", alignItems: "center", justifyContent: "center"}}>
                <input className="parent-button" type="button" value="Parent?" onClick={() => navigateToParentSignUp('Parent')} style={{marginRight: "10%"}} />
                <input className="student-button" type="button" value="Student?" onClick={() => navigateToStudentSignUp('Student')} style={{marginRight: "10%"}} />
                <input className="teacher-button" type="button" value="Teacher?" onClick={() => navigateToTeacherSignUp('Teacher')} />
                </div>
            <div className="light_circle"></div> 
        </div>
        </>
    )
}

export default MyDecision;