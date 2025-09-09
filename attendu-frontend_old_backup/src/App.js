import './welcomepage.css';
import MySignUp from "./signup.jsx";
import MyLogin from "./login.jsx";
import Welcome from "./welcome.jsx";
import MyDecision from './MyDecision.jsx';
import ParentSignUp from './ParentSignUp';
import TeacherSignUp from './TeacherSignUp';
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';

// Main application component
function App() {
    // Using the Router component to manage the application's navigation
    return (
        <Router>
            <div className="App">
                <div className="content">
                    <Switch>
                        <Route path="/" component={Welcome} exact />
                        <Route path="/signup/decision" component={MyDecision} />
                        <Route path="/signup/studentForm" component={MySignUp} />
                        <Route path="/signup/parentForm" component={ParentSignUp} />
                        <Route path="/signup/teacherForm" component={TeacherSignUp} />
                        <Route path="/login" component={MyLogin} />
                    </Switch>
                </div>
            </div>
        </Router>
    );
}
export default App;
