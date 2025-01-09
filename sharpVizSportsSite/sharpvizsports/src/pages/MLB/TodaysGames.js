import React from "react";
import Sidebar from "../../components/SideBar";
import GamesDisplay from "../../components/GamesDisplay";

const TodaysGames = () => {
  const today = new Date().toISOString().split("T")[0];

  return (
    <div className="daily-data-mlb">
      <Sidebar />
      <div className="content">
        <h1>Today's Games</h1>
        <GamesDisplay initialDate={today} />
      </div>
    </div>
  );
};

export default TodaysGames;
