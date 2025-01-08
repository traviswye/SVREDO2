import React from "react";
import { Link } from "react-router-dom";
import "../css/NavBar.css"; // Create or use this file for styling

const NavBar = () => {
  return (
    <nav className="navbar">
      <div className="navbar-left">
        <Link to="/">Home</Link>
        <div className="dropdown">
          <button className="dropbtn">MLB</button>
          <div className="dropdown-content">
            <Link to="/mlb/daily-data">Daily Data</Link>
            <Link to="/mlb/dfs-optimizer">DFS Optimizer</Link>
            <Link to="/mlb/betting-models">Betting Models</Link>
          </div>
        </div>
        <div className="dropdown">
          <button className="dropbtn">NFL</button>
          <div className="dropdown-content">
            <Link to="/nfl/daily-data">Daily Data</Link>
            <Link to="/nfl/dfs-optimizer">DFS Optimizer</Link>
            <Link to="/nfl/betting-models">Betting Models</Link>
          </div>
        </div>
        <Link to="/partner-sharps-home">Partner Sharps</Link>
      </div>
      <div className="navbar-right">
        <Link to="/account">Account</Link>
        <Link to="/login">Login</Link>
      </div>
    </nav>
  );
};

export default NavBar;
