import './welcomepage.css';
import MySignUp from "./signup.jsx"
import MyLogin from "./login.jsx"
import Welcome from "./welcome.jsx"
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';

function App() {
    return (
        <Router>
            <div className="App">
                <div className="content">
                    <Switch>
                        <Route path="/" component={Welcome} exact />
                        <Route path="/signup" component={MySignUp} />
                        <Route path="/login" component={MyLogin} />
                    </Switch>
                </div>
            </div>
        </Router>
    );
}
export default App;
