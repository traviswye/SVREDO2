import React from "react";
import Sidebar from "../../components/SideBar";
import DataBox from "../../components/DataBox";
import ProbablePitcherMetrics from "../../components/ProbablePitcherMetrics"; // New component
import "../../css/DailyDataMLB.css";

const DailyDataMLB = () => {
  const teamTempHeaders = [
    "Team",
    "Current Temperature",
    "Wins",
    "Loses",
    "Winning %",
    "RS",
    "RA",
    "Pythagran %",
    "Streak",
    "Last Result",
    "Previous Temp",
    "Date",
    "Game Number",
  ];

  const teamTempKeyHeaders = [
    "team",
    "currentTemp",
    "wins",
    "loses",
    "winPerc",
    "rs",
    "ra",
    "pythagPerc",
    "streak",
    "lastResult",
    "previousTemp",
    "date",
    "gameNumber",
  ];

  const otherHeaders = [
    "Player",
    "Stat 1",
    "Stat 2",
    "Stat 3",
    "Stat 4",
    "Date",
  ];

  const otherKeyHeaders = ["player", "stat1", "stat2", "stat3", "stat4", "date"];

  return (
    <div className="daily-data-mlb">
      <Sidebar />
      <div className="content">
        <h1>Daily MLB Data</h1>
        <div className="grid-container">
          <DataBox
            title="Team Temperatures"
            subtitle="Based on Bill James team temperature tracking"
            headers={teamTempHeaders}
            keyHeaders={teamTempKeyHeaders}
            apiUrl="https://localhost:44346/api/TeamTemperatureTracking/latest-teams/2024/true"
          />
          <DataBox
            title="Team Profitability"
            subtitle="Running totals of teams Vegas Profitability"
            headers={otherHeaders}
            keyHeaders={otherKeyHeaders}
            apiUrl="https://localhost:44346/api/PlayerStats"
            toggleEnabled={false}
          />
          <ProbablePitcherMetrics
            title="Probable Starting Pitcher Hot/Cold Metrics"
            subtitle="Metrics for probable starting pitchers"
            date="24-09-29" // Use today's date dynamically if needed
          />
          <DataBox
            title="Hitter Temperatures"
            subtitle="Hitter Temperatures and SharpViz Overperformance Metrics"
            headers={teamTempHeaders}
            keyHeaders={teamTempKeyHeaders}
            apiUrl="https://localhost:44346/api/TeamStandings"
            toggleEnabled={false}
          />
        </div>
      </div>
    </div>
  );
};

export default DailyDataMLB;
