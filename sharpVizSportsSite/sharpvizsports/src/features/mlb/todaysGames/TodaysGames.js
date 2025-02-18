// src/features/mlb/todaysGames/TodaysGames.js
import React from "react";
import Sidebar from "../../../components/common/Sidebar/SideBar";
import MLBGamesDisplay from "../dailyData/components/MLBGamesDisplay/MLBGamesDisplay";
// import "./TodaysGames.css";

const TodaysGames = () => {
  const today = new Date().toISOString().split("T")[0];

  return (
    <div className="daily-data-mlb">
      <Sidebar />
      <div className="content">
        <h1>Today's Games</h1>
        <MLBGamesDisplay initialDate={today} />
      </div>
    </div>
  );
};

export default TodaysGames;