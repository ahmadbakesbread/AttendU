import React from "react";                              // core react lib for making ui
import ReactDOM from "react-dom/client";                // handles rendering react components into actual HTML DOM
import { BrowserRouter } from "react-router-dom";       // routing w/o refreshing page
import App from "./App.jsx";                            // main application component where all routes are defined!
import "./index.css";
import { AuthProvider } from "./AuthContext.jsx";       // provides global auth state to whole app.

// finds html element with id=root in index.html file, this will be where react will mount the entire app.
ReactDOM.createRoot(document.getElementById("root")).render( // this is where the app is bootstrapped
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
);

// reminder: strictmode is dev-only tool (helps catch bugs)
// browserrouter wraps app to enable react router v6
// authprovider wrpas entire app inside Auth Context
// App, loads main app component.