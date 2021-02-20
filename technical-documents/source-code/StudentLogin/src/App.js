import React from "react";
import { BrowserRouter as Router, Route } from "react-router-dom";
import "./icons.js";
import Login from "./screens/Login";
import "./style.css";

function App() {
  return (
    <Router>
      <Route path="/" exact component={Login} />
      <Route path="/Login/" exact component={Login} />
    </Router>
  );
}

export default App;
