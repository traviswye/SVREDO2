import React from "react";
import { Link } from "react-router-dom";
import "../css/NavBar.css";

const NavBar = () => {
  return (
    <nav className="navbar">
      <div className="navbar-left">
        <Link to="/">Home</Link>
        <Link to="/mlb/todays-games">MLB</Link>
        <Link to="/nfl/home">NFL</Link>
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
