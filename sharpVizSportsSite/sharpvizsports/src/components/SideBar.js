import React from "react";
import { Link } from "react-router-dom";
import "../css/SideBar.css";

const Sidebar = () => {
  return (
    <div className="sidebar">
      <h3>MLB Menu</h3>
      <ul>
        <li><Link to="/mlb/daily-data">Daily Data</Link></li>
        <li><Link to="/mlb/dfs-optimizer">DFS Optimizer</Link></li>
        <li><Link to="/mlb/betting-models">Betting Models</Link></li>
      </ul>
    </div>
  );
};

export default Sidebar;
